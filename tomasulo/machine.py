from dataclasses import dataclass, field

from .instructions import Instruction, Op


@dataclass
class MachineConfig:
    add_stations: int = 2
    mul_stations: int = 2
    add_units: int = 1
    mul_units: int = 1
    add_latency: int = 2
    sub_latency: int = 2
    mul_latency: int = 10
    div_latency: int = 20
    register_count: int = 10


@dataclass
class Operand:
    value: float = 0.0
    tag: str | None = None
    available_cycle: int = 0

    def ready(self, cycle: int) -> bool:
        return self.tag is None and self.available_cycle <= cycle


@dataclass
class Station:
    name: str
    kind: str
    busy: bool = False
    instruction_index: int | None = None
    op: Op | None = None
    first: Operand = field(default_factory=Operand)
    second: Operand = field(default_factory=Operand)
    remaining: int = 0
    result: float = 0.0
    executing: bool = False
    available_cycle: int = 0


class Machine:
    def __init__(
        self,
        program: list[Instruction],
        config: MachineConfig | None = None,
        registers: list[float] | None = None,
    ) -> None:
        self.program = program
        self.config = config or MachineConfig()
        if len(program) == 0:
            raise ValueError("program must not be empty")
        if min(
            self.config.add_stations,
            self.config.mul_stations,
            self.config.add_units,
            self.config.mul_units,
        ) < 1:
            raise ValueError("reservation-station and execution-unit counts must be at least 1")
        if min(
            self.config.add_latency,
            self.config.sub_latency,
            self.config.mul_latency,
            self.config.div_latency,
        ) < 1:
            raise ValueError("execution latencies must be at least 1")
        self.registers = list(registers or [float(index) for index in range(self.config.register_count)])
        if len(self.registers) != self.config.register_count:
            raise ValueError("register initialization has the wrong number of values")
        self.register_tags: list[str | None] = [None] * self.config.register_count
        self.stations = self._make_stations()
        self.next_instruction = 0
        self.cycle = 0
        self.events: list[str] = []

    def _make_stations(self) -> list[Station]:
        stations = []
        stations.extend(Station(f"Add{i}", "add") for i in range(1, self.config.add_stations + 1))
        stations.extend(Station(f"Mul{i}", "mul") for i in range(1, self.config.mul_stations + 1))
        return stations

    def _kind(self, op: Op) -> str:
        if op in (Op.ADD, Op.SUB):
            return "add"
        if op in (Op.MUL, Op.DIV):
            return "mul"
        raise ValueError(f"unsupported operation: {op}")

    def _latency(self, op: Op) -> int:
        if op == Op.ADD:
            return self.config.add_latency
        if op == Op.SUB:
            return self.config.sub_latency
        if op == Op.MUL:
            return self.config.mul_latency
        return self.config.div_latency

    def _operand(self, register: int) -> Operand:
        tag = self.register_tags[register]
        return Operand(self.registers[register], tag)

    def _free_station(self, kind: str) -> Station | None:
        return next(
            (
                station
                for station in self.stations
                if station.kind == kind
                and not station.busy
                and station.available_cycle <= self.cycle
            ),
            None,
        )

    def _execution_units_available(self, kind: str) -> bool:
        limit = self.config.add_units if kind == "add" else self.config.mul_units
        active = sum(station.executing for station in self.stations if station.kind == kind)
        return active < limit

    def _issue(self) -> None:
        if self.next_instruction >= len(self.program):
            return
        instruction = self.program[self.next_instruction]
        station = self._free_station(self._kind(instruction.op))
        if station is None:
            return
        station.busy = True
        station.instruction_index = self.next_instruction
        station.op = instruction.op
        station.first = self._operand(instruction.source_1)
        station.second = self._operand(instruction.source_2)
        self.register_tags[instruction.destination] = station.name
        instruction.issue = self.cycle
        self.events.append(f"cycle {self.cycle}: issue I{self.next_instruction + 1} -> {station.name}")
        self.next_instruction += 1

    def _execute(self) -> None:
        for station in self.stations:
            if not station.busy:
                continue
            if not station.executing:
                if not (
                    station.first.ready(self.cycle)
                    and station.second.ready(self.cycle)
                ):
                    continue
                if not self._execution_units_available(station.kind):
                    continue
                station.executing = True
                station.remaining = self._latency(station.op)
                self.program[station.instruction_index].dispatch = self.cycle
                self.events.append(f"cycle {self.cycle}: dispatch I{station.instruction_index + 1}")
            station.remaining -= 1
            if station.remaining != 0:
                continue
            if station.op == Op.ADD:
                station.result = station.first.value + station.second.value
            elif station.op == Op.SUB:
                station.result = station.first.value - station.second.value
            elif station.op == Op.MUL:
                station.result = station.first.value * station.second.value
            elif station.op == Op.DIV:
                if station.second.value == 0:
                    raise ZeroDivisionError(f"division by zero in I{station.instruction_index + 1}")
                station.result = station.first.value / station.second.value

    def _broadcast(self) -> None:
        completed = next((station for station in self.stations if station.busy and station.executing and station.remaining == 0), None)
        if completed is None:
            return
        instruction = self.program[completed.instruction_index]
        instruction.broadcast = self.cycle
        destination = instruction.destination
        if self.register_tags[destination] == completed.name:
            self.registers[destination] = completed.result
            self.register_tags[destination] = None
        for station in self.stations:
            if station.first.tag == completed.name:
                station.first = Operand(completed.result, available_cycle=self.cycle + 1)
            if station.second.tag == completed.name:
                station.second = Operand(completed.result, available_cycle=self.cycle + 1)
        self.events.append(f"cycle {self.cycle}: broadcast I{completed.instruction_index + 1} ({completed.result:g})")
        completed.busy = False
        completed.executing = False
        completed.available_cycle = self.cycle + 1
        completed.instruction_index = None
        completed.op = None

    def run(self, trace: bool = False) -> list[str]:
        output = []
        while self.next_instruction < len(self.program) or any(station.busy for station in self.stations):
            self.cycle += 1
            self._broadcast()
            self._execute()
            self._issue()
            if trace:
                output.append(self.state())
        return output

    def state(self) -> str:
        stations = " ".join(
            f"{station.name}={'busy' if station.busy else 'free'}"
            for station in self.stations
        )
        return f"cycle {self.cycle}: {stations}"
