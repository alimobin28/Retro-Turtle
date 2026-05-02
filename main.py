#!/usr/bin/env python3
"""
main.py — Entry point for the RetroTurtle Compiler.

Full pipeline:
    Phase 1 : Lexer          (.rt source  → token list)
    Phase 2 : Parser         (tokens      → AST)
    Phase 3 : Semantic       (AST         → validated AST + symbol table)
    Phase 4 : IR Generation  (AST         → flat IR instructions)
    Phase 5 : Execution      (IR          → turtle graphics window)

Usage:
    python main.py <file.rt>                  # full pipeline (draws on screen)
    python main.py <file.rt> --debug          # verbose output at every phase
    python main.py <file.rt> --ir-only        # stop after IR, print instructions
    python main.py <file.rt> --lex-only       # stop after lexing
    python main.py <file.rt> --save-png       # save drawing as output/drawing.png
    python main.py <file.rt> --output         # also write tokens.txt to output/
    python main.py <file.rt> --save-ir        # write IR to output/program.ir
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.lexer.lexer        import Lexer, LexerError
from src.parser.parser      import Parser, ParseError
from src.backend.semantic   import SemanticAnalyzer, SemanticError
from src.backend.ir_generator import IRGenerator
from src.backend.executor   import Executor, ExecutionError


# ── Helpers ────────────────────────────────────────────────────────────────────

def resolve_path(raw: str) -> Path:
    p = Path(raw)
    if not p.exists():
        alt = Path(__file__).parent / raw
        if alt.exists():
            return alt
        print(f"[Error] File not found: {raw}", file=sys.stderr)
        sys.exit(1)
    return p


def ensure_output_dir() -> Path:
    out = Path(__file__).parent / "output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_tokens(tokens, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for tok in tokens:
            f.write(tok.debug_str() + "\n")
    print(f"  -> Tokens written to {path}")


def write_ir(ir_text: str, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(ir_text + "\n")
    print(f"  -> IR written to {path}")


def section(title: str) -> None:
    print(f"\n[{title}]")
    print("-" * 40)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    # Flags
    debug    = "--debug"    in args
    lex_only = "--lex-only" in args
    ir_only  = "--ir-only"  in args
    save_out = "--output"   in args
    save_png = "--save-png" in args
    save_ir  = "--save-ir"  in args
    files    = [a for a in args if not a.startswith("--")]

    if not files:
        print("[Error] No .rt file specified.", file=sys.stderr)
        sys.exit(1)

    source_path = resolve_path(files[0])
    source_text = source_path.read_text(encoding="utf-8")

    print(f"\n{'='*55}")
    print(f"  RetroTurtle Compiler  |  {source_path.name}")
    print(f"{'='*55}")

    # ── Phase 1: Lexer ─────────────────────────────────────────────────────────
    section("Phase 1 — Lexical Analysis")
    if debug:
        print("  Tokens:")
    try:
        lexer  = Lexer(source_text, debug=debug)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"\n  {e}", file=sys.stderr); sys.exit(1)

    print(f"  -> {len(tokens)} token(s) produced.")
    if save_out:
        write_tokens(tokens, ensure_output_dir() / "tokens.txt")
    if lex_only:
        print("\n[Done] Stopped after lexing."); return

    # ── Phase 2: Parser ────────────────────────────────────────────────────────
    section("Phase 2 — Syntax Analysis (Parser)")
    try:
        parser = Parser(tokens, debug=debug)
        ast    = parser.parse()
    except ParseError as e:
        print(f"\n  {e}", file=sys.stderr); sys.exit(1)

    print(f"  -> AST built. {len(ast.statements)} top-level statement(s).")
    if not debug:
        print("\n  AST Preview:")
        for line in ast.pretty().splitlines():
            print(f"    {line}")

    # ── Phase 3: Semantic Analysis ─────────────────────────────────────────────
    section("Phase 3 — Semantic Analysis")
    try:
        analyzer = SemanticAnalyzer(ast, debug=debug)
        analyzer.analyze()
    except SemanticError as e:
        print(f"\n  {e}", file=sys.stderr); sys.exit(1)

    sym_count = len(analyzer.symbol_table)
    print(f"  -> Semantic check passed. {sym_count} identifier(s) in symbol table.")
    if debug and sym_count > 0:
        pass  # already printed by analyzer in debug mode

    # ── Phase 4: IR Generation ─────────────────────────────────────────────────
    section("Phase 4 — IR Generation")
    gen          = IRGenerator(ast, debug=debug)
    instructions = gen.generate()

    print(f"  -> {len(instructions)} IR instruction(s) generated.")

    if not debug:
        print("\n  IR Listing:")
        for i, instr in enumerate(instructions, 1):
            print(f"    {i:>3}. {instr}")

    if save_ir or ir_only:
        write_ir(gen.ir_to_text(), ensure_output_dir() / "program.ir")

    if ir_only:
        print("\n[Done] Stopped after IR generation."); return

    # ── Phase 5: Execution ─────────────────────────────────────────────────────
    section("Phase 5 — Execution (Turtle Graphics)")
    print("  -> Opening drawing window...")
    print("     Close the window to exit.\n")

    png_path = str(ensure_output_dir() / "drawing.png") if save_png else None

    try:
        executor = Executor(
            instructions,
            debug    = debug,
            save_png = png_path,
            speed    = 6,
        )
        executor.run()
    except ExecutionError as e:
        print(f"\n  {e}", file=sys.stderr); sys.exit(1)

    print(f"\n{'='*55}")
    print("  Compilation complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
