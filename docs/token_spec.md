# RetroTurtle Token Specification

## 1. Keywords

| Token Type | Pattern  | Example  |
| ---------- | -------- | -------- |
| KEYWORD    | forward  | forward  |
| KEYWORD    | backward | backward |
| KEYWORD    | left     | left     |
| KEYWORD    | right    | right    |
| KEYWORD    | repeat   | repeat   |
| KEYWORD    | end      | end      |
| KEYWORD    | pen_up   | pen_up   |
| KEYWORD    | pen_down | pen_down |
| KEYWORD    | color    | color    |
| KEYWORD    | move     | move     |

---

## 2. Identifiers

| Token Type | Pattern              | Example         |
| ---------- | -------------------- | --------------- |
| IDENTIFIER | [a-zA-Z][a-zA-Z0-9]* | size, x, length |

Description:
Identifiers represent variable names.

---

## 3. Numbers

| Token Type | Pattern | Example |
| ---------- | ------- | ------- |
| NUMBER     | [0-9]+  | 100, 50 |

Description:
Only integers are supported.

---

## 4. Colors

| Token Type | Pattern          | Example |
| ---------- | ---------------- | ------- |
| COLOR      | green, red, blue | red     |

Description:
Used with color command.

---

## 5. Whitespace

| Token Type | Pattern               | Example |
| ---------- | --------------------- | ------- |
| WHITESPACE | spaces, tabs, newline | " "     |

Description:
Ignored by lexer.

---

## 6. Error Tokens

| Token Type | Example       |
| ---------- | ------------- |
| INVALID    | forwrd, 12abc |

Description:
Invalid or unrecognized tokens.
