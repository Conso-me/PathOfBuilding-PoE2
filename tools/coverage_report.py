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

T_CALL_RE       = re.compile(r'\bT\(\s*"((?:[^"\\]|\\.)*?)"\s*\)')
SKILLT_CALL_RE  = re.compile(r'\bSkillT\([^)]+\)')
ITEMT_CALL_RE   = re.compile(r'\bItemT\([^)]+\)')
STATT_CALL_RE   = re.compile(r'\bStatT\(\s*"((?:[^"\\]|\\.)*?)"\s*\)')
KEYWORDT_CALL_RE = re.compile(r'\bKeywordT\([^)]+\)')
MODFORMAT_CALL_RE = re.compile(r'\bModFormat\([^)]+\)')
DICT_ENTRY_RE   = re.compile(r'^\s*\["((?:[^"\\]|\\.)*)"\]\s*=')


def load_keys(lua_path: Path) -> set[str]:
    if not lua_path.exists():
        return set()
    out: set[str] = set()
    for line in lua_path.read_text(encoding="utf-8").splitlines():
        m = DICT_ENTRY_RE.match(line)
        if m:
            out.add(m.group(1))
    return out


def count_t_calls(repo_root: Path, pattern: re.Pattern = T_CALL_RE) -> Counter:
    counter: Counter = Counter()
    for root in ("src/Modules", "src/Classes"):
        for lua in (repo_root / root).rglob("*.lua"):
            text = lua.read_text(encoding="utf-8", errors="ignore")
            for m in pattern.finditer(text):
                if m.groups():
                    counter[m.group(1)] += 1
                else:
                    # ratio-style callers (variable args) — count as anonymous
                    counter["<dynamic>"] += 1
    return counter


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing", action="store_true",
                        help="Print untranslated keys sorted by call frequency.")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    locale_dir = repo_root / "src" / "Locale" / "ja_JP"

    def coverage(name: str, pattern: re.Pattern, dict_file: str) -> set[str]:
        calls = count_t_calls(repo_root, pattern)
        keys = load_keys(locale_dir / dict_file)
        distinct = {k for k in calls if k != "<dynamic>"}
        translated = distinct & keys
        missing = distinct - keys
        sites = sum(calls.values())
        covered = sum(c for k, c in calls.items() if k in keys)
        print(f"=== {name} ===")
        print(f"  Call sites              : {sites}")
        print(f"  Distinct literal keys   : {len(distinct)}")
        print(f"  Translated              : {len(translated)} ({len(translated)/max(len(distinct),1)*100:.1f}%)")
        print(f"  Coverage by call sites  : {covered}/{sites} ({covered/max(sites,1)*100:.1f}%)")
        print(f"  Untranslated keys       : {len(missing)}\n")
        return missing

    missing_t = coverage("UI       (T)",       T_CALL_RE,     "UI.lua")
    _missing_stat = coverage("Stats    (StatT)",   STATT_CALL_RE, "Stats.lua")
    print("=== Other wrappers (dynamic args — count only) ===")
    for label, pat in (("SkillT",  SKILLT_CALL_RE), ("ItemT",   ITEMT_CALL_RE),
                       ("KeywordT", KEYWORDT_CALL_RE), ("ModFormat", MODFORMAT_CALL_RE)):
        calls = count_t_calls(repo_root, pat)
        print(f"  {label:<10s}: {sum(calls.values())} call sites")

    print("\n=== Data dictionaries (Layer 2) ===")
    for name in ("Skills", "Items", "Uniques", "Stats", "Keywords", "Tree", "Mods"):
        keys = load_keys(locale_dir / f"{name}.lua")
        print(f"  {name:<10s}: {len(keys)} entries")

    if args.missing and (missing_t or _missing_stat):
        print(f"\n=== Untranslated keys (by call frequency) ===")
        if missing_t:
            calls = count_t_calls(repo_root, T_CALL_RE)
            print(f"-- UI ({len(missing_t)}) --")
            for k in sorted(missing_t, key=lambda k: -calls.get(k, 0)):
                print(f"  {calls.get(k, 0):4d}× {k!r}")
        if _missing_stat:
            calls = count_t_calls(repo_root, STATT_CALL_RE)
            print(f"-- Stats ({len(_missing_stat)}) --")
            for k in sorted(_missing_stat, key=lambda k: -calls.get(k, 0)):
                print(f"  {calls.get(k, 0):4d}× {k!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
