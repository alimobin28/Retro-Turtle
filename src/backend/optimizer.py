"""
optimizer.py — Optimization Phase for RetroTurtle IR.

Implements two mandatory optimizations on the flat IR instruction list:

  1. Dead Code Elimination
     • Removes any FORWARD 0 / BACKWARD 0 instructions (zero-distance moves
       that have no visible effect).
     • Removes COLOR instructions that are immediately followed by another
       COLOR instruction without any drawing command in between (the first
       color is never actually used to draw anything).
     • Removes consecutive PEN_UP instructions (only the first is needed).

  2. Peephole Optimization
     • Merges consecutive FORWARD instructions into one
       (FORWARD 50 + FORWARD 50  →  FORWARD 100).
     • Merges consecutive BACKWARD instructions into one.
     • Merges consecutive LEFT or RIGHT turns into one
       (LEFT 90 + LEFT 90  →  LEFT 180).
     • Cancels opposite moves:
         FORWARD n + BACKWARD n  →  (removed, net zero movement)
         LEFT n   + RIGHT n      →  (removed, net zero rotation)

Bonus — Constant Folding:
     • All argument arithmetic is resolved at compile time during IR
       generation (loops are already unrolled).  This pass additionally
       folds any runtime-reducible patterns such as FORWARD 0 produced
       after merge cancellation.

Usage:
    opt = Optimizer(instructions, debug=True)
    optimized = opt.optimize()           # returns list[IRInstruction]
    opt.print_report()                   # prints before/after summary
"""

from __future__ import annotations
from typing import List
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backend.ir_generator import IRInstruction


class Optimizer:
    """
    Two-pass optimizer for RetroTurtle IR.

    Pass 1 — Dead Code Elimination:
        • Zero-distance FORWARD/BACKWARD removed.
        • Shadowed COLOR instructions removed.
        • Redundant PEN_UP sequences collapsed.

    Pass 2 — Peephole / Constant Folding:
        • Adjacent same-direction moves merged.
        • Opposite-direction pairs cancelled.
        • Zero-valued instructions produced by folding removed.
    """

    def __init__(self, instructions: List[IRInstruction], debug: bool = False) -> None:
        self._original     = instructions          # keep for reporting
        self._instructions = list(instructions)    # working copy
        self._debug        = debug
        self._eliminated   = 0                     # count of removed instrs
        self._folded       = 0                     # count of folded/merged instrs

    # ── Public API ─────────────────────────────────────────────────────────────

    def optimize(self) -> List[IRInstruction]:
        """Run all optimization passes and return the optimized IR list."""
        before = len(self._instructions)

        self._pass_dead_code_elimination()
        self._pass_peephole()

        after = len(self._instructions)
        self._eliminated = before - after

        if self._debug:
            self._print_debug()

        return self._instructions

    def print_report(self) -> None:
        """Print a human-readable optimization summary."""
        before = len(self._original)
        after  = len(self._instructions)
        print("\n[Optimizer Report]")
        print(f"  Instructions before : {before}")
        print(f"  Instructions after  : {after}")
        print(f"  Eliminated          : {before - after}")
        print(f"  Reduction           : {(before - after) / before * 100:.1f}%"
              if before else "  Reduction           : N/A")

    # ── Pass 1: Dead Code Elimination ─────────────────────────────────────────

    def _pass_dead_code_elimination(self) -> None:
        """
        Remove provably useless instructions:
          • FORWARD 0 / BACKWARD 0   (no movement)
          • COLOR shadowed by next COLOR before any draw
          • Consecutive duplicate PEN_UP
        """
        result: List[IRInstruction] = []
        drawing_ops = {"FORWARD", "BACKWARD", "LEFT", "RIGHT", "MOVE"}

        i = 0
        instrs = self._instructions
        while i < len(instrs):
            instr = instrs[i]

            # -- Zero-distance movement → dead
            if instr.opcode in ("FORWARD", "BACKWARD") and instr.args and instr.args[0] == 0:
                if self._debug:
                    print(f"  [DCE] Removed zero-distance: {instr}")
                i += 1
                continue

            # -- COLOR immediately followed by another COLOR (no draw between) → dead
            if instr.opcode == "COLOR":
                j = i + 1
                shadowed = False
                while j < len(instrs):
                    if instrs[j].opcode == "COLOR":
                        shadowed = True
                        break
                    if instrs[j].opcode in drawing_ops:
                        break
                    j += 1
                if shadowed:
                    if self._debug:
                        print(f"  [DCE] Removed shadowed color: {instr}")
                    i += 1
                    continue

            # -- Consecutive PEN_UP (only keep first)
            if instr.opcode == "PEN_UP" and result and result[-1].opcode == "PEN_UP":
                if self._debug:
                    print(f"  [DCE] Removed redundant PEN_UP at line {instr.line}")
                i += 1
                continue

            result.append(instr)
            i += 1

        self._instructions = result

    # ── Pass 2: Peephole / Constant Folding ───────────────────────────────────

    def _pass_peephole(self) -> None:
        """
        Merge adjacent compatible instructions:
          • FORWARD n + FORWARD m  →  FORWARD (n+m)
          • BACKWARD n + BACKWARD m  →  BACKWARD (n+m)
          • LEFT n + LEFT m  →  LEFT (n+m)
          • RIGHT n + RIGHT m  →  RIGHT (n+m)
          • FORWARD n + BACKWARD n  →  (cancel out)
          • LEFT n + RIGHT n  →  (cancel out)
        Also removes any zero-value results produced by cancellation.
        """
        # We run multiple sub-passes until stable (fixed-point)
        changed = True
        while changed:
            changed = False
            result: List[IRInstruction] = []
            instrs = self._instructions
            i = 0
            while i < len(instrs):
                cur  = instrs[i]
                nxt  = instrs[i + 1] if i + 1 < len(instrs) else None

                if nxt is None:
                    result.append(cur)
                    i += 1
                    continue

                # ── Merge same-direction
                if (cur.opcode == nxt.opcode
                        and cur.opcode in ("FORWARD", "BACKWARD", "LEFT", "RIGHT")
                        and cur.args and nxt.args):
                    merged_val = cur.args[0] + nxt.args[0]
                    merged = IRInstruction(cur.opcode, [merged_val], cur.line)
                    if self._debug:
                        print(f"  [Peephole] Merged: {cur} + {nxt}  →  {merged}")
                    result.append(merged)
                    self._folded += 1
                    changed = True
                    i += 2
                    continue

                # ── Cancel opposite pairs
                if (cur.opcode == "FORWARD" and nxt.opcode == "BACKWARD"
                        and cur.args and nxt.args and cur.args[0] == nxt.args[0]):
                    if self._debug:
                        print(f"  [Peephole] Cancelled: {cur} + {nxt}  →  (removed)")
                    self._folded += 1
                    changed = True
                    i += 2
                    continue

                if (cur.opcode == "BACKWARD" and nxt.opcode == "FORWARD"
                        and cur.args and nxt.args and cur.args[0] == nxt.args[0]):
                    if self._debug:
                        print(f"  [Peephole] Cancelled: {cur} + {nxt}  →  (removed)")
                    self._folded += 1
                    changed = True
                    i += 2
                    continue

                if (cur.opcode == "LEFT" and nxt.opcode == "RIGHT"
                        and cur.args and nxt.args and cur.args[0] == nxt.args[0]):
                    if self._debug:
                        print(f"  [Peephole] Cancelled: {cur} + {nxt}  →  (removed)")
                    self._folded += 1
                    changed = True
                    i += 2
                    continue

                if (cur.opcode == "RIGHT" and nxt.opcode == "LEFT"
                        and cur.args and nxt.args and cur.args[0] == nxt.args[0]):
                    if self._debug:
                        print(f"  [Peephole] Cancelled: {cur} + {nxt}  →  (removed)")
                    self._folded += 1
                    changed = True
                    i += 2
                    continue

                result.append(cur)
                i += 1

            self._instructions = result

        # Final pass: remove any zero-value instructions produced by folding
        self._instructions = [
            instr for instr in self._instructions
            if not (instr.opcode in ("FORWARD", "BACKWARD", "LEFT", "RIGHT")
                    and instr.args and instr.args[0] == 0)
        ]

    # ── Debug output ───────────────────────────────────────────────────────────

    def _print_debug(self) -> None:
        print("\n[Optimizer Debug] Optimized IR:")
        print(f"  {'#':<5} {'Instruction':<25} {'Source Line'}")
        print(f"  {'-'*5} {'-'*25} {'-'*11}")
        for i, instr in enumerate(self._instructions, start=1):
            print(f"  {i:<5} {str(instr):<25} line {instr.line}")
        print()