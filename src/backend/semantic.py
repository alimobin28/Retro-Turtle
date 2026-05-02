"""
semantic.py — Semantic Analyzer for the RetroTurtle DSL.

Responsibilities:
  1. Walk the AST produced by the parser.
  2. Validate every command has the correct number / type of arguments.
  3. Maintain a Symbol Table that records every identifier encountered.
  4. Raise SemanticError with a clear line number on any violation.

Symbol Table layout (dict):
    {
        "myColor": {"type": "color_var", "first_seen": 3},
        ...
    }

Usage:
    analyzer = SemanticAnalyzer(ast, debug=True)
    analyzer.analyze()          # raises SemanticError on failure
    table = analyzer.symbol_table
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.parser.ast_nodes import (
    ASTNode, ProgramNode, CommandNode, LoopNode,
    NumberNode, IdentifierNode, ColorNode,
)


# ── Exception ──────────────────────────────────────────────────────────────────

class SemanticError(Exception):
    """Raised when a semantic rule is violated."""
    def __init__(self, message: str, line: int) -> None:
        super().__init__(f"[Line {line}] SemanticError: {message}")
        self.line = line


# ── Command argument specifications ───────────────────────────────────────────
#
#   Maps each keyword to a tuple of expected argument types.
#   Types used:
#       "NUMBER"     — must be a NumberNode
#       "COLOR_ARG"  — must be a ColorNode or IdentifierNode

_CMD_SPEC: dict[str, tuple[str, ...]] = {
    "forward":  ("NUMBER",),
    "backward": ("NUMBER",),
    "left":     ("NUMBER",),
    "right":    ("NUMBER",),
    "pen_up":   (),
    "pen_down": (),
    "color":    ("COLOR_ARG",),
    "move":     ("NUMBER", "NUMBER"),
}


# ── SemanticAnalyzer ──────────────────────────────────────────────────────────

class SemanticAnalyzer:
    """
    Walks the full AST, validates semantics, and builds a symbol table.

    After a successful analyze() call:
        self.symbol_table  →  dict of identifiers found in the program
    """

    def __init__(self, root: ProgramNode, debug: bool = False) -> None:
        self._root   = root
        self._debug  = debug
        self.symbol_table: dict[str, dict] = {}

    # ── Public API ─────────────────────────────────────────────────────────────

    def analyze(self) -> None:
        """
        Run semantic analysis over the entire AST.
        Raises SemanticError on the first violation found.
        """
        self._visit_program(self._root)

        if self._debug:
            self._print_symbol_table()

    # ── Visitor methods ────────────────────────────────────────────────────────

    def _visit_program(self, node: ProgramNode) -> None:
        for stmt in node.statements:
            self._visit_stmt(stmt)

    def _visit_stmt(self, node: ASTNode) -> None:
        if isinstance(node, CommandNode):
            self._visit_command(node)
        elif isinstance(node, LoopNode):
            self._visit_loop(node)
        else:
            raise SemanticError(
                f"Unknown AST node type: {type(node).__name__}",
                getattr(node, "line", 0),
            )

    def _visit_command(self, node: CommandNode) -> None:
        kw   = node.keyword
        args = node.args
        line = node.line

        # 1. Check keyword is known
        if kw not in _CMD_SPEC:
            raise SemanticError(f"Unknown command '{kw}'", line)

        expected = _CMD_SPEC[kw]

        # 2. Check argument count
        if len(args) != len(expected):
            raise SemanticError(
                f"'{kw}' expects {len(expected)} argument(s), "
                f"got {len(args)}",
                line,
            )

        # 3. Check argument types
        for i, (arg, exp_type) in enumerate(zip(args, expected), start=1):
            if exp_type == "NUMBER":
                if not isinstance(arg, NumberNode):
                    raise SemanticError(
                        f"'{kw}' argument {i} must be a NUMBER, "
                        f"got {type(arg).__name__}",
                        line,
                    )
                if arg.value < 0:
                    raise SemanticError(
                        f"'{kw}' argument {i} must be non-negative, "
                        f"got {arg.value}",
                        line,
                    )
            elif exp_type == "COLOR_ARG":
                if isinstance(arg, IdentifierNode):
                    # Register identifier in symbol table
                    self._register_identifier(arg.name, "color_var", line)
                elif not isinstance(arg, ColorNode):
                    raise SemanticError(
                        f"'color' requires a color name or variable, "
                        f"got {type(arg).__name__}",
                        line,
                    )

    def _visit_loop(self, node: LoopNode) -> None:
        # Validate repeat count
        if node.count.value <= 0:
            raise SemanticError(
                f"'repeat' count must be a positive integer, "
                f"got {node.count.value}",
                node.line,
            )

        # Validate loop body (recursively)
        for stmt in node.body:
            self._visit_stmt(stmt)

    # ── Symbol table helpers ───────────────────────────────────────────────────

    def _register_identifier(self, name: str, kind: str, line: int) -> None:
        """Add an identifier to the symbol table if not already present."""
        if name not in self.symbol_table:
            self.symbol_table[name] = {"type": kind, "first_seen": line}

    def _print_symbol_table(self) -> None:
        print("\n[Semantic Debug] Symbol Table:")
        if not self.symbol_table:
            print("  (empty — no user-defined identifiers used)")
            return
        print(f"  {'Name':<20} {'Type':<15} {'First Seen (line)'}")
        print(f"  {'-'*20} {'-'*15} {'-'*17}")
        for name, info in self.symbol_table.items():
            print(f"  {name:<20} {info['type']:<15} {info['first_seen']}")
        print()
