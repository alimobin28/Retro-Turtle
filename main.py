#!/usr/bin/env python3
"""
main.py — Entry point for the RetroTurtle Compiler.

Full compilation pipeline:
    Phase 1 : Lexer       (.rt source  -> token list)
    Phase 2 : Parser      (tokens      -> AST)
    Phase 3 : Semantic    (AST         -> validated AST + symbol table)
    Phase 4 : IR Gen      (AST         -> flat IR instructions)
    Phase 5 : Optimizer   (IR          -> optimized IR)
    Phase 6 : Execution   (IR          -> turtle graphics window)

Usage:
    python main.py <file.rt>                   # full pipeline
    python main.py <file.rt> -o output.ir      # compile + write IR to file
    python main.py <file.rt> --debug           # verbose output at every phase
    python main.py <file.rt> --ir-only         # stop after IR, print instructions
    python main.py <file.rt> --lex-only        # stop after lexing
    python main.py <file.rt> --save-png        # save drawing as output/drawing.png
    python main.py <file.rt> --save-ir         # write IR to output/program.ir
    python main.py <file.rt> --no-opt          # skip optimization phase
    python main.py --interactive               # REPL mode
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.lexer.lexer          import Lexer, LexerError
from src.parser.parser        import Parser, ParseError
from src.backend.semantic     import SemanticAnalyzer, SemanticError
from src.backend.ir_generator import IRGenerator
from src.backend.optimizer    import Optimizer
from src.backend.executor     import Executor, ExecutionError


def resolve_path(raw):
    p = Path(raw)
    if not p.exists():
        alt = Path(__file__).parent / raw
        if alt.exists():
            return alt
        print(f"[Error] File not found: {raw}", file=sys.stderr)
        sys.exit(1)
    return p


def ensure_output_dir():
    out = Path(__file__).parent / "output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_tokens(tokens, path):
    with open(path, "w", encoding="utf-8") as f:
        for tok in tokens:
            f.write(tok.debug_str() + "\n")
    print(f"  -> Tokens written to {path}")


def write_ir(ir_text, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(ir_text + "\n")
    print(f"  -> IR written to {path}")


def section(title):
    print(f"\n[{title}]")
    print("-" * 40)


def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    if "--interactive" in args:
        from src.repl import run_repl
        run_repl(debug="--debug" in args)
        return

    debug    = "--debug"    in args
    lex_only = "--lex-only" in args
    ir_only  = "--ir-only"  in args
    save_out = "--output"   in args
    save_png = "--save-png" in args
    save_ir  = "--save-ir"  in args
    no_opt   = "--no-opt"   in args

    out_file = None
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 >= len(args):
            print("[Error] -o requires a filename.", file=sys.stderr)
            sys.exit(1)
        out_file = Path(args[idx + 1])

    files = [a for a in args if not a.startswith("-")]
    if not files:
        print("[Error] No .rt file specified.", file=sys.stderr)
        sys.exit(1)

    source_path = resolve_path(files[0])
    source_text = source_path.read_text(encoding="utf-8")

    print(f"\n{'='*55}")
    print(f"  RetroTurtle Compiler  |  {source_path.name}")
    print(f"{'='*55}")

    # Phase 1: Lexer
    section("Phase 1 — Lexical Analysis")
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

    # Phase 2: Parser
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

    # Phase 3: Semantic
    section("Phase 3 — Semantic Analysis")
    try:
        analyzer = SemanticAnalyzer(ast, debug=debug)
        analyzer.analyze()
    except SemanticError as e:
        print(f"\n  {e}", file=sys.stderr); sys.exit(1)
    sym_count = len(analyzer.symbol_table)
    print(f"  -> Semantic check passed. {sym_count} identifier(s) in symbol table.")

    # Phase 4: IR Generation
    section("Phase 4 — IR Generation")
    gen          = IRGenerator(ast, debug=debug)
    instructions = gen.generate()
    print(f"  -> {len(instructions)} IR instruction(s) generated.")
    if not debug:
        print("\n  IR Listing (before optimization):")
        for i, instr in enumerate(instructions, 1):
            print(f"    {i:>3}. {instr}")

    # Phase 5: Optimization
    section("Phase 5 — Optimization")
    if no_opt:
        print("  -> Optimization skipped (--no-opt).")
        optimized = instructions
    else:
        opt       = Optimizer(instructions, debug=debug)
        optimized = opt.optimize()
        opt.print_report()
        if not debug:
            print("\n  IR Listing (after optimization):")
            for i, instr in enumerate(optimized, 1):
                print(f"    {i:>3}. {instr}")

    ir_text = "\n".join(str(i) for i in optimized)
    if out_file:
        out_file.parent.mkdir(parents=True, exist_ok=True)
        write_ir(ir_text, out_file)
    if save_ir or ir_only:
        write_ir(ir_text, ensure_output_dir() / "program.ir")
    if ir_only:
        print("\n[Done] Stopped after IR generation."); return

    # Phase 6: Execution
    section("Phase 6 — Execution (Turtle Graphics)")
    print("  -> Opening drawing window...")
    print("     Close the window to exit.\n")
    png_path = str(ensure_output_dir() / "drawing.png") if save_png else None
    try:
        Executor(optimized, debug=debug, save_png=png_path, speed=6).run()
    except ExecutionError as e:
        print(f"\n  {e}", file=sys.stderr); sys.exit(1)

    print(f"\n{'='*55}")
    print("  Compilation complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()