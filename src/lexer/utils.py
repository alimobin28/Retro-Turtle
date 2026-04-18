"""
utils.py — Helper constants and utility functions for the RetroTurtle lexer.
"""

# ── Known token sets ───────────────────────────────────────────────────────────

KEYWORDS: frozenset[str] = frozenset({
    "forward", "backward", "left", "right",
    "repeat", "end", "pen_up", "pen_down",
    "color", "move",
})

COLORS: frozenset[str] = frozenset({
    "red", "green", "blue", "yellow",
    "orange", "purple", "black", "white",
    "cyan", "magenta", "pink", "brown",
})

# ── Character-class helpers ────────────────────────────────────────────────────

def is_alpha_or_underscore(ch: str) -> bool:
    """True for letters and underscores (valid identifier starters)."""
    return ch.isalpha() or ch == "_"


def is_alnum_or_underscore(ch: str) -> bool:
    """True for letters, digits, and underscores (valid identifier continuations)."""
    return ch.isalnum() or ch == "_"


def is_digit(ch: str) -> bool:
    return ch.isdigit()


def is_whitespace_not_newline(ch: str) -> bool:
    """True for spaces and tabs — NOT for newline."""
    return ch in (" ", "\t")