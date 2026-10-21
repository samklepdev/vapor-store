#!/usr/bin/env bash
# verify-task-1.sh — assert the Task 1 repo scaffold is intact.
#
# Checks the deliverables from docs/plans/2026-10-20-vapor-studio-m0-m1-foundation.md
# Task 1: the pipeline/listings/reports folder skeleton with .gitkeep files,
# README.md, and the .gitignore rules that keep secrets and generated output
# out of version control.
#
# Usage:   ./verify-task-1.sh
# Exit:    0 if the scaffold is intact, 1 if any check fails.

set -uo pipefail

# Run from the repo root regardless of where this is invoked from.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not inside a git repository" >&2
  exit 1
}
cd "$ROOT"

pass=0
fail=0

ok()   { printf '  \033[32mok\033[0m   %s\n' "$1"; pass=$((pass + 1)); }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=$((fail + 1)); }

# A file that must exist on disk.
check_file() {
  if [ -f "$1" ]; then ok "$1 exists"; else bad "$1 missing"; fi
}

# A path git must treat as ignored.
check_ignored() {
  if git check-ignore -q -- "$1"; then ok "ignored: $1"; else bad "NOT ignored: $1"; fi
}

# A path git must NOT treat as ignored (e.g. a .gitkeep under an ignored dir).
check_not_ignored() {
  if git check-ignore -q -- "$1"; then bad "unexpectedly ignored: $1"; else ok "tracked (not ignored): $1"; fi
}

echo "Task 1 scaffold check  (root: $ROOT)"

echo "- folder skeleton (.gitkeep files)"
for k in \
  pipeline/01-briefs/.gitkeep \
  pipeline/02-raw/.gitkeep \
  pipeline/03-contact-sheets/.gitkeep \
  pipeline/04-approved/.gitkeep \
  pipeline/05-packaged/.gitkeep \
  listings/.gitkeep \
  reports/.gitkeep
do
  check_file "$k"
done

echo "- top-level files"
check_file .gitignore
check_file README.md

echo "- .gitignore rules actually fire"
# Secrets / config must be ignored (these paths need not exist on disk).
check_ignored tools/producer/config.toml
check_ignored .env
# Generated output is ignored, but the .gitkeep placeholders are preserved.
check_ignored     pipeline/02-raw/sample.png
check_not_ignored pipeline/02-raw/.gitkeep
check_ignored     pipeline/05-packaged/sample.zip
check_not_ignored pipeline/05-packaged/.gitkeep

echo
echo "Result: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
