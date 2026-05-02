"""
parser.py — Recursive Descent Parser for the RetroTurtle DSL.

Grammar (LL(1) compatible):
    program      → stmt_list EOF
    stmt_list    → stmt stmt_list | ε
    stmt         → command | loop
    command      → forward  NUMBER
                 | backward NUMBER
                 | left     NUMBER
                 | right    NUMBER
                 | pen_up
                 | pen_down
                 | color    (COLOR | IDENTIFIER)
                 | move     NUMBER NUMBER
    loop         → repeat NUMBER stmt_list end

Input  : list[Token]   (produced by the RetroTurtle Lexer)
Output : ProgramNode   (root of the AST)

Usage:
    parser = Parser(tokens, debug=True)
    ast    = parser.parse()
"""

from __future__ import annotations
from typing import Optional

# Local imports — Token types from the lexer package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.lexer.token import Token, TokenType
from src.parser.ast_nodes import (
    ASTNode, ProgramNode, CommandNode, LoopNode,
    NumberNode, IdentifierNode, ColorNode,
)


# ── Custom exception ───────────────────────────────────────────────────────────

class ParseError(Exception):
    """Raised when the parser encounters a syntax error."""

    def __init__(self, message: str, line: int) -> None:
        super().__init__(f"[Line {line}] ParseError: {message}")
        self.line = line


# ── Parser class ───────────────────────────────────────────────────────────────

class Parser:
    """
    Hand-written recursive descent parser for RetroTurtle.

    The parser consumes a flat token list and builds an AST.
    NEWLINE tokens are skipped transparently so grammar rules never
    have to mention them.
    """

    # Commands that take a single NUMBER argument
    _ONE_NUM_CMDS = frozenset({"forward", "backward", "left", "right"})

    def __init__(self, tokens: list[Token], debug: bool = False) -> None:
        self._tokens: list[Token] = tokens
        self._pos: int = 0
        self._debug: bool = debug

    # ── Public API ─────────────────────────────────────────────────────────────

    def parse(self) -> ProgramNode:
        """
        Entry point.  Parse the full token stream and return the root ProgramNode.
        """
        stmts = self._parse_stmt_list(top_level=True)
        self._expect(TokenType.EOF)
        root = ProgramNode(statements=stmts)

        if self._debug:
            print("\n[Parser Debug] AST:\n")
            print(root.pretty())
            print()

        return root

    # ── Grammar rules ──────────────────────────────────────────────────────────

    def _parse_stmt_list(self, top_level: bool = False) -> list[ASTNode]:
        """
        stmt_list → stmt stmt_list | ε

        Stops when it sees EOF (top-level) or the keyword 'end' (inside loop).
        """
        statements: list[ASTNode] = []

        while True:
            self._skip_newlines()
            tok = self._peek()

            # Stop conditions
            if tok.type == TokenType.EOF:
                break
            if tok.type == TokenType.KEYWORD and tok.value == "end":
                break  # 'end' is consumed by _parse_loop, not here

            stmt = self._parse_stmt()
            if stmt is not None:
                statements.append(stmt)

        return statements

    def _parse_stmt(self) -> Optional[ASTNode]:
        """
        stmt → command | loop
        """
        self._skip_newlines()
        tok = self._peek()

        if tok.type != TokenType.KEYWORD:
            raise ParseError(
                f"Expected a command keyword, got {tok.value!r}",
                tok.line,
            )

        if tok.value == "repeat":
            return self._parse_loop()
        else:
            return self._parse_command()

    def _parse_command(self) -> CommandNode:
        """
        command → forward  NUMBER
               | backward NUMBER
               | left     NUMBER
               | right    NUMBER
               | pen_up
               | pen_down
               | color    (COLOR | IDENTIFIER)
               | move     NUMBER NUMBER
        """
        kw_tok = self._expect(TokenType.KEYWORD)
        kw = kw_tok.value
        args: list[ASTNode] = []

        if kw in self._ONE_NUM_CMDS:
            # Requires exactly one NUMBER argument
            num_tok = self._expect_number(kw)
            args.append(NumberNode(value=int(num_tok.value), line=num_tok.line))

        elif kw in ("pen_up", "pen_down"):
            # No arguments
            pass

        elif kw == "color":
            # Requires a COLOR or IDENTIFIER argument
            arg_tok = self._peek()
            if arg_tok.type == TokenType.COLOR:
                self._advance()
                args.append(ColorNode(name=arg_tok.value, line=arg_tok.line))
            elif arg_tok.type == TokenType.IDENTIFIER:
                self._advance()
                args.append(IdentifierNode(name=arg_tok.value, line=arg_tok.line))
            else:
                raise ParseError(
                    f"'color' requires a color name or identifier, "
                    f"got {arg_tok.value!r}",
                    arg_tok.line,
                )

        elif kw == "move":
            # Requires exactly two NUMBER arguments
            num1 = self._expect_number("move (first argument)")
            num2 = self._expect_number("move (second argument)")
            args.append(NumberNode(value=int(num1.value), line=num1.line))
            args.append(NumberNode(value=int(num2.value), line=num2.line))

        else:
            raise ParseError(
                f"Unknown command keyword {kw!r}",
                kw_tok.line,
            )

        return CommandNode(keyword=kw, args=args, line=kw_tok.line)

    def _parse_loop(self) -> LoopNode:
        """
        loop → repeat NUMBER stmt_list end
        """
        repeat_tok = self._expect_keyword("repeat")

        # Expect the repeat count
        count_tok = self._expect_number("repeat")
        count_node = NumberNode(value=int(count_tok.value), line=count_tok.line)

        # Parse the body until we see 'end'
        body = self._parse_stmt_list()

        # Consume 'end'
        self._skip_newlines()
        end_tok = self._peek()
        if end_tok.type != TokenType.KEYWORD or end_tok.value != "end":
            raise ParseError(
                f"'repeat' block is not closed — expected 'end', "
                f"got {end_tok.value!r}",
                end_tok.line,
            )
        self._advance()  # consume 'end'

        return LoopNode(count=count_node, body=body, line=repeat_tok.line)

    # ── Token navigation helpers ───────────────────────────────────────────────

    def _peek(self) -> Token:
        """Return the current token without consuming it."""
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        """Consume and return the current token."""
        tok = self._tokens[self._pos]
        if self._pos < len(self._tokens) - 1:
            self._pos += 1
        return tok

    def _skip_newlines(self) -> None:
        """Consume any NEWLINE tokens silently."""
        while self._peek().type == TokenType.NEWLINE:
            self._advance()

    # ── Expect helpers ─────────────────────────────────────────────────────────

    def _expect(self, ttype: TokenType) -> Token:
        """
        Consume the next non-newline token and verify it is of the given type.
        Raises ParseError on mismatch.
        """
        self._skip_newlines()
        tok = self._advance()
        if tok.type != ttype:
            raise ParseError(
                f"Expected {ttype.name}, got {tok.type.name} ({tok.value!r})",
                tok.line,
            )
        return tok

    def _expect_keyword(self, keyword: str) -> Token:
        """Consume a specific KEYWORD token."""
        self._skip_newlines()
        tok = self._advance()
        if tok.type != TokenType.KEYWORD or tok.value != keyword:
            raise ParseError(
                f"Expected keyword '{keyword}', got {tok.value!r}",
                tok.line,
            )
        return tok

    def _expect_number(self, context: str) -> Token:
        """
        Consume the next token and verify it is a NUMBER.
        context is used only for the error message (e.g. 'forward').
        """
        self._skip_newlines()
        tok = self._advance()
        if tok.type != TokenType.NUMBER:
            raise ParseError(
                f"'{context}' requires a NUMBER argument, "
                f"got {tok.type.name} ({tok.value!r})",
                tok.line,
            )
        return tok
