from dataclasses import dataclass
from enum import Enum


class Op(str, Enum):
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"


@dataclass
class Instruction:
    op: Op
    destination: int | None = None
    source_1: int | None = None
    source_2: int | None = None
    issue: int | None = None
    dispatch: int | None = None
    broadcast: int | None = None
