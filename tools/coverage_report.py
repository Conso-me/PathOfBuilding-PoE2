#!/usr/bin/env python3
"""Translation coverage report.

Counts T(...) call sites in src/ and reports how many resolve to a translated
entry in src/Locale/ja_JP/UI.lua. Also reports dictionary sizes for the other
categories (Skills, Items, etc.) sourced from poe2db.

Usage:
    python3 tools/coverage_report.py             summary
    python3 tools/coverage_report.py --missing   list untranslated T() keys
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

T_CALL_RE = re.compile(r'T\(\s*"((?:[^"\\]|\\.)*?)"\s*\)')
DICT_ENTRY_RE = re.compile(r'^\s*\["((?:[^"\\]|\\.)*)"\]\s*=')


def load_keys(lua_path: Path) -> set[str]:
    if not lua_path.exists():
        return set()
    out: set[str] = set()
    for line in lua_path.read_text(encoding="utf-8").splitlines():
        m = DICT_ENTRY_RE.match(line)
        if m:
            out.add(m.group(1))
    return out


def count_t_calls(repo_root: Path) -> Counter:
    counter: Counter = Counter()
    for root in ("src/Modules", "src/Classes"):
        for lua in (repo_root / root).rglob("*.lua"):
            text = lua.read_text(encoding="utf-8", errors="ignore")
            for m in T_CALL_RE.finditer(text):
                counter[m.group(1)] += 1
    return counter


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing", action="store_true",
                        help="Print untranslated keys sorted by call frequency.")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    locale_dir = repo_root / "src" / "Locale" / "ja_JP"

    t_calls = count_t_calls(repo_root)
    ui_keys = load_keys(locale_dir / "UI.lua")

    distinct = set(t_calls)
    translated = distinct & ui_keys
    missing = distinct - ui_keys

    total_callsites = sum(t_calls.values())
    covered_callsites = sum(c for k, c in t_calls.items() if k in ui_keys)

    print("=== UI (Layer 1) ===")
    print(f"  T() call sites          : {total_callsites}")
    print(f"  Distinct keys           : {len(distinct)}")
    print(f"  Translated keys         : {len(translated)} ({len(translated)/max(len(distinct),1)*100:.1f}%)")
    print(f"  Coverage by call sites  : {covered_callsites}/{total_callsites} ({covered_callsites/max(total_callsites,1)*100:.1f}%)")
    print(f"  Untranslated keys       : {len(missing)}")

    print("\n=== Data dictionaries (Layer 2, from poe2db) ===")
    for name in ("Skills", "Items", "Uniques", "Stats", "Keywords", "Tree", "Mods"):
        keys = load_keys(locale_dir / f"{name}.lua")
        print(f"  {name:<10s}: {len(keys)} entries")

    if args.missing and missing:
        print(f"\n=== Untranslated T() keys ({len(missing)}) — sorted by call frequency ===")
        ranked = sorted(missing, key=lambda k: -t_calls[k])
        for k in ranked:
            print(f"  {t_calls[k]:4d}× {k!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
