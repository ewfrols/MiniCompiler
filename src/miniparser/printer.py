from typing import List, Optional
from .ast_nodes import (
    Visitor, ASTNode,
    Program, FnDecl, VarDecl, StructDecl, Param, StructField,
    BlockStmt, IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, AssignExpr, CallExpr,
    IdentifierExpr, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
)


class TextPrinter(Visitor):
    """Produces an indented text representation of the AST."""

    def __init__(self):
        self._depth = 0
        self._lines: List[str] = []

    def render(self, node: ASTNode) -> str:
        self._lines = []
        self._depth = 0
        node.accept(self)
        return "\n".join(self._lines)

    def _emit(self, text: str):
        self._lines.append("  " * self._depth + text)

    def _visit_child(self, node: Optional[ASTNode]):
        if node is None:
            return
        self._depth += 1
        node.accept(self)
        self._depth -= 1

    def _visit_children(self, *nodes: Optional[ASTNode]):
        for node in nodes:
            self._visit_child(node)

    def _visit_list(self, nodes: list):
        for node in nodes:
            self._visit_child(node)

    # ── Program ───────────────────────────────────────────────────────────────

    def visit_program(self, node: Program):
        self._emit("Program")
        self._visit_list(node.declarations)

    # ── Declarations ──────────────────────────────────────────────────────────

    def visit_fn_decl(self, node: FnDecl):
        rt = node.return_type if node.return_type else "none"
        self._emit(f"FnDecl name={node.name} return_type={rt}")
        self._visit_list(node.params)
        self._visit_child(node.body)

    def visit_param(self, node: Param):
        self._emit(f"Param type={node.type_name} name={node.name}")

    def visit_var_decl(self, node: VarDecl):
        self._emit(f"VarDecl type={node.type_name} name={node.name}")
        self._visit_child(node.initializer)

    def visit_struct_decl(self, node: StructDecl):
        self._emit(f"StructDecl name={node.name}")
        self._visit_list(node.fields)

    def visit_struct_field(self, node: StructField):
        self._emit(f"StructField type={node.type_name} name={node.name}")

    # ── Statements ────────────────────────────────────────────────────────────

    def visit_block_stmt(self, node: BlockStmt):
        self._emit("Block")
        self._visit_list(node.body)

    def visit_if_stmt(self, node: IfStmt):
        self._emit("IfStmt")
        self._visit_children(node.condition, node.then_branch, node.else_branch)

    def visit_while_stmt(self, node: WhileStmt):
        self._emit("WhileStmt")
        self._visit_children(node.condition, node.body)

    def visit_for_stmt(self, node: ForStmt):
        self._emit("ForStmt")
        self._visit_children(node.init, node.condition, node.update, node.body)

    def visit_return_stmt(self, node: ReturnStmt):
        self._emit("ReturnStmt")
        self._visit_child(node.value)

    def visit_expr_stmt(self, node: ExprStmt):
        self._emit("ExprStmt")
        self._visit_child(node.expr)

    # ── Expressions ───────────────────────────────────────────────────────────

    def visit_binary_expr(self, node: BinaryExpr):
        self._emit(f"BinaryExpr op={node.op}")
        self._visit_children(node.left, node.right)

    def visit_unary_expr(self, node: UnaryExpr):
        self._emit(f"UnaryExpr op={node.op}")
        self._visit_child(node.operand)

    def visit_assign_expr(self, node: AssignExpr):
        self._emit(f"AssignExpr op={node.op} target={node.target}")
        self._visit_child(node.value)

    def visit_call_expr(self, node: CallExpr):
        self._emit(f"CallExpr name={node.callee}")
        self._visit_list(node.args)

    def visit_identifier_expr(self, node: IdentifierExpr):
        self._emit(f"Identifier name={node.name}")

    def visit_int_literal(self, node: IntLiteral):
        self._emit(f"IntLiteral value={node.value}")

    def visit_float_literal(self, node: FloatLiteral):
        self._emit(f"FloatLiteral value={node.value}")

    def visit_string_literal(self, node: StringLiteral):
        self._emit(f"StringLiteral value={node.value!r}")

    def visit_bool_literal(self, node: BoolLiteral):
        self._emit(f"BoolLiteral value={node.value}")


class DotPrinter(Visitor):
    """Produces a Graphviz DOT representation of the AST."""

    def __init__(self):
        self._counter = 0
        self._lines: List[str] = []

    def render(self, node: ASTNode) -> str:
        self._counter = 0
        self._lines = ['digraph AST {', '  node [shape=box fontname="monospace"];']
        node.accept(self)
        self._lines.append('}')
        return "\n".join(self._lines)

    def _new_id(self) -> int:
        nid = self._counter
        self._counter += 1
        return nid

    def _node(self, nid: int, label: str):
        escaped = label.replace('"', '\\"')
        self._lines.append(f'  n{nid} [label="{escaped}"];')

    def _edge(self, parent: int, child: int):
        self._lines.append(f'  n{parent} -> n{child};')

    def _visit_child(self, parent_id: int, node: Optional[ASTNode]) -> Optional[int]:
        if node is None:
            return None
        prev_parent = self._current_parent
        self._current_parent = parent_id
        node.accept(self)
        cid = self._last_id
        self._current_parent = prev_parent
        return cid

    def render(self, node: ASTNode) -> str:
        self._counter = 0
        self._lines = ['digraph AST {', '  node [shape=box fontname="monospace"];']
        self._current_parent: Optional[int] = None
        self._last_id: int = 0
        node.accept(self)
        self._lines.append('}')
        return "\n".join(self._lines)

    def _emit_node(self, label: str, children: list) -> int:
        nid = self._new_id()
        self._node(nid, label)
        if self._current_parent is not None:
            self._edge(self._current_parent, nid)
        old_parent = self._current_parent
        self._current_parent = nid
        for child in children:
            if child is not None:
                child.accept(self)
        self._current_parent = old_parent
        self._last_id = nid
        return nid

    def visit_program(self, node: Program):
        self._emit_node("Program", node.declarations)

    def visit_fn_decl(self, node: FnDecl):
        rt = node.return_type if node.return_type else "none"
        self._emit_node(f"FnDecl\\nname={node.name}\\nreturn={rt}", node.params + [node.body])

    def visit_param(self, node: Param):
        self._emit_node(f"Param\\n{node.type_name} {node.name}", [])

    def visit_var_decl(self, node: VarDecl):
        children = [node.initializer] if node.initializer else []
        self._emit_node(f"VarDecl\\n{node.type_name} {node.name}", children)

    def visit_struct_decl(self, node: StructDecl):
        self._emit_node(f"StructDecl\\n{node.name}", node.fields)

    def visit_struct_field(self, node: StructField):
        self._emit_node(f"Field\\n{node.type_name} {node.name}", [])

    def visit_block_stmt(self, node: BlockStmt):
        self._emit_node("Block", node.body)

    def visit_if_stmt(self, node: IfStmt):
        children = [node.condition, node.then_branch]
        if node.else_branch:
            children.append(node.else_branch)
        self._emit_node("IfStmt", children)

    def visit_while_stmt(self, node: WhileStmt):
        self._emit_node("WhileStmt", [node.condition, node.body])

    def visit_for_stmt(self, node: ForStmt):
        children = [c for c in [node.init, node.condition, node.update, node.body] if c is not None]
        self._emit_node("ForStmt", children)

    def visit_return_stmt(self, node: ReturnStmt):
        children = [node.value] if node.value else []
        self._emit_node("ReturnStmt", children)

    def visit_expr_stmt(self, node: ExprStmt):
        self._emit_node("ExprStmt", [node.expr])

    def visit_binary_expr(self, node: BinaryExpr):
        self._emit_node(f"BinaryExpr\\nop={node.op}", [node.left, node.right])

    def visit_unary_expr(self, node: UnaryExpr):
        self._emit_node(f"UnaryExpr\\nop={node.op}", [node.operand])

    def visit_assign_expr(self, node: AssignExpr):
        self._emit_node(f"AssignExpr\\n{node.target} {node.op}", [node.value])

    def visit_call_expr(self, node: CallExpr):
        self._emit_node(f"CallExpr\\n{node.callee}()", node.args)

    def visit_identifier_expr(self, node: IdentifierExpr):
        self._emit_node(f"Identifier\\n{node.name}", [])

    def visit_int_literal(self, node: IntLiteral):
        self._emit_node(f"IntLiteral\\n{node.value}", [])

    def visit_float_literal(self, node: FloatLiteral):
        self._emit_node(f"FloatLiteral\\n{node.value}", [])

    def visit_string_literal(self, node: StringLiteral):
        self._emit_node(f"StringLiteral\\n{node.value!r}", [])

    def visit_bool_literal(self, node: BoolLiteral):
        self._emit_node(f"BoolLiteral\\n{node.value}", [])
