#!/usr/bin/env python3
"""Scrape poe2db.tw/jp/ navigation links and build EN→JP dictionaries.

Output: src/Locale/ja_JP/<Category>.lua  (one file per category)

Strategy:
    poe2db structures internal links as <a href="/jp/Slug_With_Underscores">日本語名</a>.
    Slugs are the canonical English identifiers (matching PoB's Data/ contents).
    Link text is the localized Japanese name.

Dependencies (system packages only):
    - python3-requests  (apt install python3-requests, already present)
    - stdlib only otherwise

Respects:
    - robots.txt allows /, no crawl-delay specified → we apply 1.0s self-imposed.
    - User-Agent identifies the project for poe2db operators.
"""
import argparse
import html as html_lib
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote

import requests

BASE = "https://poe2db.tw"
USER_AGENT = "PoB-PoE2-JP/0.1 (i18n; +github.com/Conso-me/PathOfBuilding-PoE2)"
DELAY = 1.0  # seconds between requests; raise if poe2db ops object
TIMEOUT = 30

# poe2db markup notes:
#   - Top-level nav links use class="dropdown-item" / "nav-link" → exclude.
#   - Items use class="whiteitem ItemSubclass" and *relative* hrefs.
#   - Gems use class="gemitem" / "gem_red|green|blue|white|purple|black".
#   - Uniques use class="uniqueitem".
# We match by class pattern so nav garbage is dropped automatically.

# NOTE: src/Locale/ja_JP/Stats.lua is maintained manually — poe2db has no
# dedicated stats page (verified: /jp/Stat /jp/Statistics /jp/Stat_Descriptions
# etc. all 404). It's intentionally NOT in CATEGORIES so this script never
# overwrites it.

CATEGORIES = {
    "Skills": {
        "urls": [
            "/jp/Skill_Gems", "/jp/Support_Gems", "/jp/Spirit_Gems",
            "/jp/Lineage_Supports",
        ],
        "class_re": r"(?:gemitem|gem_red|gem_green|gem_blue|gem_white|gem_purple|gem_black)",
    },
    "Items": {
        # Body-slot pages contain both normal-base items (class="whiteitem") and
        # unique items (class="uniqueitem") in separate sections of the same page.
        "urls": [
            "/jp/Body_Armours", "/jp/Helmets", "/jp/Gloves", "/jp/Boots", "/jp/Belts",
            "/jp/Rings", "/jp/Amulets", "/jp/Bows", "/jp/Crossbows", "/jp/Wands",
            "/jp/Staves", "/jp/Sceptres", "/jp/Spears", "/jp/Flails", "/jp/Quivers",
            "/jp/Shields", "/jp/Focuses", "/jp/Bucklers", "/jp/Charms", "/jp/Flasks",
            "/jp/Jewels", "/jp/Tablets",
        ],
        "class_re": r"whiteitem",
    },
    "Uniques": {
        # Same body-slot URLs as Items — uniques are present on the same pages
        # under a different CSS class. Keep the URL list mirrored.
        "urls": [
            "/jp/Body_Armours", "/jp/Helmets", "/jp/Gloves", "/jp/Boots", "/jp/Belts",
            "/jp/Rings", "/jp/Amulets", "/jp/Bows", "/jp/Crossbows", "/jp/Wands",
            "/jp/Staves", "/jp/Sceptres", "/jp/Spears", "/jp/Flails", "/jp/Quivers",
            "/jp/Shields", "/jp/Focuses", "/jp/Bucklers", "/jp/Charms", "/jp/Flasks",
            "/jp/Jewels", "/jp/Tablets",
        ],
        "class_re": r"uniqueitem",
    },
    "Keywords": {
        "urls": ["/jp/Keywords"],
        # Keywords appear as <a class="KeywordPopups" href="..."> with relative
        # hrefs scattered throughout the document.
        "class_re": r"KeywordPopups",
    },
    "Tree": {
        "urls": ["/jp/passive-skill-tree/", "/jp/Ascendancy_class"],
        "class_re": None,
    },
}

# Plain nav link: <a href="/jp/Slug">JP</a> (used when class_re is None)
PLAIN_LINK_RE = re.compile(
    r'<a\b(?![^>]*class="[^"]*(?:dropdown-item|nav-link)[^"]*")(?:[^>]*?\s)?href="/jp/([^"#?]+?)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
KANA_KANJI_RE = re.compile(r"[぀-ヿ一-鿿]")


def class_link_re(class_re: str) -> re.Pattern:
    """<a ... class="...{class_re}..." ... href="(/jp/)?Slug" ...>JP</a>

    Uses a positive lookahead so class can appear before OR after href in the
    attribute list (poe2db inconsistently orders attributes). Allows relative
    or /jp/-prefixed hrefs."""
    return re.compile(
        rf'<a\b(?=[^>]*?class="[^"]*?{class_re}[^"]*?")[^>]*?\shref="(?:/jp/)?([^"#?/][^"#?]*?)"[^>]*?>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )


def clean_text(raw: str) -> str:
    txt = TAG_RE.sub("", raw)
    txt = html_lib.unescape(txt)
    return WS_RE.sub(" ", txt).strip()


def slug_to_en(slug: str) -> str:
    # poe2db slugs can contain percent-encoded chars (e.g. "Companion%3A_%7B0%7D")
    return unquote(slug).replace("_", " ")


_FETCH_CACHE: dict[str, str] = {}


def fetch(path: str) -> str:
    """Get page text. Caches within a single run so categories that share URLs
    (Items + Uniques use the same body-slot pages) hit the network only once."""
    if path in _FETCH_CACHE:
        return _FETCH_CACHE[path]
    url = f"{BASE}{path}"
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    r.raise_for_status()
    _FETCH_CACHE[path] = r.text
    return r.text


def scrape_pairs(path: str, skip_slugs: set[str], pattern: re.Pattern) -> dict[str, str]:
    """Extract EN slug → JA text pairs from one listing page using the given regex."""
    html = fetch(path)
    pairs: dict[str, str] = {}
    for slug, inner in pattern.findall(html):
        if "/" in slug:           # ignore deep sub-pages
            continue
        if slug in skip_slugs:    # ignore nav/category self-links
            continue
        en = slug_to_en(slug)
        ja = clean_text(inner)
        if not ja or ja == en:
            continue
        if not KANA_KANJI_RE.search(ja):   # no Japanese chars → likely garbage
            continue
        pairs.setdefault(en, ja)
    return pairs


def lua_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ────────────────────────────────────────────────────────────────
# Mod template extraction (separate flow from class-attribute scrape)
# ────────────────────────────────────────────────────────────────

# Mod templates appear as:
#   <span class="explicitMod">…</span>  on /Modifiers (special mods)
#   <div  class="explicitMod">…</div>   on item-base pages (unique mods baked
#                                        into specific item bases)
MOD_SPAN_RE = re.compile(
    r'<(span|div) class="(?:explicitMod|implicitMod)">(.*?)</\1>',
    re.DOTALL,
)
SECONDARY_SPAN_RE = re.compile(
    r'<span class="secondary">.*?</span>',
    re.DOTALL,
)
BADGE_SPAN_RE = re.compile(
    r'<span class="badge[^"]*"[^>]*>.*?</span>',
    re.DOTALL,
)
MOD_VALUE_DOUBLE = re.compile(r'<span class="mod-value">.*?</span>', re.DOTALL)
MOD_VALUE_SINGLE = re.compile(r"<span class='mod-value'>.*?</span>", re.DOTALL)
ANY_TAG_RE = re.compile(r'<[^>]+>')


NDASH_SPAN_RE = re.compile(r'<span class="ndash">(.*?)</span>', re.DOTALL)
# After ndash flatten, mod-value spans are flat — non-greedy is safe.
MOD_VALUE_FLAT = re.compile(
    r"<span class=['\"]mod-value['\"]>([^<]*)</span>"
)
# Sentinel substituted into the HTML for each mod-value, so the outer explicit
# /implicit Mod span has no nested <span> tags by the time we extract it.
SENTINEL = "\x00MV\x00"


def _preflatten(html: str) -> str:
    """Make the HTML safe for non-greedy outer-span extraction by removing all
    nested <span class="ndash"> and replacing every <span class="mod-value">…
    </span> with a SENTINEL marker. We re-introduce per-mod %N placeholders
    later in _normalize_mod."""
    html = NDASH_SPAN_RE.sub(r'\1', html)
    html = MOD_VALUE_FLAT.sub(SENTINEL, html)
    return html


def _normalize_mod(raw: str) -> list[str]:
    """Inner HTML of one explicitMod/implicitMod span → list of clean lines
    with %1, %2, ... placeholders where mod-value spans were.

    Expects the input to have already passed through _preflatten() — SENTINEL
    strings are re-numbered per LINE (not per mod) so that the resulting Lua
    pattern captures align 1-to-1 with Lua gsub backreferences."""
    raw = SECONDARY_SPAN_RE.sub('', raw)
    raw = BADGE_SPAN_RE.sub('', raw)
    parts = re.split(r'<br\s*/?>', raw)
    out: list[str] = []
    for p in parts:
        # Re-number SENTINEL → %1, %2, ... PER LINE so capture indices align
        # with Lua gsub backreference numbering inside this single mod line.
        counter = [0]
        def sub_sentinel(_m):
            counter[0] += 1
            return f"%{counter[0]}"
        s = re.sub(re.escape(SENTINEL), sub_sentinel, p)
        s = ANY_TAG_RE.sub('', s)
        s = (s.replace('&amp;', '&').replace('&lt;', '<')
               .replace('&gt;', '>').replace('&nbsp;', ' '))
        s = re.sub(r'\s+', ' ', s).strip()
        if s:
            out.append(s)
    return out


LUA_MAGIC = set("().%+-*?[]^$")


def _lua_escape_pattern(s: str) -> str:
    """Escape Lua-pattern magic chars (NOT Python regex's set — Lua uses % not \\)."""
    return ''.join('%' + c if c in LUA_MAGIC else c for c in s)


# Pages to harvest mod templates from. Each item-base page contributes the
# explicit/implicit mods baked into its unique items as <div class="...Mod">.
# Order matters only for dedupe — the global /Modifiers entries come first
# because their patterns tend to be more specific (jewel/map mods).
MOD_SOURCES = [
    "/Modifiers",
    "/Body_Armours", "/Helmets", "/Gloves", "/Boots", "/Belts",
    "/Rings", "/Amulets", "/Bows", "/Crossbows", "/Wands",
    "/Staves", "/Sceptres", "/Spears", "/Flails", "/Quivers",
    "/Shields", "/Bucklers", "/Charms", "/Flasks", "/Jewels",
]


def _harvest_mod_lines(path: str) -> tuple[list[list[str]], list[list[str]]]:
    """Fetch /us<path> and /jp<path>, return (en_spans, jp_spans).
    Each span is a list of cleaned mod lines."""
    en_html = fetch("/us" + path)
    time.sleep(DELAY)
    jp_html = fetch("/jp" + path)
    time.sleep(DELAY)
    en_html = _preflatten(en_html)
    jp_html = _preflatten(jp_html)
    en_spans = [_normalize_mod(t[1]) for t in MOD_SPAN_RE.findall(en_html)]
    jp_spans = [_normalize_mod(t[1]) for t in MOD_SPAN_RE.findall(jp_html)]
    return en_spans, jp_spans


def scrape_mod_patterns() -> list[dict]:
    """Pair EN/JP mod templates position-by-position across every MOD_SOURCES
    page. Returns a list of {"en": <lua pattern>, "ja": <replacement>} dicts
    ready for Mods.lua, deduped globally."""
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for path in MOD_SOURCES:
        try:
            en_spans, jp_spans = _harvest_mod_lines(path)
        except requests.HTTPError as e:
            print(f"    ! HTTP {e.response.status_code} on {path} — skipped",
                  file=sys.stderr)
            continue
        except requests.RequestException as e:
            print(f"    ! request failed on {path}: {e}", file=sys.stderr)
            continue
        for en_lines, jp_lines in zip(en_spans, jp_spans):
            if len(en_lines) != len(jp_lines):
                continue
            for en, ja in zip(en_lines, jp_lines):
                if en == ja:
                    continue
                if not re.search(r'[぀-ヿ一-鿿]', ja):
                    continue
                if (en, ja) in seen:
                    continue
                seen.add((en, ja))
                en_pat = _lua_escape_pattern(en)
                for n in range(1, 10):
                    en_pat = en_pat.replace(f'%%{n}', '(%d+)')
                out.append({"en": '^' + en_pat + '$', "ja": ja})
    return out


def write_mods_lua(out_path: Path, patterns: list[dict]) -> None:
    lines = [
        "-- Mod template patterns from poe2db.tw/jp/Modifiers.",
        "-- Auto-generated by tools/scrape_poe2db.py.",
        "-- Each entry's `en` field is a Lua pattern; `ja` may reference %1..%N",
        "-- captures. ModFormat() in Locale.lua falls back to the original on miss.",
        "return {",
        "\tpatterns = {",
    ]
    for p in patterns:
        en = p["en"].replace('\\', '\\\\').replace('"', '\\"')
        ja = p["ja"].replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'\t\t{{ en = "{en}", ja = "{ja}" }},')
    lines.append("\t},")
    lines.append("}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_lua_dict(out_path: Path, mapping: dict[str, str], header: str) -> None:
    lines = [
        f"-- {header}",
        "-- Auto-generated by tools/scrape_poe2db.py. Do not edit by hand;",
        "-- if you need to override an entry, add it under src/Locale/ja_JP/_overrides/",
        "-- (override merge step is run after scrape — see tools/apply_overrides.py).",
        "return {",
    ]
    for en in sorted(mapping):
        ja = mapping[en]
        lines.append(f'\t["{lua_escape(en)}"] = "{lua_escape(ja)}",')
    lines.append("}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Scrape poe2db.tw/jp into Lua dictionaries.")
    parser.add_argument("--only", choices=list(CATEGORIES) + ["Mods"], default=None,
                        help="Scrape one category only (debug).")
    parser.add_argument("--out", default=None,
                        help="Output directory (default: ../src/Locale/ja_JP/ relative to this script).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print stats without writing files.")
    args = parser.parse_args(argv)

    out_dir = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "src" / "Locale" / "ja_JP"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Self-link slugs: the listing page slugs themselves (so we don't re-add them as entries)
    skip_slugs = set()
    for spec in CATEGORIES.values():
        for p in spec["urls"]:
            skip_slugs.add(p.removeprefix("/jp/").rstrip("/"))

    # "Mods" is handled in its own post-loop branch; for the main category loop
    # we just skip it here (it's not in CATEGORIES anyway).
    if args.only and args.only != "Mods":
        categories = {args.only: CATEGORIES[args.only]}
    elif args.only == "Mods":
        categories = {}    # main loop runs zero times; Mods branch executes below
    else:
        categories = CATEGORIES

    total = 0
    for category, spec in categories.items():
        merged: dict[str, str] = {}
        pattern = class_link_re(spec["class_re"]) if spec["class_re"] else PLAIN_LINK_RE
        for path in spec["urls"]:
            cached = path in _FETCH_CACHE
            print(f"  {'CACHE' if cached else 'GET  '} {path}", flush=True)
            try:
                merged.update(scrape_pairs(path, skip_slugs, pattern))
            except requests.HTTPError as e:
                print(f"    ! HTTP {e.response.status_code} — skipped", file=sys.stderr)
            except requests.RequestException as e:
                print(f"    ! request failed: {e}", file=sys.stderr)
            if not cached:
                time.sleep(DELAY)
        out_path = out_dir / f"{category}.lua"
        if not args.dry_run:
            write_lua_dict(out_path, merged, f"{category} dictionary from poe2db.tw/jp/")
        print(f"  -> {out_path.name}: {len(merged)} entries"
              + (" (dry-run, not written)" if args.dry_run else ""))
        total += len(merged)

    print(f"\nDone. {total} entries total across {len(categories)} categor{'y' if len(categories) == 1 else 'ies'}.")

    # Mods are handled separately because their structure (placeholder templates
    # with %N captures, not simple key→value pairs) requires different scraping.
    # Skipped when --only narrows to a specific category.
    if not args.only or args.only == "Mods":
        print("\nScraping mod templates (/us/Modifiers + /jp/Modifiers)...")
        try:
            patterns = scrape_mod_patterns()
        except requests.RequestException as e:
            print(f"  ! failed: {e}", file=sys.stderr)
            patterns = []
        out_path = out_dir / "Mods.lua"
        if not args.dry_run:
            write_mods_lua(out_path, patterns)
        print(f"  -> Mods.lua: {len(patterns)} patterns"
              + (" (dry-run, not written)" if args.dry_run else ""))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
