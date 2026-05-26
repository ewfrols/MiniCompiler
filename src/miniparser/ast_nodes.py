from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any
from lexer.token import Token


class Visitor(ABC):
    def visit_program(self, node: 'Program'): pass
    def visit_fn_decl(self, node: 'FnDecl'): pass
    def visit_var_decl(self, node: 'VarDecl'): pass
    def visit_struct_decl(self, node: 'StructDecl'): pass
    def visit_param(self, node: 'Param'): pass
    def visit_struct_field(self, node: 'StructField'): pass
    def visit_block_stmt(self, node: 'BlockStmt'): pass
    def visit_if_stmt(self, node: 'IfStmt'): pass
    def visit_while_stmt(self, node: 'WhileStmt'): pass
    def visit_for_stmt(self, node: 'ForStmt'): pass
    def visit_return_stmt(self, node: 'ReturnStmt'): pass
    def visit_expr_stmt(self, node: 'ExprStmt'): pass
    def visit_binary_expr(self, node: 'BinaryExpr'): pass
    def visit_unary_expr(self, node: 'UnaryExpr'): pass
    def visit_assign_expr(self, node: 'AssignExpr'): pass
    def visit_call_expr(self, node: 'CallExpr'): pass
    def visit_identifier_expr(self, node: 'IdentifierExpr'): pass
    def visit_int_literal(self, node: 'IntLiteral'): pass
    def visit_float_literal(self, node: 'FloatLiteral'): pass
    def visit_string_literal(self, node: 'StringLiteral'): pass
    def visit_bool_literal(self, node: 'BoolLiteral'): pass


class ASTNode(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor): ...


# ── Declarations ──────────────────────────────────────────────────────────────

@dataclass
class Param(ASTNode):
    type_name: str
    name: str
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_param(self)


@dataclass
class StructField(ASTNode):
    type_name: str
    name: str
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_struct_field(self)


@dataclass
class FnDecl(ASTNode):
    name: str
    params: List[Param]
    return_type: Optional[str]
    body: 'BlockStmt'
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_fn_decl(self)


@dataclass
class VarDecl(ASTNode):
    type_name: str
    name: str
    initializer: Optional[ASTNode]
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_var_decl(self)


@dataclass
class StructDecl(ASTNode):
    name: str
    fields: List[StructField]
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_struct_decl(self)


# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class BlockStmt(ASTNode):
    body: List[ASTNode]
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_block_stmt(self)


@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_branch: ASTNode
    else_branch: Optional[ASTNode]
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_if_stmt(self)


@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: ASTNode
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_while_stmt(self)


@dataclass
class ForStmt(ASTNode):
    init: Optional[ASTNode]
    condition: Optional[ASTNode]
    update: Optional[ASTNode]
    body: ASTNode
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_for_stmt(self)


@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode]
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_return_stmt(self)


@dataclass
class ExprStmt(ASTNode):
    expr: ASTNode
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_expr_stmt(self)


# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass
class BinaryExpr(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_binary_expr(self)


@dataclass
class UnaryExpr(ASTNode):
    op: str
    operand: ASTNode
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_unary_expr(self)


@dataclass
class AssignExpr(ASTNode):
    target: str
    op: str
    value: ASTNode
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_assign_expr(self)


@dataclass
class CallExpr(ASTNode):
    callee: str
    args: List[ASTNode]
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_call_expr(self)


@dataclass
class IdentifierExpr(ASTNode):
    name: str
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_identifier_expr(self)


@dataclass
class IntLiteral(ASTNode):
    value: int
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_int_literal(self)


@dataclass
class FloatLiteral(ASTNode):
    value: float
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_float_literal(self)


@dataclass
class StringLiteral(ASTNode):
    value: str
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_string_literal(self)


@dataclass
class BoolLiteral(ASTNode):
    value: bool
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_bool_literal(self)


# ── Program root ──────────────────────────────────────────────────────────────

@dataclass
class Program(ASTNode):
    declarations: List[ASTNode]
    token: Token

    def accept(self, visitor: Visitor):
        return visitor.visit_program(self)
