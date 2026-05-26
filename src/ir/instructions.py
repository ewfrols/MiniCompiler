from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class Opcode(Enum):
    # арифметика
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    MOD = "MOD"
    NEG = "NEG"
    # логика
    AND = "AND"
    OR  = "OR"
    NOT = "NOT"
    # сравнения
    CMP_EQ = "CMP_EQ"
    CMP_NE = "CMP_NE"
    CMP_LT = "CMP_LT"
    CMP_LE = "CMP_LE"
    CMP_GT = "CMP_GT"
    CMP_GE = "CMP_GE"
    # память
    LOAD  = "LOAD"
    STORE = "STORE"
    # управление потоком
    JUMP        = "JUMP"
    JUMP_IF     = "JUMP_IF"
    JUMP_IF_NOT = "JUMP_IF_NOT"
    # функции
    CALL   = "CALL"
    RETURN = "RETURN"
    PARAM  = "PARAM"
    # перемещение данных
    MOVE = "MOVE"


@dataclass
class Instruction:
    opcode: Opcode
    dest: Optional[str]
    args: List[str]
    comment: str = ""

    def __str__(self) -> str:
        args_str = ", ".join(self.args)
        if self.dest:
            body = f"{self.dest} = {self.opcode.value} {args_str}"
        else:
            body = f"{self.opcode.value} {args_str}" if args_str else self.opcode.value
        if self.comment:
            return f"{body:<42}  # {self.comment}"
        return body


@dataclass
class BasicBlock:
    label: str
    instructions: List[Instruction] = field(default_factory=list)
    successors: List["BasicBlock"]  = field(default_factory=list)
    predecessors: List["BasicBlock"] = field(default_factory=list)


@dataclass
class IRFunction:
    name: str
    return_type: str
    params: List[Tuple[str, str]]      # [(имя, тип), ...]
    blocks: List[BasicBlock] = field(default_factory=list)


@dataclass
class IRProgram:
    functions: List[IRFunction] = field(default_factory=list)
