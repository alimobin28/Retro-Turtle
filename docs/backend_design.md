# RetroTurtle — IR Design & Backend Documentation

## Overview

Qadir's phase takes the validated AST and converts it into an executable
drawing output through three stages:

```
AST  →  [Semantic Analyzer]  →  [IR Generator]  →  [Executor]  →  Screen
```

---

## 1. Symbol Table Structure

The Symbol Table is a Python `dict` populated by the Semantic Analyzer.
It records every **identifier** (user-defined variable) seen in the program.

```python
symbol_table = {
    "myColor": {"type": "color_var", "first_seen": 3},
    "mySize":  {"type": "color_var", "first_seen": 7},
}
```

| Field        | Description                              |
|--------------|------------------------------------------|
| `type`       | Category of identifier (`color_var`)     |
| `first_seen` | Line number where it first appeared      |

In programs that only use literal colors (e.g. `color red`), the symbol
table remains empty — that is valid and expected.

---

## 2. Semantic Rules Enforced

| Rule                                   | Error raised if violated             |
|----------------------------------------|--------------------------------------|
| `forward/backward/left/right` take 1 NUMBER | SemanticError (wrong arg type) |
| `pen_up / pen_down` take 0 arguments   | SemanticError (wrong arg count)      |
| `color` takes 1 COLOR or IDENTIFIER    | SemanticError (wrong arg type)       |
| `move` takes 2 NUMBERs                 | SemanticError (wrong arg count)      |
| NUMBER arguments must be ≥ 0           | SemanticError (negative value)       |
| `repeat` count must be > 0             | SemanticError (zero/negative repeat) |
| All keywords must be known             | SemanticError (unknown command)      |

---

## 3. IR Opcodes

The IR is a **flat list** of instructions. Loops are fully unrolled — there
is no control flow in the IR.

| Opcode       | Arguments    | Example          |
|--------------|--------------|------------------|
| `PEN_DOWN`   | none         | `PEN_DOWN`       |
| `PEN_UP`     | none         | `PEN_UP`         |
| `FORWARD`    | n (int)      | `FORWARD 100`    |
| `BACKWARD`   | n (int)      | `BACKWARD 30`    |
| `LEFT`       | degrees      | `LEFT 90`        |
| `RIGHT`      | degrees      | `RIGHT 45`       |
| `COLOR`      | name (str)   | `COLOR red`      |
| `MOVE`       | x y (int)    | `MOVE 10 20`     |

---

## 4. Sample IR Output

Input (`tests/test1.rt`):
```
pen_down
color green
forward 100
left 90
forward 100
left 90
repeat 4
    forward 50
    right 90
end
color red
backward 30
pen_up
move 10 20
```

Generated IR (`output/program.ir`):
```
PEN_DOWN
COLOR green
FORWARD 100
LEFT 90
FORWARD 100
LEFT 90
FORWARD 50
RIGHT 90
FORWARD 50
RIGHT 90
FORWARD 50
RIGHT 90
FORWARD 50
RIGHT 90
COLOR red
BACKWARD 30
PEN_UP
MOVE 10 20
```

Note: the `repeat 4` loop is unrolled into 4 × `FORWARD 50` + `RIGHT 90` pairs.

---

## 5. Error Examples

### SemanticError — repeat count of 0
```
[Line 5] SemanticError: 'repeat' count must be a positive integer, got 0
```

### SemanticError — wrong argument count
```
[Line 3] SemanticError: 'pen_up' expects 0 argument(s), got 1
```

### ParseError — missing end
```
[Line 7] ParseError: 'repeat' block is not closed — expected 'end', got 'EOF'
```

### LexerError — invalid token
```
[Line 5, Col 11] LexerError: Invalid number: digit sequence followed by 'a'
```

---

## 6. How to Run

```bash
# Full pipeline (opens drawing window)
python main.py tests/test1.rt

# Stop after IR, print IR listing
python main.py tests/test1.rt --ir-only

# Save IR to output/program.ir
python main.py tests/test1.rt --ir-only --save-ir

# Full debug output (tokens + AST + symbol table + IR trace)
python main.py tests/test1.rt --debug --ir-only

# Save PNG of drawing (requires Pillow)
python main.py tests/test1.rt --save-png
```

---

## 7. Dependencies

| Library      | Required? | Purpose                          | Install              |
|--------------|-----------|----------------------------------|----------------------|
| Python 3.10+ | YES       | Core language                    | (system)             |
| `turtle`     | YES       | Drawing engine (stdlib)          | built-in             |
| `tkinter`    | YES       | Window/canvas backend (stdlib)   | built-in             |
| `Pillow`     | OPTIONAL  | PNG export from EPS canvas       | `pip install Pillow` |

No external libraries are needed to run the compiler up through Phase 4 (IR).
Pillow is only needed for `--save-png`.
