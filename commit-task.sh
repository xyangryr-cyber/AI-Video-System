#!/usr/bin/env bash
# commit-task.sh -- automated task commit + PROGRESS.md SHA backfill.
#
# Usage:
#   ./commit-task.sh <task_id> "<subject>"
#
# Behavior:
#   1. Commits the files YOU have already `git add`-ed, with message
#      "[<task_id>] <subject>" (HARNESS section 3.2 format).
#   2. Locates the entry "## [<task_id>]" in PROGRESS.md and replaces the
#      "- **Commit**:" line whose value is `pending`, `(see below)`, `TBD`,
#      or empty with "<short-sha> [<task_id>] <subject>" (HARNESS section
#      9.2 template).
#   3. Creates a SECOND commit recording the PROGRESS backfill.
#
# Why two commits:
#   Git commit SHAs are content-addressed: a commit cannot contain its own
#   SHA. The two-commit model lets PROGRESS.md stay append-only (HARNESS
#   section 9.3.1) while keeping it synchronized with git history.
#
# Pre-conditions:
#   - Run from repo root.
#   - You have already `git add`-ed the task's allowed_files.
#   - PROGRESS.md has a "## [<task_id>]" entry with a Commit-field
#     placeholder (`pending`, `(see below)`, `TBD`, or blank).
#
# Non-goals:
#   - Does NOT run `git add -A`. You stage what you want.
#   - Does NOT push.
#   - Does NOT run verification commands -- do those first.

set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <task_id> '<subject>'" >&2
  echo "Example: $0 SPEC-A-010 'add session token storage'" >&2
  exit 1
fi

TASK_ID="$1"
SUBJECT="$2"

if git diff --cached --quiet; then
  echo "Error: nothing is staged. Run 'git add <files>' first." >&2
  exit 1
fi

# Step 1: create the task commit.
git commit -m "[${TASK_ID}] ${SUBJECT}"
SHA=$(git rev-parse --short HEAD)
echo "Task commit: ${SHA} [${TASK_ID}] ${SUBJECT}"

# Step 2: backfill PROGRESS.md.
PROGRESS="PROGRESS.md"
if [ ! -f "$PROGRESS" ]; then
  echo "Note: no PROGRESS.md at repo root -- skipping backfill." >&2
  exit 0
fi

python3 - "$PROGRESS" "$TASK_ID" "$SHA" "$SUBJECT" <<'PY'
import re
import sys

path, task_id, sha, subject = sys.argv[1:]
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

header_re = re.compile(rf'^## \[{re.escape(task_id)}\][^\n]*$', re.MULTILINE)
m = header_re.search(text)
if not m:
    sys.stderr.write(f"Note: no PROGRESS entry titled '## [{task_id}]' -- skipping backfill.\n")
    sys.exit(0)

start = m.end()
next_header = re.search(r'^## \[', text[start:], re.MULTILINE)
end = start + (next_header.start() if next_header else len(text) - start)
section = text[start:end]

commit_re = re.compile(
    r'^- \*\*Commit\*\*: (pending|\(see below\)|TBD)?\s*$',
    re.MULTILINE,
)
new_section, n = commit_re.subn(
    f'- **Commit**: {sha} [{task_id}] {subject}',
    section,
    count=1,
)
if n == 0:
    sys.stderr.write(
        "Note: no placeholder Commit field "
        "(pending|(see below)|TBD|empty) found in entry -- skipping backfill.\n"
    )
    sys.exit(0)

with open(path, "w", encoding="utf-8") as f:
    f.write(text[:start] + new_section + text[end:])
print(f"Backfilled PROGRESS.md: ## [{task_id}] -> Commit {sha}")
PY

# Step 3: second commit for the backfill (only if PROGRESS.md actually changed).
if git diff --quiet -- "$PROGRESS"; then
  echo "PROGRESS.md unchanged (no placeholder to backfill)."
  exit 0
fi

git add "$PROGRESS"
git commit -m "[${TASK_ID}] backfill PROGRESS commit SHA -> ${SHA}"
BACKFILL_SHA=$(git rev-parse --short HEAD)
echo "Backfill commit: ${BACKFILL_SHA} [${TASK_ID}] backfill PROGRESS commit SHA -> ${SHA}"
