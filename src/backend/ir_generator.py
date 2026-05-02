"""
ir_generator.py — Intermediate Representation (IR) Generator for RetroTurtle.

Converts a validated AST into a flat list of IR instructions.

IR Instruction format:
    IRInstruction(opcode, args, line)

Opcodes:
    PEN_DOWN
    PEN_UP
    FORWARD   <n>
    BACKWARD  <n>
    LEFT      <n>
    RIGHT     <n>
    COLOR     <name>
    MOVE      <x> <y>

Loops are fully unrolled at IR generation time — the IR has no control flow,
only a straight sequence of drawing commands.  This makes the execution engine
trivially simple.

Usage:
    gen = IRGenerator(ast, debug=True)
    instructions = gen.generate()   # list[IRInstruction]
"""

from __future__ import annotations
from dataclasses import dataclass, field
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.parser.ast_nodes import (
    ASTNode, ProgramNode, CommandNode, LoopNode,
    NumberNode, IdentifierNode, ColorNode,
)


# ── IR Instruction ─────────────────────────────────────────────────────────────

@dataclass
class IRInstruction:
    """
    One flat IR instruction.

    Examples:
        IRInstruction("FORWARD",  [100], 3)
        IRInstruction("COLOR",    ["red"], 4)
        IRInstruction("PEN_DOWN", [], 1)
    """
    opcode: str
    args:   list  = field(default_factory=list)
    line:   int   = 0

    def __str__(self) -> str:
        if self.args:
            return f"{self.opcode} {' '.join(str(a) for a in self.args)}"
        return self.opcode


# ── IRGenerator ────────────────────────────────────────────────────────────────

class IRGenerator:
    """
    Traverses the AST depth-first and emits a flat list of IRInstructions.
    Repeat-loops are unrolled at this stage.
    """

    # Maps AST CommandNode keywords → IR opcodes
    _OPCODE_MAP: dict[str, str] = {
        "forward":  "FORWARD",
        "backward": "BACKWARD",
        "left":     "LEFT",
        "right":    "RIGHT",
        "pen_up":   "PEN_UP",
        "pen_down": "PEN_DOWN",
        "color":    "COLOR",
        "move":     "MOVE",
    }

    def __init__(self, root: ProgramNode, debug: bool = False) -> None:
        self._root   = root
        self._debug  = debug
        self._instructions: list[IRInstruction] = []

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(self) -> list[IRInstruction]:
        """
        Traverse the AST and return the complete IR instruction list.
        """
        self._visit_stmts(self._root.statements)

        if self._debug:
            self._print_ir()

        return self._instructions

    # ── Visitor methods ────────────────────────────────────────────────────────

    def _visit_stmts(self, stmts: list[ASTNode]) -> None:
        for node in stmts:
            if isinstance(node, CommandNode):
                self._visit_command(node)
            elif isinstance(node, LoopNode):
                self._visit_loop(node)

    def _visit_command(self, node: CommandNode) -> None:
        """Translate one CommandNode into one IRInstruction."""
        opcode = self._OPCODE_MAP[node.keyword]
        args   = []

        for arg in node.args:
            if isinstance(arg, NumberNode):
                args.append(arg.value)
            elif isinstance(arg, ColorNode):
                args.append(arg.name)
            elif isinstance(arg, IdentifierNode):
                # Identifiers used as color variables — pass name through
                args.append(arg.name)

        instr = IRInstruction(opcode=opcode, args=args, line=node.line)
        self._instructions.append(instr)

    def _visit_loop(self, node: LoopNode) -> None:
        """Unroll a repeat-loop by visiting its body N times."""
        count = node.count.value
        for _ in range(count):
            self._visit_stmts(node.body)

    # ── Debug output ───────────────────────────────────────────────────────────

    def _print_ir(self) -> None:
        print("\n[IR Debug] Generated IR Instructions:")
        print(f"  {'#':<5} {'Instruction':<25} {'Source Line'}")
        print(f"  {'-'*5} {'-'*25} {'-'*11}")
        for i, instr in enumerate(self._instructions, start=1):
            print(f"  {i:<5} {str(instr):<25} line {instr.line}")
        print(f"\n  Total: {len(self._instructions)} instruction(s)\n")

    # ── Utility ────────────────────────────────────────────────────────────────

    def ir_to_text(self) -> str:
        """Return the IR as a plain text string (one instruction per line)."""
        return "\n".join(str(i) for i in self._instructions)
