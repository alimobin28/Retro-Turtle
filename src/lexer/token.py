"""
token.py — Token definitions for the RetroTurtle lexer.
Defines TokenType enum and the Token dataclass.
"""

from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """All valid token categories in the RetroTurtle DSL."""
    KEYWORD    = auto()   # forward, backward, left, right, repeat, end, pen_up, pen_down, color, move
    IDENTIFIER = auto()   # user-defined variable names (e.g., x, size)
    NUMBER     = auto()   # integer literals (e.g., 90, 100)
    COLOR      = auto()   # named colors (e.g., red, green, blue)
    NEWLINE    = auto()   # line separator \n
    EOF        = auto()   # end of file sentinel


@dataclass
class Token:
    """
    Represents a single lexical token.

    Attributes:
        type    : TokenType category
        value   : raw string value from source
        line    : 1-based line number in source file
        column  : 1-based column number where token starts
    """
    type:   TokenType
    value:  str
    line:   int
    column: int

    def __repr__(self) -> str:
        return f"<{self.type.name}, {self.value!r}, line={self.line}, col={self.column}>"

    def debug_str(self) -> str:
        """Format used in --debug output: <TYPE, VALUE, LINE>"""
        return f"<{self.type.name}, {self.value}, {self.line}>"