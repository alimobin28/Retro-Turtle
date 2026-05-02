"""
ast_nodes.py — Abstract Syntax Tree node definitions for RetroTurtle.

Every node in the AST is a plain dataclass.  The tree mirrors the grammar:

    program      → ProgramNode
    stmt_list    → list[ASTNode]
    command      → CommandNode
    loop         → LoopNode
"""

from __future__ import annotations
from dataclasses import dataclass, field


# ── Base ───────────────────────────────────────────────────────────────────────

class ASTNode:
    """Abstract base for all AST nodes."""

    def pretty(self, indent: int = 0) -> str:  # pragma: no cover
        """Return a human-readable tree string (overridden in subclasses)."""
        raise NotImplementedError


# ── Leaf / value nodes ─────────────────────────────────────────────────────────

@dataclass
class NumberNode(ASTNode):
    """An integer literal, e.g. 100."""
    value: int
    line: int

    def pretty(self, indent: int = 0) -> str:
        return "  " * indent + f"Number({self.value})"


@dataclass
class IdentifierNode(ASTNode):
    """An identifier used as a color argument, e.g. 'myColor'."""
    name: str
    line: int

    def pretty(self, indent: int = 0) -> str:
        return "  " * indent + f"Identifier({self.name})"


@dataclass
class ColorNode(ASTNode):
    """A named color literal, e.g. 'red'."""
    name: str
    line: int

    def pretty(self, indent: int = 0) -> str:
        return "  " * indent + f"Color({self.name})"


# ── Statement nodes ────────────────────────────────────────────────────────────

@dataclass
class CommandNode(ASTNode):
    """
    A single turtle command, e.g.:
        forward 100
        pen_up
        color red
        move 10 20
    """
    keyword: str                          # 'forward', 'left', 'color', etc.
    args: list[ASTNode] = field(default_factory=list)  # 0, 1, or 2 arg nodes
    line: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        if not self.args:
            return pad + f"Command({self.keyword})"
        arg_lines = "\n".join(a.pretty(indent + 1) for a in self.args)
        return pad + f"Command({self.keyword})\n{arg_lines}"


@dataclass
class LoopNode(ASTNode):
    """
    A repeat-block, e.g.:
        repeat 4
            forward 50
            right 90
        end
    """
    count: NumberNode                       # how many times to repeat
    body: list[ASTNode] = field(default_factory=list)  # statements inside
    line: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        header = pad + f"Loop(repeat={self.count.value})"
        body_lines = "\n".join(s.pretty(indent + 1) for s in self.body)
        return header + "\n" + body_lines


# ── Root node ──────────────────────────────────────────────────────────────────

@dataclass
class ProgramNode(ASTNode):
    """Root of the AST; holds the top-level statement list."""
    statements: list[ASTNode] = field(default_factory=list)

    def pretty(self, indent: int = 0) -> str:
        header = "Program"
        if not self.statements:
            return header + " (empty)"
        body = "\n".join(s.pretty(indent + 1) for s in self.statements)
        return header + "\n" + body
