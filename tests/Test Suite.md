# RetroTurtle — Test Suite with Expected Outputs

All test files live in `tests/`. Run with:

```bash
python main.py tests/<file>.rt --ir-only
python main.py tests/<file>.rt --debug
```

---

## Test 1 — `test1.rt` (Valid Program)

**Description:** Basic turtle drawing — forward moves, turns, a loop, color changes, pen control.

**Input:**
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

**Expected IR output (optimized):**
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

**Expected console:**
```
Phase 1 — Lexical Analysis
  -> 34 token(s) produced.
Phase 2 — Syntax Analysis (Parser)
  -> AST built. 8 top-level statement(s).
Phase 3 — Semantic Analysis
  -> Semantic check passed. 0 identifier(s) in symbol table.
Phase 4 — IR Generation
  -> 18 IR instruction(s) generated.
Phase 5 — Optimization
  Instructions before : 18
  Instructions after  : 18
  Eliminated          : 0
```

---

## Test 2 — `test2.rt` (Spiral/Star Pattern)

**Description:** Hexagonal star in blue, then triangle in magenta.

**Input:**
```
pen_down
color blue
repeat 6
    forward 80
    right 60
end
move 0 0
color magenta
repeat 3
    forward 60
    left 120
end
pen_up
```

**Expected IR output (optimized):**
```
PEN_DOWN
COLOR blue
FORWARD 80
RIGHT 60
FORWARD 80
RIGHT 60
FORWARD 80
RIGHT 60
FORWARD 80
RIGHT 60
FORWARD 80
RIGHT 60
FORWARD 80
RIGHT 60
MOVE 0 0
COLOR magenta
FORWARD 60
LEFT 120
FORWARD 60
LEFT 120
FORWARD 60
LEFT 120
PEN_UP
```

**Expected console:**
```
Phase 5 — Optimization
  Instructions before : 22
  Instructions after  : 22
  Eliminated          : 0
```

---

## Test 3 — `test3.rt` (House Shape)

**Description:** Square base in orange, triangular roof in red.

**Input:**
```
pen_down
color orange
repeat 4
    forward 80
    right 90
end
pen_up
move 0 80
pen_down
color red
forward 80
right 120
forward 80
right 120
forward 80
pen_up
```

**Expected IR output (optimized):**
```
PEN_DOWN
COLOR orange
FORWARD 80
RIGHT 90
FORWARD 80
RIGHT 90
FORWARD 80
RIGHT 90
FORWARD 80
RIGHT 90
PEN_UP
MOVE 0 80
PEN_DOWN
COLOR red
FORWARD 80
RIGHT 120
FORWARD 80
RIGHT 120
FORWARD 80
PEN_UP
```

**Expected console:**
```
Phase 5 — Optimization
  Instructions before : 20
  Instructions after  : 20
  Eliminated          : 0
```

---

## Test 4 — `test4_optimizer.rt` (Optimizer Stress Test)

**Description:** Deliberately triggers dead code elimination and peephole optimizations.

**Input:**
```
pen_down
color green
color blue
forward 30
forward 30
left 45
right 45
right 90
forward 50
pen_up
```

**Expected IR before optimization (10 instructions):**
```
PEN_DOWN
COLOR green
COLOR blue
FORWARD 30
FORWARD 30
LEFT 45
RIGHT 45
RIGHT 90
FORWARD 50
PEN_UP
```

**Expected IR after optimization (6 instructions):**
```
PEN_DOWN
COLOR blue
FORWARD 60
RIGHT 90
FORWARD 50
PEN_UP
```

**Optimizations applied:**
| Optimization | Type | Before | After |
|---|---|---|---|
| `COLOR green` removed (shadowed by `COLOR blue`) | Dead Code Elimination | 2 COLOR instrs | 1 COLOR instr |
| `FORWARD 30 + FORWARD 30` merged | Peephole / Constant Folding | 2 instrs | `FORWARD 60` |
| `LEFT 45 + RIGHT 45` cancelled | Peephole | 2 instrs | removed |

**Expected console:**
```
Phase 5 — Optimization
  Instructions before : 10
  Instructions after  : 6
  Eliminated          : 4
  Reduction           : 40.0%
```

---

## Test 5 — `test5.rt` (Nested Loops / Flower Pattern)

**Description:** 4 triangle petals arranged in a cross, drawn in cyan.

**Input:**
```
pen_down
color cyan
repeat 4
    repeat 3
        forward 40
        left 120
    end
    right 90
end
pen_up
```

**Expected IR output (optimized, loops unrolled):**
```
PEN_DOWN
COLOR cyan
FORWARD 40
LEFT 120
FORWARD 40
LEFT 120
FORWARD 40
LEFT 120
RIGHT 90
FORWARD 40
LEFT 120
FORWARD 40
LEFT 120
FORWARD 40
LEFT 120
RIGHT 90
FORWARD 40
LEFT 120
FORWARD 40
LEFT 120
FORWARD 40
LEFT 120
RIGHT 90
FORWARD 40
LEFT 120
FORWARD 40
LEFT 120
FORWARD 40
LEFT 120
RIGHT 90
PEN_UP
```

**Expected console:**
```
Phase 4 — IR Generation
  -> 30 IR instruction(s) generated.
Phase 5 — Optimization
  Instructions before : 30
  Instructions after  : 30
  Eliminated          : 0
```

---

## Error Test A — `test_invalid.rt` (Lexer Error)

**Description:** Tests that the lexer catches an invalid character (`@`) and a bad number (`99abc`).

**Expected error output:**
```
[Line 5, Col 11] LexerError: Invalid number: digit sequence followed by 'a'
```
*(Compiler stops at Phase 1; `@` on line 9 is never reached.)*

---

## Error Test B — `test_missing_end.rt` (Parser Error)

**Description:** A `repeat` block missing its closing `end`.

**Expected error output:**
```
[Line 5] ParseError: 'repeat' block is not closed — expected 'end', got 'KEYWORD' ('pen_down')
```

---

## Error Test C — `test_semantic_error.rt` (Semantic Error)

**Description:** `repeat 0` — repeat count must be positive.

**Expected error output:**
```
[Line 5] SemanticError: 'repeat' count must be a positive integer, got 0
```