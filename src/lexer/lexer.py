"""
lexer.py — Core lexer for the RetroTurtle DSL.

Responsibilities:
  • Read source text character by character.
  • Emit a list of Token objects.
  • Raise LexerError with line + column on invalid input.
  • Optionally print debug output when debug=True.
"""

from .token import Token, TokenType
from .utils import (
    KEYWORDS, COLORS,
    is_alpha_or_underscore, is_alnum_or_underscore,
    is_digit, is_whitespace_not_newline,
)


# ── Custom exception ───────────────────────────────────────────────────────────

class LexerError(Exception):
    """Raised when the lexer encounters an unrecognised character sequence."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(f"[Line {line}, Col {column}] LexerError: {message}")
        self.line   = line
        self.column = column


# ── Lexer class ────────────────────────────────────────────────────────────────

class Lexer:
    """
    Hand-written, single-pass lexer for RetroTurtle (.rt) files.

    Usage:
        lexer  = Lexer(source_text, debug=True)
        tokens = lexer.tokenize()
    """

    def __init__(self, source: str, debug: bool = False) -> None:
        self._source  = source          # full source text
        self._pos     = 0               # current char index
        self._line    = 1               # current line   (1-based)
        self._col     = 1               # current column (1-based)
        self._debug   = debug
        self._tokens: list[Token] = []

    # ── Public API ─────────────────────────────────────────────────────────────

    def tokenize(self) -> list[Token]:
        """
        Scan the entire source and return the complete token list.
        Always ends with an EOF token.
        """
        while not self._at_end():
            self._scan_token()

        self._emit(TokenType.EOF, "EOF")
        return self._tokens

    # ── Internal scanning ──────────────────────────────────────────────────────

    def _scan_token(self) -> None:
        """Dispatch the next character to the appropriate scanner."""
        ch = self._current_char()

        # Skip horizontal whitespace
        if is_whitespace_not_newline(ch):
            self._advance()
            return

        # Newline → emit NEWLINE token
        if ch == "\n":
            self._emit(TokenType.NEWLINE, "\\n")
            self._advance()
            self._line += 1
            self._col   = 1
            return

        # Skip carriage return (Windows line endings)
        if ch == "\r":
            self._advance()
            return

        # Skip single-line comments starting with '#'
        if ch == "#":
            self._skip_comment()
            return

        # Word token: keyword / identifier / color
        if is_alpha_or_underscore(ch):
            self._scan_word()
            return

        # Number token
        if is_digit(ch):
            self._scan_number()
            return

        # Unrecognised character
        raise LexerError(
            f"Unexpected character {ch!r}",
            self._line,
            self._col,
        )

    def _scan_word(self) -> None:
        """Scan a contiguous word and classify as KEYWORD, COLOR, or IDENTIFIER."""
        start_col = self._col
        word_chars: list[str] = []

        while not self._at_end() and is_alnum_or_underscore(self._current_char()):
            word_chars.append(self._current_char())
            self._advance()

        raw   = "".join(word_chars)
        lower = raw.lower()          # case-insensitive matching

        if lower in KEYWORDS:
            self._emit_at(TokenType.KEYWORD, lower, start_col)
        elif lower in COLORS:
            self._emit_at(TokenType.COLOR, lower, start_col)
        else:
            self._emit_at(TokenType.IDENTIFIER, raw, start_col)

    def _scan_number(self) -> None:
        """Scan an integer literal. Floats / trailing letters are invalid."""
        start_col = self._col
        digits: list[str] = []

        while not self._at_end() and is_digit(self._current_char()):
            digits.append(self._current_char())
            self._advance()

        # Guard: a digit string immediately followed by a letter is invalid
        if not self._at_end() and is_alpha_or_underscore(self._current_char()):
            bad_char = self._current_char()
            raise LexerError(
                f"Invalid number: digit sequence followed by {bad_char!r}",
                self._line,
                self._col,
            )

        self._emit_at(TokenType.NUMBER, "".join(digits), start_col)

    def _skip_comment(self) -> None:
        """Consume everything from '#' to end of line."""
        while not self._at_end() and self._current_char() != "\n":
            self._advance()

    # ── Emit helpers ───────────────────────────────────────────────────────────

    def _emit(self, ttype: TokenType, value: str) -> None:
        """Emit a token at the current position."""
        self._emit_at(ttype, value, self._col)

    def _emit_at(self, ttype: TokenType, value: str, col: int) -> None:
        """Emit a token with an explicitly provided column (for multi-char tokens)."""
        tok = Token(ttype, value, self._line, col)
        self._tokens.append(tok)
        if self._debug:
            print(tok.debug_str())

    # ── Character navigation ───────────────────────────────────────────────────

    def _current_char(self) -> str:
        return self._source[self._pos]

    def _advance(self) -> str:
        """Consume and return the current character, advancing position."""
        ch         = self._source[self._pos]
        self._pos += 1
        self._col += 1
        return ch

    def _at_end(self) -> bool:
        return self._pos >= len(self._source)