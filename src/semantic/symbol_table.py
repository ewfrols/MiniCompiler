from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional
from .type_system import Type


class SymbolKind(Enum):
    VARIABLE  = "variable"
    FUNCTION  = "function"
    PARAMETER = "parameter"
    STRUCT    = "struct"


@dataclass
class Symbol:
    name: str
    type: Type
    kind: SymbolKind
    line: int
    column: int


class Scope:
    def __init__(self, label: str = ""):
        self.label = label
        self._symbols: Dict[str, Symbol] = {}

    def insert(self, symbol: Symbol) -> bool:
        """Insert symbol; return False if name already declared in this scope."""
        if symbol.name in self._symbols:
            return False
        self._symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        return self._symbols.get(name)

    def symbols(self) -> List[Symbol]:
        return list(self._symbols.values())


class SymbolTable:
    def __init__(self):
        self._scopes: List[Scope] = [Scope("global")]

    # ── Scope management ──────────────────────────────────────────────────────

    def enter_scope(self, label: str = ""):
        self._scopes.append(Scope(label))

    def exit_scope(self):
        if len(self._scopes) > 1:
            self._scopes.pop()

    @property
    def depth(self) -> int:
        return len(self._scopes)

    # ── Symbol operations ─────────────────────────────────────────────────────

    def insert(self, symbol: Symbol) -> bool:
        return self._scopes[-1].insert(symbol)

    def lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self._scopes):
            sym = scope.lookup(name)
            if sym is not None:
                return sym
        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self._scopes[-1].lookup(name)

    # ── Dump ──────────────────────────────────────────────────────────────────

    def dump(self) -> str:
        lines = []
        for i, scope in enumerate(self._scopes):
            indent = "  " * i
            label = scope.label or f"scope{i}"
            lines.append(f"{indent}{label}:")
            for sym in scope.symbols():
                lines.append(f"{indent}  {sym.name}: {sym.kind.value} {sym.type}")
        return "\n".join(lines)
