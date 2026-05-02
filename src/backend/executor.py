"""
executor.py — Execution Engine for RetroTurtle IR.

Reads a list of IRInstruction objects and drives Python's `turtle` module
to draw the corresponding shapes on screen.

Supported opcodes (all produced by ir_generator.py):
    PEN_DOWN
    PEN_UP
    FORWARD   <n>
    BACKWARD  <n>
    LEFT      <n>
    RIGHT     <n>
    COLOR     <name>
    MOVE      <x> <y>

Optional:
    • Save the final canvas as a PNG (requires the 'Pillow' library;
      a graceful warning is printed if Pillow is missing).

Usage:
    executor = Executor(instructions, debug=True, save_png="output/drawing.png")
    executor.run()
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backend.ir_generator import IRInstruction


# ── Named-color safety map ─────────────────────────────────────────────────────
#
# Python turtle accepts most CSS color names directly.
# We keep a whitelist of the ones RetroTurtle officially supports so that
# unknown identifier names produce a clear error instead of a cryptic crash.

_VALID_COLORS: frozenset[str] = frozenset({
    "red", "green", "blue", "yellow", "orange", "purple",
    "black", "white", "cyan", "magenta", "pink", "brown",
})


# ── Exception ──────────────────────────────────────────────────────────────────

class ExecutionError(Exception):
    """Raised when an IR instruction cannot be executed."""
    pass


# ── Executor ───────────────────────────────────────────────────────────────────

class Executor:
    """
    Drives Python turtle graphics from a flat IR instruction list.

    Parameters
    ----------
    instructions : list[IRInstruction]
        Output of IRGenerator.generate().
    debug : bool
        If True, prints each instruction as it executes.
    save_png : str | None
        If a file path is given, attempts to save the finished drawing as PNG.
        Requires the Pillow library (pip install Pillow).
    speed : int
        Turtle animation speed 1–10 (10 = fastest, 0 = instant).
    """

    def __init__(
        self,
        instructions: list[IRInstruction],
        debug:    bool        = False,
        save_png: str | None  = None,
        speed:    int         = 6,
    ) -> None:
        self._instructions = instructions
        self._debug        = debug
        self._save_png     = save_png
        self._speed        = speed

    # ── Public API ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """
        Execute all IR instructions using Python turtle.
        Opens a window, draws, then waits for the user to close it.
        If save_png is set, saves the canvas before the window closes.
        """
        import turtle

        # ── Screen setup
        screen = turtle.Screen()
        screen.title("RetroTurtle — Drawing Output")
        screen.bgcolor("white")

        # ── Turtle setup
        t = turtle.Turtle()
        t.speed(self._speed)
        t.pencolor("black")
        t.pendown()

        # ── Execute each instruction
        for instr in self._instructions:
            if self._debug:
                print(f"  [exec] {instr}")
            self._execute_one(t, instr)

        # ── Optional PNG export
        if self._save_png:
            self._export_png(screen, self._save_png)

        # ── Keep window open until user closes it
        try:
            screen.mainloop()
        except Exception:
            pass  # Already closed or running in non-interactive mode

    # ── Single-instruction dispatcher ─────────────────────────────────────────

    def _execute_one(self, t, instr: IRInstruction) -> None:
        """Dispatch one IR instruction to the appropriate turtle call."""
        op   = instr.opcode
        args = instr.args

        if op == "PEN_DOWN":
            t.pendown()

        elif op == "PEN_UP":
            t.penup()

        elif op == "FORWARD":
            t.forward(args[0])

        elif op == "BACKWARD":
            t.backward(args[0])

        elif op == "LEFT":
            t.left(args[0])

        elif op == "RIGHT":
            t.right(args[0])

        elif op == "COLOR":
            color_name = str(args[0]).lower()
            self._set_color(t, color_name, instr.line)

        elif op == "MOVE":
            x, y = args[0], args[1]
            was_down = t.isdown()
            t.penup()
            t.goto(x, y)
            if was_down:
                t.pendown()

        else:
            raise ExecutionError(
                f"Unknown IR opcode '{op}' at source line {instr.line}"
            )

    # ── Color helper ───────────────────────────────────────────────────────────

    def _set_color(self, t, name: str, line: int) -> None:
        """
        Set the turtle pen color.
        Accepts any name from _VALID_COLORS, or tries it directly as a
        turtle color string (covers identifier variables that happen to be
        valid color names at runtime).
        """
        try:
            t.pencolor(name)
        except Exception:
            raise ExecutionError(
                f"[Line {line}] '{name}' is not a recognized turtle color."
            )

    # ── PNG export ─────────────────────────────────────────────────────────────

    def _export_png(self, screen, filepath: str) -> None:
        """
        Save the turtle canvas as a PNG using Pillow + Ghostscript-free EPS.
        Prints a warning if Pillow is not installed.
        """
        import os
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        # Step 1 — save canvas as EPS (built into tkinter, no dependencies)
        eps_path = filepath.replace(".png", ".eps")
        try:
            screen.getcanvas().postscript(file=eps_path)
        except Exception as e:
            print(f"[Warning] Could not save EPS: {e}")
            return

        # Step 2 — convert EPS → PNG with Pillow
        try:
            from PIL import Image
            img = Image.open(eps_path)
            img.save(filepath, "PNG")
            os.remove(eps_path)
            print(f"[Info] Drawing saved to {filepath}")
        except ImportError:
            print(
                f"[Info] EPS saved to {eps_path}\n"
                f"       Install Pillow ('pip install Pillow') to auto-convert to PNG."
            )
        except Exception as e:
            print(f"[Warning] PNG export failed: {e}")
