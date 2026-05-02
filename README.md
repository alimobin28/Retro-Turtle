# 🐢 RetroTurtle — DSL Lexer

A clean, modular lexer implementing the **Lexical Analysis** phase of a mini-compiler for the RetroTurtle drawing DSL.

---

## Project Structure

```
RetroTurtle/
│
├── src/
│   └── lexer/
│       ├── lexer.py      # Core Lexer class + LexerError
│       ├── token.py      # TokenType enum + Token dataclass
│       └── utils.py      # Keyword/color sets + char-class helpers
│
├── tests/
│   ├── test1.rt          # Valid sample program
│   └── test_invalid.rt   # Program with intentional errors
│
├── docs/
│   └── token_spec.md     # Token definition table + DFA sketch
│
├── output/
│   └── tokens.txt        # Generated token list (via --output flag)
│
├── main.py               # Entry point
└── README.md
```

---

## Usage

```bash
# Normal mode (lexes silently, prints summary)
python main.py tests/test1.rt

# Debug mode — prints every token as <TYPE, VALUE, LINE>
python main.py tests/test1.rt --debug

# Save tokens to output/tokens.txt
python main.py tests/test1.rt --output

# Combine flags
python main.py tests/test1.rt --debug --output
```

---

## Token Types

| Type         | Example              |
|--------------|----------------------|
| `KEYWORD`    | `forward`, `repeat`  |
| `IDENTIFIER` | `x`, `size`          |
| `NUMBER`     | `90`, `100`          |
| `COLOR`      | `red`, `green`       |
| `NEWLINE`    | `\n`                 |
| `EOF`        | *(end of file)*      |

See [`docs/token_spec.md`](docs/token_spec.md) for the full specification and DFA.

---

## Sample Programs

### Valid (`tests/test1.rt`)

```
pen_down
color green
forward 100
left 90
repeat 4
    forward 50
    right 90
end
move 10 20
```

### Invalid (`tests/test_invalid.rt`)

```
forward 99abc   # ← invalid number
@ invalid_token  # ← unrecognised character
```

---

## Error Output Example

```
[Line 7, Col 11] LexerError: Invalid number: digit sequence followed by 'a'
```

---

## Language Rules

- **Case-insensitive keywords** — `FoRwArD` → `<KEYWORD, forward>`
- **Comments** — `#` to end-of-line are ignored
- **Whitespace** — spaces and tabs between tokens are skipped
- **Integers only** — floats and alphanumeric digit strings are rejected
- **Blocks** — `repeat N ... end` defines a loop body

---

## Running Tests

```bash
# Quick smoke test for both files
python main.py tests/test1.rt --debug
python main.py tests/test_invalid.rt --debug
```