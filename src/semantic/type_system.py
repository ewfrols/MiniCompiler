from enum import Enum, auto
from typing import Dict, List, Optional


class TypeKind(Enum):
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    VOID = auto()
    STRING = auto()
    STRUCT = auto()
    FUNCTION = auto()
    ERROR = auto()   # sentinel — suppresses cascading errors


class Type:
    def __init__(self, kind: TypeKind, name: str):
        self.kind = kind
        self.name = name

    def is_numeric(self) -> bool:
        return self.kind in (TypeKind.INT, TypeKind.FLOAT)

    def is_compatible_with(self, expected: 'Type') -> bool:
        """True if self can be used where expected is required."""
        if self.kind == TypeKind.ERROR or expected.kind == TypeKind.ERROR:
            return True  # suppress cascading errors
        if self == expected:
            return True
        # int widens to float
        if self.kind == TypeKind.INT and expected.kind == TypeKind.FLOAT:
            return True
        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Type):
            return NotImplemented
        return self.kind == other.kind and self.name == other.name

    def __hash__(self) -> int:
        return hash((self.kind, self.name))

    def __repr__(self) -> str:
        return self.name


class StructType(Type):
    def __init__(self, name: str, fields: Optional[Dict[str, 'Type']] = None):
        super().__init__(TypeKind.STRUCT, name)
        self.fields: Dict[str, Type] = fields or {}

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StructType) and self.name == other.name

    def __hash__(self) -> int:
        return hash(("struct", self.name))


class FunctionType(Type):
    def __init__(self, name: str, param_types: List['Type'], return_type: 'Type'):
        super().__init__(TypeKind.FUNCTION, name)
        self.param_types = param_types
        self.return_type = return_type

    def __repr__(self) -> str:
        params = ", ".join(str(p) for p in self.param_types)
        return f"fn({params}) -> {self.return_type}"


# ── Built-in type singletons ──────────────────────────────────────────────────

INT_TYPE    = Type(TypeKind.INT,    "int")
FLOAT_TYPE  = Type(TypeKind.FLOAT,  "float")
BOOL_TYPE   = Type(TypeKind.BOOL,   "bool")
VOID_TYPE   = Type(TypeKind.VOID,   "void")
STRING_TYPE = Type(TypeKind.STRING, "string")
ERROR_TYPE  = Type(TypeKind.ERROR,  "<error>")

_BUILTINS: Dict[str, Type] = {
    "int":    INT_TYPE,
    "float":  FLOAT_TYPE,
    "bool":   BOOL_TYPE,
    "void":   VOID_TYPE,
    "string": STRING_TYPE,
}


def resolve_builtin(name: str) -> Optional[Type]:
    return _BUILTINS.get(name)


def binary_result_type(op: str, left: Type, right: Type) -> Optional[Type]:
    """Return result type of (left op right), or None if invalid."""
    if left.kind == TypeKind.ERROR or right.kind == TypeKind.ERROR:
        return ERROR_TYPE

    arithmetic = {"+", "-", "*", "/", "%"}
    comparison = {"==", "!=", "<", "<=", ">", ">="}
    logical    = {"&&", "||"}

    if op in arithmetic:
        if left.is_numeric() and right.is_numeric():
            # float wins
            if left.kind == TypeKind.FLOAT or right.kind == TypeKind.FLOAT:
                return FLOAT_TYPE
            return INT_TYPE
        return None

    if op in comparison:
        if left.is_numeric() and right.is_numeric():
            return BOOL_TYPE
        if left.kind == TypeKind.BOOL and right.kind == TypeKind.BOOL and op in {"==", "!="}:
            return BOOL_TYPE
        if left == right and op in {"==", "!="}:
            return BOOL_TYPE
        return None

    if op in logical:
        if left.kind == TypeKind.BOOL and right.kind == TypeKind.BOOL:
            return BOOL_TYPE
        return None

    return None


def unary_result_type(op: str, operand: Type) -> Optional[Type]:
    """Return result type of (op operand), or None if invalid."""
    if operand.kind == TypeKind.ERROR:
        return ERROR_TYPE
    if op == "-":
        if operand.is_numeric():
            return operand
    if op == "!":
        if operand.kind == TypeKind.BOOL:
            return BOOL_TYPE
    return None
