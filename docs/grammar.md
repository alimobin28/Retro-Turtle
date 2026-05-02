# RetroTurtle — Grammar Specification

## Context-Free Grammar (CFG)

```
program      → stmt_list EOF

stmt_list    → stmt stmt_list
             | ε

stmt         → command
             | loop

command      → forward  NUMBER
             | backward NUMBER
             | left     NUMBER
             | right    NUMBER
             | pen_up
             | pen_down
             | color    (COLOR | IDENTIFIER)
             | move     NUMBER NUMBER

loop         → repeat NUMBER stmt_list end
```

## Notes

- **Keywords** are case-insensitive (`FoRwArD` = `forward`).
- **NEWLINE** tokens are ignored by the parser; they exist only in the token stream for potential future use.
- The grammar is **LL(1)** — each rule can be selected by looking at the next keyword alone, with no ambiguity.
- `color` accepts both a named `COLOR` token (e.g. `red`) and a user-defined `IDENTIFIER` (e.g. `myColor`).
- `repeat` blocks must be closed with `end`. A missing `end` raises a `ParseError`.

## FIRST / FOLLOW Sets (Summary)

| Non-terminal | FIRST set                                                              |
|--------------|------------------------------------------------------------------------|
| stmt_list    | {forward, backward, left, right, pen_up, pen_down, color, move, repeat, ε} |
| stmt         | {forward, backward, left, right, pen_up, pen_down, color, move, repeat} |
| command      | {forward, backward, left, right, pen_up, pen_down, color, move}        |
| loop         | {repeat}                                                               |

## Parse Tree Example

Input:
```
repeat 2
    forward 50
    right 90
end
```

Parse Tree:
```
Program
  Loop(repeat=2)
    Command(forward)
      Number(50)
    Command(right)
      Number(90)
```
