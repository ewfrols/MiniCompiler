import sys
from typing import List, Optional

from lexer.token import Token, TokenType
from lexer.scanner import Scanner
from .errors import ParseError
from .ast_nodes import (
    ASTNode, Program,
    FnDecl, VarDecl, StructDecl, Param, StructField,
    BlockStmt, IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, AssignExpr, CallExpr,
    IdentifierExpr, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
)

_TYPE_TOKENS = {
    TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL, TokenType.KW_VOID,
}

_ASSIGN_OPS = {
    TokenType.OP_ASSIGN,
    TokenType.OP_ASSIGN_ADD,
    TokenType.OP_ASSIGN_SUB,
    TokenType.OP_ASSIGN_MUL,
    TokenType.OP_ASSIGN_DIV,
}


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.errors: List[ParseError] = []

    # ── Public interface ──────────────────────────────────────────────────────

    def parse(self) -> Program:
        root_token = self._peek()
        declarations = []
        while not self._is_at_end():
            try:
                declarations.append(self._declaration())
            except ParseError:
                self._synchronize()
        return Program(declarations, root_token)

    # ── Top-level ─────────────────────────────────────────────────────────────

    def _declaration(self) -> ASTNode:
        t = self._peek().type
        if t == TokenType.KW_FN:
            return self._fn_decl()
        if t == TokenType.KW_STRUCT:
            return self._struct_decl()
        if t in _TYPE_TOKENS:
            return self._var_decl()
        return self._statement()

    def _fn_decl(self) -> FnDecl:
        token = self._consume(TokenType.KW_FN, "Expected 'fn'")
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected function name")
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        params = self._params()
        self._consume(TokenType.RPAREN, "Expected ')' after parameters")
        return_type: Optional[str] = None
        if self._match(TokenType.COLON):
            return_type = self._type_name()
        body = self._block()
        return FnDecl(name_tok.lexeme, params, return_type, body, token)

    def _params(self) -> List[Param]:
        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._param())
            while self._match(TokenType.COMMA):
                params.append(self._param())
        return params

    def _param(self) -> Param:
        type_tok = self._peek()
        type_name = self._type_name()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected parameter name")
        return Param(type_name, name_tok.lexeme, type_tok)

    def _var_decl(self) -> VarDecl:
        type_tok = self._peek()
        type_name = self._type_name()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name")
        initializer: Optional[ASTNode] = None
        if self._match(TokenType.OP_ASSIGN):
            initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        return VarDecl(type_name, name_tok.lexeme, initializer, type_tok)

    def _struct_decl(self) -> StructDecl:
        token = self._consume(TokenType.KW_STRUCT, "Expected 'struct'")
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected struct name")
        self._consume(TokenType.LBRACE, "Expected '{' after struct name")
        fields = self._struct_fields()
        self._consume(TokenType.RBRACE, "Expected '}' after struct fields")
        return StructDecl(name_tok.lexeme, fields, token)

    def _struct_fields(self) -> List[StructField]:
        fields = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            type_tok = self._peek()
            type_name = self._type_name()
            name_tok = self._consume(TokenType.IDENTIFIER, "Expected field name")
            self._consume(TokenType.SEMICOLON, "Expected ';' after field declaration")
            fields.append(StructField(type_name, name_tok.lexeme, type_tok))
        return fields

    # ── Statements ────────────────────────────────────────────────────────────

    def _statement(self) -> ASTNode:
        t = self._peek().type
        if t == TokenType.LBRACE:
            return self._block()
        if t == TokenType.KW_IF:
            return self._if_stmt()
        if t == TokenType.KW_WHILE:
            return self._while_stmt()
        if t == TokenType.KW_FOR:
            return self._for_stmt()
        if t == TokenType.KW_RETURN:
            return self._return_stmt()
        return self._expr_stmt()

    def _block(self) -> BlockStmt:
        token = self._consume(TokenType.LBRACE, "Expected '{'")
        body = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            try:
                body.append(self._declaration())
            except ParseError:
                self._synchronize()
        self._consume(TokenType.RBRACE, "Expected '}'")
        return BlockStmt(body, token)

    def _if_stmt(self) -> IfStmt:
        token = self._consume(TokenType.KW_IF, "Expected 'if'")
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after condition")
        then_branch = self._statement()
        else_branch: Optional[ASTNode] = None
        if self._match(TokenType.KW_ELSE):
            else_branch = self._statement()
        return IfStmt(condition, then_branch, else_branch, token)

    def _while_stmt(self) -> WhileStmt:
        token = self._consume(TokenType.KW_WHILE, "Expected 'while'")
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after condition")
        body = self._statement()
        return WhileStmt(condition, body, token)

    def _for_stmt(self) -> ForStmt:
        token = self._consume(TokenType.KW_FOR, "Expected 'for'")
        self._consume(TokenType.LPAREN, "Expected '(' after 'for'")

        # init: var_decl (consumes ';') | expr ';' | ';'
        init: Optional[ASTNode] = None
        if self._check(TokenType.SEMICOLON):
            self._advance()
        elif self._peek().type in _TYPE_TOKENS:
            init = self._var_decl()
        else:
            init = ExprStmt(self._expression(), self._peek())
            self._consume(TokenType.SEMICOLON, "Expected ';' after for-init expression")

        # condition
        condition: Optional[ASTNode] = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after for-condition")

        # update
        update: Optional[ASTNode] = None
        if not self._check(TokenType.RPAREN):
            update = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after for-update")

        body = self._statement()
        return ForStmt(init, condition, update, body, token)

    def _return_stmt(self) -> ReturnStmt:
        token = self._consume(TokenType.KW_RETURN, "Expected 'return'")
        value: Optional[ASTNode] = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after return")
        return ReturnStmt(value, token)

    def _expr_stmt(self) -> ExprStmt:
        tok = self._peek()
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExprStmt(expr, tok)

    # ── Expressions ───────────────────────────────────────────────────────────

    def _expression(self) -> ASTNode:
        return self._assignment()

    def _assignment(self) -> ASTNode:
        expr = self._logical_or()
        if isinstance(expr, IdentifierExpr) and self._peek().type in _ASSIGN_OPS:
            op_tok = self._advance()
            value = self._assignment()
            return AssignExpr(expr.name, op_tok.lexeme, value, op_tok)
        return expr

    def _logical_or(self) -> ASTNode:
        left = self._logical_and()
        while self._check(TokenType.OP_OR):
            op_tok = self._advance()
            right = self._logical_and()
            left = BinaryExpr(left, op_tok.lexeme, right, op_tok)
        return left

    def _logical_and(self) -> ASTNode:
        left = self._equality()
        while self._check(TokenType.OP_AND):
            op_tok = self._advance()
            right = self._equality()
            left = BinaryExpr(left, op_tok.lexeme, right, op_tok)
        return left

    def _equality(self) -> ASTNode:
        left = self._comparison()
        while self._peek().type in {TokenType.OP_EQ, TokenType.OP_NE}:
            op_tok = self._advance()
            right = self._comparison()
            left = BinaryExpr(left, op_tok.lexeme, right, op_tok)
        return left

    def _comparison(self) -> ASTNode:
        left = self._addition()
        while self._peek().type in {TokenType.OP_LT, TokenType.OP_LE, TokenType.OP_GT, TokenType.OP_GE}:
            op_tok = self._advance()
            right = self._addition()
            left = BinaryExpr(left, op_tok.lexeme, right, op_tok)
        return left

    def _addition(self) -> ASTNode:
        left = self._multiplication()
        while self._peek().type in {TokenType.OP_PLUS, TokenType.OP_MINUS}:
            op_tok = self._advance()
            right = self._multiplication()
            left = BinaryExpr(left, op_tok.lexeme, right, op_tok)
        return left

    def _multiplication(self) -> ASTNode:
        left = self._unary()
        while self._peek().type in {TokenType.OP_STAR, TokenType.OP_SLASH, TokenType.OP_PERCENT}:
            op_tok = self._advance()
            right = self._unary()
            left = BinaryExpr(left, op_tok.lexeme, right, op_tok)
        return left

    def _unary(self) -> ASTNode:
        if self._peek().type in {TokenType.OP_NOT, TokenType.OP_MINUS}:
            op_tok = self._advance()
            operand = self._unary()
            return UnaryExpr(op_tok.lexeme, operand, op_tok)
        return self._call()

    def _call(self) -> ASTNode:
        expr = self._primary()
        # function call: identifier followed by '('
        if isinstance(expr, IdentifierExpr) and self._check(TokenType.LPAREN):
            paren_tok = self._advance()
            args = self._args()
            self._consume(TokenType.RPAREN, "Expected ')' after arguments")
            return CallExpr(expr.name, args, paren_tok)
        return expr

    def _args(self) -> List[ASTNode]:
        args = []
        if not self._check(TokenType.RPAREN):
            args.append(self._expression())
            while self._match(TokenType.COMMA):
                args.append(self._expression())
        return args

    def _primary(self) -> ASTNode:
        tok = self._peek()

        if tok.type == TokenType.INT_LITERAL:
            self._advance()
            return IntLiteral(tok.literal, tok)

        if tok.type == TokenType.FLOAT_LITERAL:
            self._advance()
            return FloatLiteral(tok.literal, tok)

        if tok.type == TokenType.STRING_LITERAL:
            self._advance()
            return StringLiteral(tok.literal, tok)

        if tok.type == TokenType.KW_TRUE:
            self._advance()
            return BoolLiteral(True, tok)

        if tok.type == TokenType.KW_FALSE:
            self._advance()
            return BoolLiteral(False, tok)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return IdentifierExpr(tok.lexeme, tok)

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise self._make_error(f"Unexpected token '{tok.lexeme}' in expression")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _type_name(self) -> str:
        tok = self._peek()
        if tok.type in _TYPE_TOKENS or tok.type == TokenType.IDENTIFIER:
            self._advance()
            return tok.lexeme
        raise self._make_error(f"Expected type name, got '{tok.type.name}'")

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.END_OF_FILE

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _check(self, type: TokenType) -> bool:
        return self._peek().type == type

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, type: TokenType, message: str) -> Token:
        if self._check(type):
            return self._advance()
        raise self._make_error(message)

    def _make_error(self, message: str) -> ParseError:
        tok = self._peek()
        err = ParseError(message, tok.line, tok.column)
        self.errors.append(err)
        print(err, file=sys.stderr)
        return err

    def _synchronize(self):
        self._advance()
        _sync_starts = {
            TokenType.KW_FN, TokenType.KW_STRUCT, TokenType.KW_IF,
            TokenType.KW_WHILE, TokenType.KW_FOR, TokenType.KW_RETURN,
            TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL, TokenType.KW_VOID,
        }
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._peek().type in _sync_starts:
                return
            self._advance()
