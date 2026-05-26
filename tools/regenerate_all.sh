#!/usr/bin/env bash
# One-stop regeneration: scrape poe2db, wrap UI calls, refresh translation queue,
# then print coverage. Safe to run after every upstream sync.
#
# Usage:
#   tools/regenerate_all.sh         # full run (writes everything)
#   tools/regenerate_all.sh --dry   # dry-run preview only

set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-apply}"

step() { printf '\n\033[1;36m── %s ──\033[0m\n' "$*"; }

step "1/4  Scrape poe2db.tw → dictionaries"
if [ "$MODE" = "--dry" ]; then
  python3 tools/scrape_poe2db.py --dry-run
else
  python3 tools/scrape_poe2db.py
fi

step "2/4  Auto-wrap new UI call sites with T()/StatT()/..."
if [ "$MODE" = "--dry" ]; then
  python3 tools/wrap_ui_calls.py --dry-run
else
  python3 tools/wrap_ui_calls.py
fi

step "3/4  Refresh UI translation queue"
if [ "$MODE" = "--dry" ]; then
  python3 tools/extract_strings.py --dry-run
else
  python3 tools/extract_strings.py
fi

step "4/4  Coverage report"
python3 tools/coverage_report.py

if [ "$MODE" != "--dry" ]; then
  printf '\n\033[1;32mDone. Review with: git diff --stat\033[0m\n'
fi
