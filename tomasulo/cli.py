import argparse
from pathlib import Path

from .machine import Machine, MachineConfig
from .parser import parse_program, read_program


SAMPLE = """\
MUL R3, R1, R2
ADD R4, R3, R1
DIV R5, R4, R2
"""


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _interactive() -> tuple[list, MachineConfig]:
    instruction_count = _positive(input("Number of instructions: "))
    print("Enter instructions one per line.")
    lines = []
    for instruction_number in range(1, instruction_count + 1):
        line = input(f"I{instruction_number}> ")
        if not line.strip():
            raise ValueError(f"instruction {instruction_number} cannot be blank")
        lines.append(line)
    program = parse_program("\n".join(lines))
    add = _positive(input("Number of add/sub reservation stations [2]: ") or "2")
    mul = _positive(input("Number of mul/div reservation stations [2]: ") or "2")
    add_units = _positive(input("Number of add/sub execution units [1]: ") or "1")
    mul_units = _positive(input("Number of mul/div execution units [1]: ") or "1")
    add_latency = _positive(input("Cycles for add [2]: ") or "2")
    sub_latency = _positive(input("Cycles for sub [2]: ") or "2")
    mul_latency = _positive(input("Cycles for mul [10]: ") or "10")
    div_latency = _positive(input("Cycles for div [20]: ") or "20")
    return program, MachineConfig(
        add_stations=add,
        mul_stations=mul,
        add_units=add_units,
        mul_units=mul_units,
        add_latency=add_latency,
        sub_latency=sub_latency,
        mul_latency=mul_latency,
        div_latency=div_latency,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configurable Tomasulo algorithm simulator")
    parser.add_argument("program", nargs="?", type=Path, help="instruction file; omit for interactive mode")
    parser.add_argument("--add-stations", type=_positive, default=2)
    parser.add_argument("--mul-stations", type=_positive, default=2)
    parser.add_argument("--add-units", type=_positive, default=1)
    parser.add_argument("--mul-units", type=_positive, default=1)
    parser.add_argument("--add-latency", type=_positive, default=2)
    parser.add_argument("--sub-latency", type=_positive, default=2)
    parser.add_argument("--mul-latency", type=_positive, default=10)
    parser.add_argument("--div-latency", type=_positive, default=20)
    parser.add_argument("--trace", action="store_true", help="print station state every cycle")
    parser.add_argument("--sample", action="store_true", help="run the built-in sample program")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.sample:
        program = parse_program(SAMPLE)
        config = MachineConfig(
            add_stations=args.add_stations,
            mul_stations=args.mul_stations,
            add_units=args.add_units,
            mul_units=args.mul_units,
            add_latency=args.add_latency,
            sub_latency=args.sub_latency,
            mul_latency=args.mul_latency,
            div_latency=args.div_latency,
        )
    elif args.program:
        program = read_program(args.program)
        config = MachineConfig(
            add_stations=args.add_stations,
            mul_stations=args.mul_stations,
            add_units=args.add_units,
            mul_units=args.mul_units,
            add_latency=args.add_latency,
            sub_latency=args.sub_latency,
            mul_latency=args.mul_latency,
            div_latency=args.div_latency,
        )
    else:
        program, config = _interactive()
    machine = Machine(program, config)
    trace = machine.run(trace=args.trace)
    print("\n".join(machine.events))
    if args.trace:
        print("\n".join(trace))
    print(f"\nCompleted in {machine.cycle} cycles.")
    print("Registers:", " ".join(f"R{i}={value:g}" for i, value in enumerate(machine.registers)))
    print("\nTiming graph")
    print(f"{'Instruction':<24} {'Issue':>5} {'Dispatch':>8} {'Broadcast':>9}")
    print("-" * 52)
    for index, instruction in enumerate(program, start=1):
        operands = f"R{instruction.source_1}, R{instruction.source_2}"
        label = f"I{index} {instruction.op.value} R{instruction.destination}, {operands}"
        print(
            f"{label:<24} {instruction.issue:>5} "
            f"{instruction.dispatch:>8} {instruction.broadcast:>9}"
        )
