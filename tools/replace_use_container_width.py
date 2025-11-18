#!/usr/bin/env python3
"""
Tool to replace deprecated Streamlit use_container_width keyword with width in
Python files and Jupyter notebook code cells.

Usage:
  - Dry-run (show files that would change, no write): python tools\\replace_use_container_width.py
  - Apply changes and create branch/commit: python tools\\replace_use_container_width.py --apply --branch chore/replace-use_container_width-with-width-20251113 --commit-message "Replace deprecated use_container_width with width parameter"

Notes:
  - This script ignores paths that start with ".venv", "venv", ".git", "node_modules", "__pycache__".
  - It rewrites only .py and .ipynb code cells (it does not touch third-party package files).
"""
from __future__ import annotations
import argparse
import io
import json
import os
import sys
import token as token_mod
import tokenize
import subprocess
import py_compile
from pathlib import Path
from typing import List, Tuple

IGNORED_DIR_PREFIXES = (".venv", "venv", ".git", "node_modules", "__pycache__")

def is_ignored_path(path: Path) -> bool:
    parts = path.parts
    for p in parts:
        for prefix in IGNORED_DIR_PREFIXES:
            if p.startswith(prefix):
                return True
    return False

def replace_tokens_in_source(src: str) -> Tuple[str, bool]:
    changed = False
    src_bytes = src.encode("utf-8")
    tokens = list(tokenize.tokenize(io.BytesIO(src_bytes).readline))
    out_tokens: List[tokenize.TokenInfo] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == token_mod.NAME and tok.string == "use_container_width":
            j = i + 1
            while j < len(tokens) and tokens[j].type in (token_mod.NL, token_mod.NEWLINE, token_mod.ENCODING):
                j += 1
            if j < len(tokens) and tokens[j].type == token_mod.OP and tokens[j].string == "=":
                k = j + 1
                expr_tokens: List[tokenize.TokenInfo] = []
                paren_depth = 0
                while k < len(tokens):
                    t = tokens[k]
                    if t.type == token_mod.OP and t.string in ("(", "[", "{"):
                        paren_depth += 1
                    elif t.type == token_mod.OP and t.string in (")", "]", "}"):
                        if paren_depth > 0:
                            paren_depth -= 1
                    if paren_depth == 0 and t.type == token_mod.OP and t.string in (",", ")"):
                        break
                    if t.type in (token_mod.NEWLINE, token_mod.NL):
                        break
                    expr_tokens.append(t)
                    k += 1
                expr_text = tokenize.untokenize(expr_tokens)
                expr_text_stripped = expr_text.strip()
                if expr_text_stripped == "True":
                    replacement_str = "width='stretch'"
                elif expr_text_stripped == "False":
                    replacement_str = "width='content'"
                else:
                    replacement_str = f"width=('stretch' if {expr_text_stripped} else 'content')"
                repl_tokens = list(tokenize.generate_tokens(io.StringIO(replacement_str).readline))
                if repl_tokens and repl_tokens[-1].type == token_mod.ENDMARKER:
                    repl_tokens = repl_tokens[:-1]
                out_tokens.extend(repl_tokens)
                changed = True
                i = k
                continue
        out_tokens.append(tok)
        i += 1
    try:
        new_src = tokenize.untokenize(out_tokens)
    except Exception:
        return src, False
    return new_src, changed

def process_py_file(path: Path) -> Tuple[bool, str]:
    src = path.read_text(encoding="utf-8")
    new_src, changed = replace_tokens_in_source(src)
    if changed and new_src != src:
        path.write_text(new_src, encoding="utf-8")
    return changed, str(path)

def process_ipynb_file(path: Path) -> Tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    obj = json.loads(text)
    changed_any = False
    for cell in obj.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        if isinstance(source, list):
            src = "".join(source)
        else:
            src = source
        new_src, changed = replace_tokens_in_source(src)
        if changed and new_src != src:
            cell["source"] = new_src.splitlines(keepends=True)
            changed_any = True
    if changed_any:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    return changed_any, str(path)

def find_targets(root: Path) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file():
            if is_ignored_path(p):
                continue
            if p.suffix in (".py", ".ipynb"):
                files.append(p)
    return files

def run_py_compile(files: List[Path]) -> List[str]:
    failures = []
    for f in files:
        if f.suffix != ".py":
            continue
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError:
            failures.append(str(f))
    return failures

def run_git_cmd(args: List[str], check=True, capture_output=False):
    return subprocess.run(["git"] + args, check=check, capture_output=capture_output, text=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to files (otherwise dry-run).")
    parser.add_argument("--branch", default="chore/replace-use_container_width-with-width-20251113", help="Branch name to create when --apply is used.")
    parser.add_argument("--commit-message", default="Replace deprecated use_container_width with width parameter")
    parser.add_argument("--push", action="store_true", help="Push branch after commit.")
    parser.add_argument("--create-pr", action="store_true", help="Create a PR using 'gh pr create' after push (requires GitHub CLI and auth).")
    args = parser.parse_args()

    root = Path(".").resolve()
    targets = find_targets(root)
    if not targets:
        print("No .py or .ipynb files found to scan.")
        return

    modified_files = []
    for p in sorted(targets):
        try:
            if p.suffix == ".py":
                if args.apply:
                    changed, name = process_py_file(p)
                    if changed:
                        modified_files.append(str(p))
                else:
                    content = p.read_text(encoding="utf-8")
                    if "use_container_width" in content:
                        modified_files.append(str(p))
            elif p.suffix == ".ipynb":
                if args.apply:
                    changed, name = process_ipynb_file(p)
                    if changed:
                        modified_files.append(str(p))
                else:
                    content = p.read_text(encoding="utf-8")
                    if "use_container_width" in content:
                        modified_files.append(str(p))
        except Exception as e:
            print(f"Error processing {p}: {e}", file=sys.stderr)

    if not args.apply:
        if modified_files:
            print("Files that would be changed (dry-run):")
            for f in modified_files:
                print(" -", f)
        else:
            print("No occurrences of use_container_width found in scanned files.")
        return

    try:
        run_git_cmd(["checkout", "-b", args.branch])
        print(f"Created and switched to branch {args.branch}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create branch {args.branch}: {e}", file=sys.stderr)

    run_git_cmd(["add", "."])
    changes_path = root / "CHANGES.md"
    note = (
        f"- 2025-11-13: Replaced deprecated Streamlit keyword argument `use_container_width` with `width` in application code.\n"
        "  - True -> width='stretch'\n"
        "  - False -> width='content'\n"
        "  - non-literals -> width=('stretch' if expr else 'content')\n"
    )
    if changes_path.exists():
        existing = changes_path.read_text(encoding="utf-8")
        new_existing = existing + "\n" + note
        changes_path.write_text(new_existing, encoding="utf-8")
    else:
        changes_path.write_text("# CHANGES\n\n" + note, encoding="utf-8")
    run_git_cmd(["add", "CHANGES.md"])
    run_git_cmd(["commit", "-m", args.commit_message])
    print("Committed changes.")
    if args.push:
        run_git_cmd(["push", "--set-upstream", "origin", args.branch])
        print(f"Pushed {args.branch} to origin.")
    failures = run_py_compile([Path(f) for f in modified_files])
    if failures:
        print("Syntax check failures in the following files:")
        for f in failures:
            print(" -", f)
    else:
        print("All modified .py files passed python -m py_compile.")

    if args.create_pr:
        pr_body = (
            "Replace deprecated use_container_width with width parameter.\n\n"
            f"Repository: {root}\n\n"
            "Replacements:\n"
            "- use_container_width=True -> width='stretch'\n"
            "- use_container_width=False -> width='content'\n"
            "- use_container_width=<expr> -> width=('stretch' if <expr> else 'content')\n\n"
            "Files changed:\n" + os.linesep.join(" - " + f for f in modified_files) + "\n\n"
            "Note: Non-literal expressions were converted into conditional expressions like width=('stretch' if expr else 'content').\n"
        )
        subprocess.run(["gh", "pr", "create", "--title", args.commit_message, "--body", pr_body, "--base", "main", "--head", args.branch])

if __name__ == "__main__":
    main()