import sys
from typing import Dict, List, Optional

from miniparser.ast_nodes import (
    Visitor, ASTNode, Program,
    FnDecl, VarDecl, StructDecl, Param, StructField,
    BlockStmt, IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, AssignExpr, CallExpr,
    IdentifierExpr, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
)
from .errors import SemanticError
from .symbol_table import Symbol, SymbolKind, SymbolTable
from .type_system import (
    Type, FunctionType, StructType,
    INT_TYPE, FLOAT_TYPE, BOOL_TYPE, VOID_TYPE, STRING_TYPE, ERROR_TYPE,
    resolve_builtin, binary_result_type, unary_result_type,
)


class SemanticAnalyzer(Visitor):
    def __init__(self):
        self._table = SymbolTable()
        self._errors: List[SemanticError] = []
        self._type_map: Dict[int, Type] = {}   # id(node) -> resolved type
        self._current_fn_return: Optional[Type] = None

    # ── Public interface ──────────────────────────────────────────────────────

    def analyze(self, ast: Program) -> List[SemanticError]:
        self._errors = []
        self._type_map = {}
        self._pre_pass(ast)
        ast.accept(self)
        return self._errors

    def get_errors(self) -> List[SemanticError]:
        return self._errors

    def get_symbol_table(self) -> SymbolTable:
        return self._table

    def get_type_map(self) -> Dict[int, Type]:
        return self._type_map

    # ── Pre-pass: register top-level fns and structs (forward refs) ───────────

    def _pre_pass(self, program: Program):
        for decl in program.declarations:
            if isinstance(decl, FnDecl):
                self._register_fn_symbol(decl)
            elif isinstance(decl, StructDecl):
                self._register_struct_symbol(decl)

    def _register_fn_symbol(self, node: FnDecl):
        param_types = [self._resolve_type(p.type_name, p.token) for p in node.params]
        ret = self._resolve_type(node.return_type or "void", node.token)
        fn_type = FunctionType(node.name, param_types, ret)
        sym = Symbol(node.name, fn_type, SymbolKind.FUNCTION, node.token.line, node.token.column)
        if not self._table.insert(sym):
            self._error(f"duplicate declaration of function '{node.name}'", node.token)

    def _register_struct_symbol(self, node: StructDecl):
        fields: Dict[str, Type] = {}
        seen = set()
        for f in node.fields:
            if f.name in seen:
                self._error(f"duplicate field '{f.name}' in struct '{node.name}'", f.token)
            seen.add(f.name)
            fields[f.name] = self._resolve_type(f.type_name, f.token)
        struct_type = StructType(node.name, fields)
        sym = Symbol(node.name, struct_type, SymbolKind.STRUCT, node.token.line, node.token.column)
        if not self._table.insert(sym):
            self._error(f"duplicate declaration of struct '{node.name}'", node.token)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _resolve_type(self, name: str, token) -> Type:
        builtin = resolve_builtin(name)
        if builtin is not None:
            return builtin
        sym = self._table.lookup(name)
        if sym is not None and isinstance(sym.type, StructType):
            return sym.type
        self._error(f"unknown type '{name}'", token)
        return ERROR_TYPE

    def _error(self, message: str, token, kind: str = "error"):
        err = SemanticError(message, token.line, token.column, kind)
        self._errors.append(err)
        print(err, file=sys.stderr)

    def _infer(self, node: ASTNode) -> Type:
        """Visit an expression node and return its inferred type."""
        result = node.accept(self)
        t = result if isinstance(result, Type) else ERROR_TYPE
        self._type_map[id(node)] = t
        return t

    def _expect_bool(self, node: ASTNode, context: str):
        t = self._infer(node)
        if t.kind not in (BOOL_TYPE.kind,) and t is not ERROR_TYPE:
            self._error(
                f"condition in {context} must be bool, got {t}",
                node.token,
            )

    # ── Program ───────────────────────────────────────────────────────────────

    def visit_program(self, node: Program):
        for decl in node.declarations:
            decl.accept(self)

    # ── Declarations ──────────────────────────────────────────────────────────

    def visit_fn_decl(self, node: FnDecl):
        # Symbol already registered in pre-pass; just analyse the body
        sym = self._table.lookup(node.name)
        fn_type = sym.type if sym else None
        ret_type = fn_type.return_type if isinstance(fn_type, FunctionType) else VOID_TYPE

        self._table.enter_scope(f"fn {node.name}")
        prev_ret = self._current_fn_return
        self._current_fn_return = ret_type

        for p in node.params:
            p.accept(self)
        node.body.accept(self)

        self._current_fn_return = prev_ret
        self._table.exit_scope()

    def visit_param(self, node: Param):
        t = self._resolve_type(node.type_name, node.token)
        sym = Symbol(node.name, t, SymbolKind.PARAMETER, node.token.line, node.token.column)
        if not self._table.insert(sym):
            self._error(f"duplicate parameter '{node.name}'", node.token)

    def visit_var_decl(self, node: VarDecl):
        declared_type = self._resolve_type(node.type_name, node.token)
        init_type: Optional[Type] = None
        if node.initializer is not None:
            init_type = self._infer(node.initializer)
            if not init_type.is_compatible_with(declared_type):
                self._error(
                    f"cannot initialise '{node.name}' of type {declared_type} "
                    f"with value of type {init_type}",
                    node.token,
                )
        sym = Symbol(node.name, declared_type, SymbolKind.VARIABLE, node.token.line, node.token.column)
        if not self._table.insert(sym):
            self._error(f"duplicate declaration of '{node.name}'", node.token)

    def visit_struct_decl(self, node: StructDecl):
        # Already registered in pre-pass; nothing more to do at statement level
        pass

    def visit_struct_field(self, node: StructField):
        pass

    # ── Statements ────────────────────────────────────────────────────────────

    def visit_block_stmt(self, node: BlockStmt):
        self._table.enter_scope("block")
        for stmt in node.body:
            stmt.accept(self)
        self._table.exit_scope()

    def visit_if_stmt(self, node: IfStmt):
        self._expect_bool(node.condition, "if")
        node.then_branch.accept(self)
        if node.else_branch:
            node.else_branch.accept(self)

    def visit_while_stmt(self, node: WhileStmt):
        self._expect_bool(node.condition, "while")
        node.body.accept(self)

    def visit_for_stmt(self, node: ForStmt):
        self._table.enter_scope("for")
        if node.init:
            node.init.accept(self)
        if node.condition:
            self._expect_bool(node.condition, "for")
        if node.update:
            self._infer(node.update)
        node.body.accept(self)
        self._table.exit_scope()

    def visit_return_stmt(self, node: ReturnStmt):
        expected = self._current_fn_return or VOID_TYPE
        if node.value is None:
            if expected != VOID_TYPE and expected.kind != ERROR_TYPE.kind:
                self._error(
                    f"missing return value; function returns {expected}",
                    node.token,
                )
        else:
            actual = self._infer(node.value)
            if not actual.is_compatible_with(expected):
                self._error(
                    f"return type mismatch: expected {expected}, got {actual}",
                    node.token,
                )

    def visit_expr_stmt(self, node: ExprStmt):
        self._infer(node.expr)

    # ── Expressions (all return Type) ─────────────────────────────────────────

    def visit_binary_expr(self, node: BinaryExpr) -> Type:
        left  = self._infer(node.left)
        right = self._infer(node.right)
        result = binary_result_type(node.op, left, right)
        if result is None:
            self._error(
                f"operator '{node.op}' cannot be applied to {left} and {right}",
                node.token,
            )
            return ERROR_TYPE
        return result

    def visit_unary_expr(self, node: UnaryExpr) -> Type:
        operand = self._infer(node.operand)
        result = unary_result_type(node.op, operand)
        if result is None:
            self._error(
                f"operator '{node.op}' cannot be applied to {operand}",
                node.token,
            )
            return ERROR_TYPE
        return result

    def visit_assign_expr(self, node: AssignExpr) -> Type:
        sym = self._table.lookup(node.target)
        if sym is None:
            self._error(f"undeclared identifier '{node.target}'", node.token)
            self._infer(node.value)
            return ERROR_TYPE
        if sym.kind == SymbolKind.FUNCTION:
            self._error(f"cannot assign to function '{node.target}'", node.token)
        val_type = self._infer(node.value)
        if node.op != "=":
            # compound: e.g. +=  — both sides must be numeric
            compound_result = binary_result_type(node.op[0], sym.type, val_type)
            if compound_result is None:
                self._error(
                    f"operator '{node.op}' cannot be applied to {sym.type} and {val_type}",
                    node.token,
                )
                return ERROR_TYPE
            val_type = compound_result
        if not val_type.is_compatible_with(sym.type):
            self._error(
                f"cannot assign {val_type} to '{node.target}' of type {sym.type}",
                node.token,
            )
        return sym.type

    def visit_call_expr(self, node: CallExpr) -> Type:
        sym = self._table.lookup(node.callee)
        if sym is None:
            self._error(f"undeclared function '{node.callee}'", node.token)
            for arg in node.args:
                self._infer(arg)
            return ERROR_TYPE
        if not isinstance(sym.type, FunctionType):
            self._error(f"'{node.callee}' is not a function", node.token)
            return ERROR_TYPE
        fn_type: FunctionType = sym.type
        arg_types = [self._infer(a) for a in node.args]
        if len(arg_types) != len(fn_type.param_types):
            self._error(
                f"'{node.callee}' expects {len(fn_type.param_types)} argument(s), "
                f"got {len(arg_types)}",
                node.token,
            )
        else:
            for i, (at, pt) in enumerate(zip(arg_types, fn_type.param_types)):
                if not at.is_compatible_with(pt):
                    self._error(
                        f"argument {i + 1} of '{node.callee}': expected {pt}, got {at}",
                        node.token,
                    )
        return fn_type.return_type

    def visit_identifier_expr(self, node: IdentifierExpr) -> Type:
        sym = self._table.lookup(node.name)
        if sym is None:
            self._error(f"undeclared identifier '{node.name}'", node.token)
            return ERROR_TYPE
        return sym.type

    def visit_int_literal(self, node: IntLiteral) -> Type:
        return INT_TYPE

    def visit_float_literal(self, node: FloatLiteral) -> Type:
        return FLOAT_TYPE

    def visit_string_literal(self, node: StringLiteral) -> Type:
        return STRING_TYPE

    def visit_bool_literal(self, node: BoolLiteral) -> Type:
        return BOOL_TYPE
