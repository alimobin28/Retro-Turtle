# 🐢 RetroTurtle — Mini Compiler

A complete compiler for the **RetroTurtle** drawing DSL (`.rt` files), built in Python.  
Draws turtle-graphics shapes from a simple, readable scripting language.

---

## Project Structure

```
Retro-Turtle/
├── main.py                        # Entry point — full CLI
├── src/
│   ├── repl.py                    # Interactive REPL mode
│   ├── lexer/
│   │   ├── lexer.py               # Phase 1: Lexical Analysis
│   │   ├── token.py               # Token definitions
│   │   └── utils.py               # Keyword/color sets, char helpers
│   ├── parser/
│   │   ├── parser.py              # Phase 2: Recursive Descent Parser
│   │   └── ast_nodes.py           # AST node dataclasses
│   └── backend/
│       ├── semantic.py            # Phase 3: Semantic Analysis + Symbol Table
│       ├── ir_generator.py        # Phase 4: IR Generation (loop unrolling)
│       ├── optimizer.py           # Phase 5: Dead-Code Elim + Peephole Opt
│       └── executor.py            # Phase 6: Turtle Graphics Execution
├── tests/
│   ├── test1.rt                   # Valid: basic moves + loop
│   ├── test2.rt                   # Valid: hexagon star + triangle
│   ├── test3.rt                   # Valid: house shape
│   ├── test4_optimizer.rt         # Valid: optimizer stress test
│   ├── test5.rt                   # Valid: nested loops (flower)
│   ├── test_invalid.rt            # Error: bad lexer tokens
│   ├── test_missing_end.rt        # Error: missing 'end' keyword
│   └── test_semantic_error.rt     # Error: repeat count = 0
├── docs/
│   ├── grammar.md                 # CFG grammar + FIRST/FOLLOW sets
│   ├── token_spec.md              # Lexical token specification
│   ├── backend_design.md          # IR design + semantic rules doc
│   └── test_suite.md              # All tests with expected outputs
└── output/
    ├── program.ir                 # Generated IR (--save-ir)
    └── tokens.txt                 # Token list (--output)
```

---

## Compilation Pipeline

```
.rt source
    │
    ▼
[Phase 1] Lexer          → Token list
    │
    ▼
[Phase 2] Parser         → Abstract Syntax Tree (AST)
    │
    ▼
[Phase 3] Semantic       → Validated AST + Symbol Table
    │
    ▼
[Phase 4] IR Generator   → Flat IR instructions (loops unrolled)
    │
    ▼
[Phase 5] Optimizer      → Optimized IR (DCE + Peephole)
    │
    ▼
[Phase 6] Executor       → Turtle Graphics Window / PNG
```

---

## Usage

```bash
# Full pipeline (opens drawing window)
python main.py tests/test1.rt

# Compile to IR file (-o flag)
python main.py tests/test1.rt -o output/result.ir

# Show all intermediate representations
python main.py tests/test1.rt --debug

# Stop after IR generation (print IR listing)
python main.py tests/test1.rt --ir-only

# Stop after lexing (print token count)
python main.py tests/test1.rt --lex-only

# Save drawing as PNG (requires Pillow)
python main.py tests/test1.rt --save-png

# Save IR to output/program.ir
python main.py tests/test1.rt --save-ir

# Skip optimization phase
python main.py tests/test1.rt --no-opt

# Interactive REPL mode
python main.py --interactive
```

---

## Language Quick Reference

| Command         | Syntax                  | Description                          |
|-----------------|-------------------------|--------------------------------------|
| `forward`       | `forward N`             | Move forward N pixels                |
| `backward`      | `backward N`            | Move backward N pixels               |
| `left`          | `left N`                | Turn left N degrees                  |
| `right`         | `right N`               | Turn right N degrees                 |
| `pen_up`        | `pen_up`                | Lift pen (move without drawing)      |
| `pen_down`      | `pen_down`              | Lower pen (draw on move)             |
| `color`         | `color red`             | Set pen color                        |
| `move`          | `move X Y`              | Jump to coordinates (X, Y)           |
| `repeat`/`end`  | `repeat N ... end`      | Repeat block N times (nestable)      |
| `#`             | `# comment`             | Single-line comment                  |

**Supported colors:** `red green blue yellow orange purple black white cyan magenta pink brown`

---

## Optimization Examples

Run `python main.py tests/test4_optimizer.rt --ir-only` to see:

**Before optimization (10 instructions):**
```
PEN_DOWN
COLOR green     ← shadowed, never draws
COLOR blue
FORWARD 30      ← mergeable
FORWARD 30      ← mergeable
LEFT 45         ← cancels with RIGHT 45
RIGHT 45        ← cancels with LEFT 45
RIGHT 90
FORWARD 50
PEN_UP
```

**After optimization (6 instructions — 40% reduction):**
```
PEN_DOWN
COLOR blue
FORWARD 60
RIGHT 90
FORWARD 50
PEN_UP
```

---

## Error Messages

```bash
# Lexer error
[Line 5, Col 11] LexerError: Invalid number: digit sequence followed by 'a'

# Parser error
[Line 4] ParseError: 'repeat' block is not closed — expected 'end', got 'EOF'

# Semantic error
[Line 5] SemanticError: 'repeat' count must be a positive integer, got 0
```

---

## Dependencies

| Library      | Required? | Purpose                        | Install              |
|--------------|-----------|--------------------------------|----------------------|
| Python 3.10+ | YES       | Core language                  | (system)             |
| `turtle`     | YES       | Drawing engine (stdlib)        | built-in             |
| `tkinter`    | YES       | Window/canvas backend (stdlib) | built-in             |
| `Pillow`     | OPTIONAL  | PNG export from EPS canvas     | `pip install Pillow` |