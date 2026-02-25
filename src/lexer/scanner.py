import sys
from .token import Token, TokenType
from .errors import LexicalError

class Scanner:

    def __init__(self, source: str):
        self.source = source
        self.start = 0          
        self.current = 0         
        self.line = 1
        self.column = 1
        self.errors: list[LexicalError] = []

        # Таблица ключевых слов
        self.keywords = {
            'if': TokenType.KW_IF,
            'else': TokenType.KW_ELSE,
            'while': TokenType.KW_WHILE,
            'for': TokenType.KW_FOR,
            'int': TokenType.KW_INT,
            'float': TokenType.KW_FLOAT,
            'bool': TokenType.KW_BOOL,
            'return': TokenType.KW_RETURN,
            'true': TokenType.KW_TRUE,
            'false': TokenType.KW_FALSE,
            'void': TokenType.KW_VOID,
            'struct': TokenType.KW_STRUCT,
            'fn': TokenType.KW_FN,
        }

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def peek_token(self) -> Token:
        saved = (self.start, self.current, self.line, self.column)
        token = self.next_token()
        self.start, self.current, self.line, self.column = saved
        return token

    def next_token(self) -> Token:
        self._skip_whitespace()
        self.start = self.current
        if self.is_at_end():
            return self._make_token(TokenType.END_OF_FILE)

        c = self._advance()

        if c.isalpha() or c == '_':
            return self._identifier()
        if c.isdigit():
            return self._number()
        if c == '"':
            return self._string()

        if c == '=':
            return self._make_token(TokenType.OP_EQ) if self._match('=') else self._make_token(TokenType.OP_ASSIGN)
        if c == '!':
            return self._make_token(TokenType.OP_NE) if self._match('=') else self._make_token(TokenType.OP_NOT)
        if c == '<':
            return self._make_token(TokenType.OP_LE) if self._match('=') else self._make_token(TokenType.OP_LT)
        if c == '>':
            return self._make_token(TokenType.OP_GE) if self._match('=') else self._make_token(TokenType.OP_GT)
        if c == '+':
            return self._make_token(TokenType.OP_ASSIGN_ADD) if self._match('=') else self._make_token(TokenType.OP_PLUS)
        if c == '-':
            return self._make_token(TokenType.OP_ASSIGN_SUB) if self._match('=') else self._make_token(TokenType.OP_MINUS)
        if c == '*':
            return self._make_token(TokenType.OP_ASSIGN_MUL) if self._match('=') else self._make_token(TokenType.OP_STAR)
        if c == '/':
            if self._match('='):
                return self._make_token(TokenType.OP_ASSIGN_DIV)
            if self._match('/'):        
                self._skip_line_comment()
                return self.next_token()
            if self._match('*'):           
                self._skip_block_comment()
                return self.next_token()
            return self._make_token(TokenType.OP_SLASH)
        if c == '%':
            return self._make_token(TokenType.OP_PERCENT)
        if c == '&':
            if self._match('&'):
                return self._make_token(TokenType.OP_AND)
        if c == '|':
            if self._match('|'):
                return self._make_token(TokenType.OP_OR)
        if c == '(':
            return self._make_token(TokenType.LPAREN)
        if c == ')':
            return self._make_token(TokenType.RPAREN)
        if c == '{':
            return self._make_token(TokenType.LBRACE)
        if c == '}':
            return self._make_token(TokenType.RBRACE)
        if c == '[':
            return self._make_token(TokenType.LBRACKET)
        if c == ']':
            return self._make_token(TokenType.RBRACKET)
        if c == ';':
            return self._make_token(TokenType.SEMICOLON)
        if c == ',':
            return self._make_token(TokenType.COMMA)
        if c == ':':
            return self._make_token(TokenType.COLON)

        self._error(f"Unexpected character '{c}'")
        return self._make_token(TokenType.UNKNOWN)

    # Вспомогательные методы
    def _advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self._advance()
        return True

    def _peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def _skip_whitespace(self):
        while not self.is_at_end():
            c = self._peek()
            if c in ' \t\r\n':
                self._advance()
            else:
                break

    def _skip_line_comment(self):
        while not self.is_at_end() and self._peek() != '\n':
            self._advance()
        # новую строку обработает _skip_whitespace при следующем вызове

    def _skip_block_comment(self):
        nesting = 1
        while not self.is_at_end() and nesting > 0:
            if self._peek() == '*' and not self.is_at_end() and self.source[self.current+1] == '/':
                self._advance()
                self._advance()
                nesting -= 1
            elif self._peek() == '/' and not self.is_at_end() and self.source[self.current+1] == '*':
                self._advance()
                self._advance()
                nesting += 1
            else:
                self._advance()
        if nesting > 0:
            self._error("Unterminated block comment")

    def _identifier(self) -> Token:
        while not self.is_at_end() and (self._peek().isalnum() or self._peek() == '_'):
            self._advance()
        text = self.source[self.start:self.current]
        tok_type = self.keywords.get(text, TokenType.IDENTIFIER)
        return self._make_token(tok_type)

    def _number(self) -> Token:
        is_float = False
        while not self.is_at_end() and self._peek().isdigit():
            self._advance()
        if not self.is_at_end() and self._peek() == '.':
            is_float = True
            self._advance()  
            if not self.is_at_end() and self._peek().isdigit():
                while not self.is_at_end() and self._peek().isdigit():
                    self._advance()
            else:
                self._error("Malformed float literal: expected digits after '.'")
                return self._make_token(TokenType.UNKNOWN)
        num_str = self.source[self.start:self.current]
        if is_float:
            return self._make_token(TokenType.FLOAT_LITERAL, literal=float(num_str))
        else:
            return self._make_token(TokenType.INT_LITERAL, literal=int(num_str))

    def _string(self) -> Token:
        value = ''
        while not self.is_at_end() and self._peek() != '"':
            if self._peek() == '\n':
                self._advance()
                pass
            value += self._advance()
        if self.is_at_end():
            self._error("Unterminated string")
            return self._make_token(TokenType.STRING_LITERAL, literal=value)
        self._advance()  
        return self._make_token(TokenType.STRING_LITERAL, literal=value)

    def _make_token(self, tok_type: TokenType, literal=None) -> Token:
        lexeme = self.source[self.start:self.current]
        col = self.column - (self.current - self.start)
        return Token(tok_type, lexeme, self.line, col, literal)

    def _error(self, message: str):
        err = LexicalError(message, self.line, self.column)
        self.errors.append(err)
        print(err, file=sys.stderr)

    def get_line(self) -> int:
        return self.line

    def get_column(self) -> int:
        return self.column