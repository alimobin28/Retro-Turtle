#!/usr/bin/env python3
"""
main.py — Entry point for the RetroTurtle Lexer.

Usage:
    python main.py <file.rt>            # normal mode
    python main.py <file.rt> --debug    # prints <TYPE, VALUE, LINE> for every token
    python main.py <file.rt> --output   # also writes tokens to output/tokens.txt
"""

import sys
import os
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent))

from src.lexer.lexer import Lexer, LexerError


def resolve_path(raw: str) -> Path:
    """Resolve a file path relative to the project root."""
    p = Path(raw)
    if not p.exists():
        # Try relative to this script's directory
        alt = Path(__file__).parent / raw
        if alt.exists():
            return alt
        print(f"[Error] File not found: {raw}", file=sys.stderr)
        sys.exit(1)
    return p


def write_tokens_to_file(tokens, out_path: Path) -> None:
    """Persist token list to output/tokens.txt."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for tok in tokens:
            f.write(tok.debug_str() + "\n")
    print(f"[Info] Tokens written to {out_path}")


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print("Usage: python main.py <file.rt> [--debug] [--output]")
        sys.exit(0)

    # Parse flags
    debug       = "--debug"  in args
    save_output = "--output" in args
    positional  = [a for a in args if not a.startswith("--")]

    if not positional:
        print("[Error] No .rt file specified.", file=sys.stderr)
        sys.exit(1)

    source_path = resolve_path(positional[0])
    source_text = source_path.read_text(encoding="utf-8")

    print(f"[RetroTurtle Lexer] Processing: {source_path}")
    if debug:
        print("[Debug mode ON]\n")

    try:
        lexer  = Lexer(source_text, debug=debug)
        tokens = lexer.tokenize()
    except LexerError as err:
        print(f"\n{err}", file=sys.stderr)
        sys.exit(1)

    # Summary
    print(f"\n[Done] {len(tokens)} token(s) produced.")

    if save_output:
        out_file = Path(__file__).parent / "output" / "tokens.txt"
        write_tokens_to_file(tokens, out_file)


if __name__ == "__main__":
    main()