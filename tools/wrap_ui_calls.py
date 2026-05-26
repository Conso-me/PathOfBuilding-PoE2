#!/usr/bin/env python3
"""Wrap literal string arguments of known UI-creation calls in T().

Targets (and which positional literal arg gets wrapped):
    new("ButtonControl", anchor, geom, "Label", ...)   → wrap arg 4
    new("LabelControl",  anchor, geom, "Text",  ...)   → wrap arg 4
    OpenPopup(width, height, "Title", ...)             → wrap arg 3
    OpenMessagePopup("Title", "Body literal")          → wrap arg 1 (and arg 2 if plain literal)
    OpenConfirmPopup("Title", "Body", "ConfirmLabel")  → wrap arg 1 + 3

Conservative rules — never wrap when:
    - The "literal" contains `..` (string concatenation)
    - The "literal" starts with `^` (PoB color escape — handled differently)
    - The "literal" is already inside T(...)
    - The arg looks like a variable / function call (no leading quote)

Usage:
    python3 tools/wrap_ui_calls.py --dry-run       preview changes
    python3 tools/wrap_ui_calls.py                 apply changes
    python3 tools/wrap_ui_calls.py --file PATH     restrict to one file
"""
import argparse
import re
import sys
from pathlib import Path

# Arg shapes: nil  | { ... non-brace ... } | "..." | T("...") | identifier(...)
# For first 2 positional args of ButtonControl/LabelControl: nil or {...}
ARG_TABLE_OR_NIL = r'(?:nil|\{[^{}]*\})'

# Pattern for the LITERAL we want to wrap. Conservative:
#   double-quoted, no escape that suggests dynamic content, no ^ color, no T( already
LITERAL_SIMPLE = r'"((?:[^"\\\n]|\\.)*?)"'

WRAP_PATTERNS = [
    # new("ButtonControl", anchor, geom, "Label", ...)
    (
        re.compile(
            rf'(new\s*\(\s*"ButtonControl"\s*,\s*{ARG_TABLE_OR_NIL}\s*,\s*\{{[^{{}}]*\}}\s*,\s*){LITERAL_SIMPLE}'
        ),
        "ButtonControl label",
    ),
    # new("LabelControl", anchor, geom, "Text", ...)
    (
        re.compile(
            rf'(new\s*\(\s*"LabelControl"\s*,\s*{ARG_TABLE_OR_NIL}\s*,\s*\{{[^{{}}]*\}}\s*,\s*){LITERAL_SIMPLE}'
        ),
        "LabelControl text",
    ),
    # OpenPopup(W, H, "Title", ...) — W and H are numbers / simple expressions, no commas inside braces
    (
        re.compile(
            rf'(:OpenPopup\s*\(\s*[^,]+,\s*[^,]+,\s*){LITERAL_SIMPLE}'
        ),
        "OpenPopup title",
    ),
    # OpenMessagePopup("Title", ...) — wrap title only (body often contains concatenation)
    (
        re.compile(
            rf'(:OpenMessagePopup\s*\(\s*){LITERAL_SIMPLE}'
        ),
        "OpenMessagePopup title",
    ),
    # OpenConfirmPopup("Title", ...) — wrap title only
    (
        re.compile(
            rf'(:OpenConfirmPopup\s*\(\s*){LITERAL_SIMPLE}'
        ),
        "OpenConfirmPopup title",
    ),
    # tooltip:AddLine(size, "literal") — explanatory help text
    # First arg is the font size (integer), then the literal line.
    (
        re.compile(
            rf'(tooltip:AddLine\s*\(\s*\d+\s*,\s*){LITERAL_SIMPLE}'
        ),
        "tooltip:AddLine",
    ),
]


def looks_wrappable(literal: str) -> bool:
    """Decide whether to wrap. Conservative: skip dynamic / colored / empty / very short."""
    if len(literal) == 0:
        return False
    if literal.startswith("^"):
        return False                # PoB color escape — keep as is
    if "\\n" in literal or "\\t" in literal:
        return False                # whitespace / formatting strings
    if not re.search(r"[A-Za-z]", literal):
        return False                # no letters
    if literal in {"LEFT", "RIGHT", "CENTER", "TOPLEFT", "TOPRIGHT", "BOTTOMLEFT", "BOTTOMRIGHT", "VAR", "FIXED", "VAR BOLD"}:
        return False
    return True


def wrap_file(path: Path, apply: bool) -> tuple[int, list[str]]:
    text = path.read_text(encoding="utf-8")
    edits: list[str] = []

    def make_replacer(label: str):
        def replacer(m: re.Match) -> str:
            prefix = m.group(1)
            literal = m.group(2)
            if not looks_wrappable(literal):
                return m.group(0)
            # Skip if already adjacent to T(  (rough check on the preceding chars)
            start = m.start()
            if start >= 2 and text[start - 2 : start] == "T(":
                return m.group(0)
            edits.append(f'  {path.name}: {label}: "{literal}"')
            return f'{prefix}T("{literal}")'
        return replacer

    new_text = text
    for pattern, label in WRAP_PATTERNS:
        new_text = pattern.sub(make_replacer(label), new_text)

    if apply and new_text != text:
        path.write_text(new_text, encoding="utf-8")

    return (len(edits), edits)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--file", help="Restrict to one file path.")
    parser.add_argument("--show-edits", action="store_true",
                        help="Print every edit. Default: print only summary per file.")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    if args.file:
        p = Path(args.file)
        files = [p if p.is_absolute() else (repo_root / p).resolve()]
    else:
        files = []
        for root in ("src/Modules", "src/Classes"):
            files.extend((repo_root / root).rglob("*.lua"))

    total_edits = 0
    files_changed = 0
    for f in sorted(files):
        n, edits = wrap_file(f, apply=not args.dry_run)
        if n > 0:
            files_changed += 1
            total_edits += n
            print(f"{f.relative_to(repo_root)}: {n} wraps")
            if args.show_edits:
                for e in edits:
                    print(e)

    verb = "would wrap" if args.dry_run else "wrapped"
    print(f"\n{verb} {total_edits} literals across {files_changed} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
