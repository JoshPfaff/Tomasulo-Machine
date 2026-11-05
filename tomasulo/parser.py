import re
from pathlib import Path

from .instructions import Instruction, Op

REGISTER_COUNT = 10
REGISTER_PATTERN = re.compile(r"R([0-9]+)$", re.IGNORECASE)


def _register(token: str) -> int:
    match = REGISTER_PATTERN.fullmatch(token.strip())
    if match is None:
        raise ValueError(f"expected a register such as R1, got '{token}'")
    number = int(match.group(1))
    if not 0 <= number < REGISTER_COUNT:
        raise ValueError(f"register out of range: {token}")
    return number


def parse_instruction(line: str) -> Instruction:
    cleaned = line.split("#", 1)[0].replace(",", " ")
    cleaned = cleaned.replace("(", " ").replace(")", " ")
    parts = cleaned.split()
    if not parts:
        raise ValueError("empty instruction")
    try:
        op = Op(parts[0].upper())
    except ValueError as error:
        raise ValueError(f"unknown opcode: {parts[0]}") from error

    try:
        if len(parts) != 4:
            raise ValueError(f"{op.value} syntax is: {op.value} destination, source1, source2")
        return Instruction(
            op,
            destination=_register(parts[1]),
            source_1=_register(parts[2]),
            source_2=_register(parts[3]),
        )
    except ValueError as error:
        if str(error).startswith(("ADD syntax", "SUB syntax", "MUL syntax", "DIV syntax")):
            raise
        raise ValueError(f"invalid {op.value} instruction: {error}") from error


def parse_program(text: str) -> list[Instruction]:
    program = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.split("#", 1)[0].strip():
            try:
                program.append(parse_instruction(line))
            except ValueError as error:
                raise ValueError(f"line {line_number}: {error}") from error
    if not program:
        raise ValueError("program must contain at least one instruction")
    return program


def read_program(path: Path) -> list[Instruction]:
    try:
        return parse_program(path.read_text(encoding="utf-8-sig"))
    except OSError as error:
        raise ValueError(f"could not read program file '{path}': {error}") from error
