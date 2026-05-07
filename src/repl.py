"""
repl.py — Interactive REPL mode for the RetroTurtle compiler.

Provides a live read-eval-print loop where the user can type RetroTurtle
commands one line (or block) at a time and see the results immediately.

Features:
  • Multi-line support — opens a `repeat ... end` block across lines.
  • Type `run` to execute the current buffer (opens turtle window).
  • Type `ir` to print the current IR without executing.
  • Type `clear` to reset the buffer.
  • Type `quit` or `exit` to leave the REPL.
  • Full pipeline: Lexer → Parser → Semantic → Optimizer → IR → Executor.

Usage:
    python main.py --interactive
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.lexer.lexer          import Lexer, LexerError
from src.parser.parser        import Parser, ParseError
from src.backend.semantic     import SemanticAnalyzer, SemanticError
from src.backend.ir_generator import IRGenerator
from src.backend.optimizer    import Optimizer
from src.backend.executor     import Executor, ExecutionError

_BANNER = r"""
╔══════════════════════════════════════════════╗
║   🐢  RetroTurtle — Interactive REPL  🐢     ║
╚══════════════════════════════════════════════╝
  Type RetroTurtle commands line by line.
  Special commands:
    run    — execute the buffer (opens drawing window)
    ir     — print current IR without executing
    opt    — print optimized IR
    clear  — reset the buffer
    quit   — exit the REPL

  Example session:
    >>> pen_down
    >>> color red
    >>> repeat 4
    ...   forward 50
    ...   right 90
    ... end
    >>> run
"""


def run_repl(debug: bool = False) -> None:
    """Start the interactive REPL loop."""
    print(_BANNER)

    buffer: list[str] = []
    depth  = 0          # nesting depth of open repeat blocks

    while True:
        prompt = "... " if depth > 0 else ">>> "
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n[REPL] Bye!")
            break

        stripped = line.strip().lower()

        # ── Special REPL commands ──────────────────────────────────────────────

        if stripped == "quit" or stripped == "exit":
            print("[REPL] Bye!")
            break

        if stripped == "clear":
            buffer.clear()
            depth = 0
            print("[REPL] Buffer cleared.")
            continue

        if stripped == "ir":
            if not buffer:
                print("[REPL] Buffer is empty.")
            else:
                _compile_and_show_ir(buffer, debug=debug, optimized=False)
            continue

        if stripped == "opt":
            if not buffer:
                print("[REPL] Buffer is empty.")
            else:
                _compile_and_show_ir(buffer, debug=debug, optimized=True)
            continue

        if stripped == "run":
            if not buffer:
                print("[REPL] Buffer is empty. Type some commands first.")
            else:
                _compile_and_run(buffer, debug=debug)
            continue

        # ── Track nesting depth ───────────────────────────────────────────────
        tok = stripped.split()
        if tok and tok[0] == "repeat":
            depth += 1
        if tok and tok[0] == "end":
            depth = max(0, depth - 1)

        buffer.append(line)

        # Auto-execute single commands (not inside a block)
        if depth == 0 and buffer:
            # Provide instant feedback for single-line commands
            _compile_and_preview(buffer, debug=debug)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_buffer(buffer: list[str], debug: bool = False):
    """
    Run Lexer → Parser → Semantic on the joined buffer.
    Returns (instructions_unoptimized, analyzer) or prints error and returns None.
    """
    source = "\n".join(buffer)
    try:
        tokens   = Lexer(source, debug=debug).tokenize()
        ast      = Parser(tokens, debug=debug).parse()
        analyzer = SemanticAnalyzer(ast, debug=debug)
        analyzer.analyze()
        instrs   = IRGenerator(ast, debug=debug).generate()
        return instrs, analyzer
    except (LexerError, ParseError, SemanticError) as e:
        print(f"  [Error] {e}")
        return None, None


def _compile_and_preview(buffer: list[str], debug: bool = False) -> None:
    """Show a quick IR preview after each complete statement."""
    result = _parse_buffer(buffer, debug)
    if result[0] is None:
        return
    instrs, _ = result
    opt_instrs = Optimizer(instrs).optimize()
    print(f"  [OK] {len(opt_instrs)} IR instruction(s) in buffer "
          f"(type 'run' to execute, 'ir' to list)")


def _compile_and_show_ir(buffer: list[str], debug: bool, optimized: bool) -> None:
    """Print the IR listing for the current buffer."""
    result = _parse_buffer(buffer, debug)
    if result[0] is None:
        return
    instrs, _ = result
    if optimized:
        opt = Optimizer(instrs, debug=debug)
        instrs = opt.optimize()
        opt.print_report()
        label = "Optimized IR"
    else:
        label = "IR"
    print(f"\n  [{label}]")
    for i, instr in enumerate(instrs, 1):
        print(f"    {i:>3}. {instr}")
    print()


def _compile_and_run(buffer: list[str], debug: bool) -> None:
    """Full pipeline: compile and execute the current buffer."""
    result = _parse_buffer(buffer, debug)
    if result[0] is None:
        return
    instrs, _ = result

    opt = Optimizer(instrs, debug=debug)
    opt_instrs = opt.optimize()
    opt.print_report()

    print("\n  [REPL] Opening drawing window… close it to continue.\n")
    try:
        Executor(opt_instrs, debug=debug, speed=6).run()
    except ExecutionError as e:
        print(f"  [ExecutionError] {e}")