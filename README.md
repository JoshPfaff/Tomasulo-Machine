# Tomasulo Machine

This project is a modular Python simulator for the Tomasulo algorithm. It
supports register renaming, reservation stations, operand forwarding,
configurable execution latencies, and cycle-by-cycle tracing for arithmetic
instructions (`ADD`, `SUB`, `MUL`, and `DIV`).

## Run

Use the built-in sample:

```powershell
python main.py --sample --trace
```

Run `python main.py` without arguments to enter the number of instructions,
then enter each instruction one at a time, followed by the reservation station
counts, execution-unit counts, and the add, subtract, multiply, and divide latencies. Execution-unit
counts limit how many ready instructions of each class can execute simultaneously. The simulator prints a
timing graph containing the issue, dispatch, and broadcast cycle for every
instruction. Registers are `R0` through `R9`.
