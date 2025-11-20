#!/usr/bin/env python3
"""
Replace use_container_width=... with width=... in the given files.

Usage:
  - Dry-run (show matches, no write):
      python tools\\fix_helpdesk_use_container_width.py --dry-run helpdesk_app.py temp\\helpdesk_app.py
  - Apply changes (make backups .bak before changing):
      python tools\\fix_helpdesk_use_container_width.py --apply helpdesk_app.py temp\\helpdesk_app.py

Behavior:
  - Replaces:
      use_container_width=True  -> width='stretch'
      use_container_width=False -> width='content'
      use_container_width=<expr> -> width=('stretch' if <expr> else 'content')
  - Makes a backup file filename.bak before modifying.
  - Only edits files explicitly passed on the command line (won't touch .venv or other dirs).
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import List, Tuple

# Regex to find use_container_width=... up to a comma or closing paren/bracket
PAT = re.compile(r"""
    (?P<prefix>\buse_container_width\s*=\s*)
    (?P<expr>            # capture the expression to the next comma or closing paren/bracket
        (?:              # non-capturing group for expression chars
            [^,\)\]\}]+  # one or more chars that are not comma or closing ),],}
        )
    )
""", re.VERBOSE)

def replacement(match: re.Match) -> str:
    expr = match.group("expr").strip()
    if expr == "True":
        return "width='stretch'"
    if expr == "False":
        return "width='content'"
    # For non-literals: keep the original expr text inside the conditional
    # Avoid double parentheses if expr already enclosed in parentheses
    return f"width=('stretch' if {expr} else 'content')"

def process_text(text: str) -> Tuple[str, List[Tuple[int, str]]]:
    """Return (new_text, list_of_replacements) where each replacement is (offset, original_text)."""
    replacements = []
    def _repl(m):
        orig = m.group(0)
        repl = replacement(m)
        replacements.append((m.start(), orig))
        return repl
    new_text = PAT.sub(_repl, text)
    return new_text, replacements

def process_file(path: Path, apply: bool) -> None:
    text = path.read_text(encoding="utf-8")
    new_text, reps = process_text(text)
    if not reps:
        print(f"No use_container_width occurrences found in {path}")
        return
    print(f"{len(reps)} occurrence(s) in {path}:")
    for i, (off, orig) in enumerate(reps, start=1):
        print(f"  {i}. {orig.strip()[:200]!r}")
    if apply:
        bak = path.with_suffix(path.suffix + ".bak")
        path.rename(bak)  # move original to .bak
        bak_text = bak.read_text(encoding="utf-8")
        # Write new text to original filename
        path.write_text(new_text, encoding="utf-8")
        print(f"Applied replacements and saved backup: {bak.name}")
    else:
        print(f"Dry-run only (no files changed). Use --apply to write changes.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help="Files to process (explicit paths only).")
    parser.add_argument("--apply", action="store_true", help="Write changes (creates .bak backups).")
    parser.add_argument("--dry-run", action="store_true", help="Alias for no --apply (shows matches).")
    args = parser.parse_args()
    apply = args.apply
    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"File not found: {f}")
            continue
        process_file(p, apply)

if __name__ == "__main__":
    main()