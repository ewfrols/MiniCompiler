from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional

class TokenType(Enum):
    # Ключевые слова
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_FOR = auto()
    KW_INT = auto()
    KW_FLOAT = auto()
    KW_BOOL = auto()
    KW_RETURN = auto()
    KW_TRUE = auto()
    KW_FALSE = auto()
    KW_VOID = auto()
    KW_STRUCT = auto()
    KW_FN = auto()

    # Идентификаторы и литералы
    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()

    # Операторы
    OP_PLUS = auto()
    OP_MINUS = auto()
    OP_STAR = auto()
    OP_SLASH = auto()
    OP_PERCENT = auto()
    OP_EQ = auto()
    OP_NE = auto()
    OP_LT = auto()
    OP_LE = auto()
    OP_GT = auto()
    OP_GE = auto()
    OP_AND = auto()
    OP_OR = auto()
    OP_NOT = auto()
    OP_ASSIGN = auto()
    OP_ASSIGN_ADD = auto()
    OP_ASSIGN_SUB = auto()
    OP_ASSIGN_MUL = auto()
    OP_ASSIGN_DIV = auto()

    # Разделители
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COMMA = auto()
    COLON = auto()

    # Специальные
    END_OF_FILE = auto()
    UNKNOWN = auto()

@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
    literal: Optional[Any] = None

    def __str__(self):
        base = f"{self.line}:{self.column} {self.type.name} \"{self.lexeme}\""
        if self.literal is not None:
            base += f" {self.literal}"
        return base