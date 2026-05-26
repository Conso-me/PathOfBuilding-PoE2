#!/usr/bin/env python3
"""Extract English UI string-literal candidates from src/ for the JP translator.

Scans every .lua file under src/ (excluding Data/, Locale/, Export/) for double-quoted
string literals that *look* like user-facing UI text — capitalized, mixed-case,
multi-word, or punctuated.

Output:
    src/Locale/ja_JP/UI.lua  is regenerated with two sections:
        1. Existing translated entries (preserved)
        2. TODO comments for newly-discovered candidates

This keeps already-translated work safe across re-runs.

Usage:
    python3 tools/extract_strings.py                # update UI.lua in place
    python3 tools/extract_strings.py --dry-run      # just print stats + sample
    python3 tools/extract_strings.py --print-todo   # print new TODOs to stdout
"""
import argparse
import re
import sys
from pathlib import Path

# Roots scanned for string literals
SCAN_ROOTS = ["src/Modules", "src/Classes"]

# Skip these subdirs entirely (data files, generated content, our own locale)
SKIP_DIRS = {"src/Data", "src/Locale", "src/Export", "src/Assets", "src/TreeData"}

# Lua string literal: double-quoted, single-line only (Lua "..." strings cannot
# physically span newlines; restricting to one line avoids accidentally swallowing
# code blocks when the source has odd quoting in comments).
STRING_RE = re.compile(r'"((?:[^"\\\n]|\\.)*)"')

# Length bounds for candidates.
MIN_LEN, MAX_LEN = 3, 200

# Identifier-looking strings (CamelCase without spaces, snake_case, prefixed codes)
# These almost always represent internal IDs, not UI text.
CAMEL_NOSPACE_RE = re.compile(r'^[A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*$')  # ≥2 caps, no spaces
SNAKE_CASE_RE = re.compile(r'^[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+$')
ALLCAPS_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')

# Path / format / escape patterns we never want
EXCLUDE_RE = re.compile(
    r'^(?:'
    r'.*\.(lua|xml|cfg|png|jpg|json|zip|txt|tga)$'
    r'|.*[/\\].*'                           # path-like (slash or backslash)
    r'|.*%.*'                               # any percent (printf/Lua pattern)
    r'|.*\^[0-9xX].*'                       # PoB color escapes like ^7 or ^xRRGGBB
    r'|.*<.*>.*'                            # contains XML/HTML-like brackets
    r'|.*\{.*\}.*'                          # contains brace template
    r'|.*[=*+]{1,}.*[A-Za-z]+\(.*'          # formula/expression like sqrt(...) or a*b + c
    r')$'
)

# Reject if contains no vowel — usually identifiers or codes
VOWEL_RE = re.compile(r'[aeiouAEIOU]')


def looks_like_ui(s: str) -> bool:
    if not (MIN_LEN <= len(s) <= MAX_LEN):
        return False
    if s in LITERAL_STOPWORDS:
        return False
    if s != s.strip():
        return False                        # leading/trailing whitespace → suffix fragment
    if EXCLUDE_RE.match(s):
        return False
    if ALLCAPS_RE.match(s):
        return False
    if not VOWEL_RE.search(s):
        return False
    has_space = " " in s
    has_sentence_punct = any(c in s for c in ":?!,.")
    if has_space or has_sentence_punct:
        # Multi-word phrase or sentence — usually UI.
        if not re.search(r'[a-z]', s):
            return False
        return True
    # Single token — accept only if Capitalized (first upper, rest lower).
    if SNAKE_CASE_RE.match(s):
        return False
    if CAMEL_NOSPACE_RE.match(s):
        return False
    if re.match(r'^[A-Z][a-z]+$', s):
        return True
    return False

# These exact tokens come from PoB rendering style args (alignments, fonts, colors)
LITERAL_STOPWORDS = {
    "LEFT", "RIGHT", "CENTER", "TOPLEFT", "TOPRIGHT", "BOTTOMLEFT", "BOTTOMRIGHT",
    "VAR", "FIXED", "PROP", "VAR BOLD", "FONTI",
    "WHITE", "BLACK", "RED", "GREEN", "BLUE", "YELLOW", "GRAY",
    "TRUE", "FALSE", "NIL",
}

EXISTING_RE = re.compile(
    r'^\s*\["((?:[^"\\]|\\.)*)"\]\s*=\s*"((?:[^"\\]|\\.)*)"\s*,\s*(?:--.*)?$'
)


def read_existing(ui_path: Path) -> dict[str, str]:
    if not ui_path.exists():
        return {}
    out: dict[str, str] = {}
    for line in ui_path.read_text(encoding="utf-8").splitlines():
        m = EXISTING_RE.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def collect_candidates(repo_root: Path) -> set[str]:
    found: set[str] = set()
    for rel in SCAN_ROOTS:
        root = repo_root / rel
        if not root.exists():
            continue
        for lua in root.rglob("*.lua"):
            # skip nested excluded dirs
            if any(str(lua).startswith(str(repo_root / sd)) for sd in SKIP_DIRS):
                continue
            try:
                text = lua.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in STRING_RE.finditer(text):
                s = m.group(1)
                if looks_like_ui(s):
                    found.add(s)
    return found


def write_ui_lua(ui_path: Path, translated: dict[str, str]) -> None:
    """UI.lua contains ONLY translated entries — keeps the runtime file small."""
    lua_escape = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
    lines = [
        "-- UI chrome strings.",
        "-- Entries are maintained manually; new candidates live in",
        "-- docs/ja/ui-translation-queue.txt (regenerate via tools/extract_strings.py).",
        "return {",
    ]
    for en in sorted(translated):
        lines.append(f'\t["{lua_escape(en)}"] = "{lua_escape(translated[en])}",')
    lines.append("}")
    ui_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_todo_queue(queue_path: Path, todos: set[str]) -> None:
    """Plain text queue, one English string per line. Easy to grep, batch-translate, diff."""
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "# UI translation queue — auto-generated by tools/extract_strings.py",
        "# One English UI candidate per line. Translate by adding the pair to",
        "# src/Locale/ja_JP/UI.lua, then re-run the extractor to remove from this list.",
        "#",
        f"# Total pending: {len(todos)}",
        "",
    ]
    body = sorted(todos)
    queue_path.write_text("\n".join(header + body) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-todo", action="store_true",
                        help="Print TODOs to stdout instead of/in-addition-to writing.")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    ui_path = repo_root / "src" / "Locale" / "ja_JP" / "UI.lua"
    queue_path = repo_root / "docs" / "ja" / "ui-translation-queue.txt"

    existing = read_existing(ui_path)
    candidates = collect_candidates(repo_root)

    new_todos = {c for c in candidates if c not in existing}

    print(f"  Existing translated entries : {len(existing)}")
    print(f"  Candidates discovered       : {len(candidates)}")
    print(f"  New TODOs to add            : {len(new_todos)}")

    if args.print_todo or args.dry_run:
        sample = sorted(new_todos)[:25]
        print("\nFirst 25 TODOs (sample):")
        for s in sample:
            print(f"  - {s!r}")

    if not args.dry_run:
        write_ui_lua(ui_path, existing)
        write_todo_queue(queue_path, new_todos)
        print(f"\n  -> rewrote {ui_path.relative_to(repo_root)} ({len(existing)} translated)")
        print(f"  -> rewrote {queue_path.relative_to(repo_root)} ({len(new_todos)} pending)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
