# Auto-Commit Workflow

This document describes how to use `commit-task.sh` to ensure every task card
completion is committed AND has its commit SHA reflected in PROGRESS.md, in
one shell invocation.

## Why this exists

HARNESS section 4.1 mandates a `git commit` at the end of every RED-GREEN-
REFACTOR cycle. HARNESS section 9.2 mandates that the PROGRESS.md entry's
`**Commit**:` field contain `<short-sha> <subject>`. In practice these two
steps are often performed by separate invocations, and the second step gets
forgotten -- leaving PROGRESS.md out of sync with git history (e.g.
SPEC-A-009 required four follow-up FIX commits to reach a consistent state).

`commit-task.sh` collapses the two steps into one operation.

## Usage

From the repo root:

```bash
# 1. Stage the task's allowed_files (per the task card and HARNESS section 1.1).
git add src/shared/constants/auth.py \
        src/backend/startup/ensure_user_dir.py \
        tests/unit/contracts/test_auth_model.py \
        PROGRESS.md

# 2. Invoke the helper:
./commit-task.sh SPEC-A-009 "define DEFAULT_USER_ID and ensure_user_dir startup"
```

That single invocation produces two commits:

```
abcd123 [SPEC-A-009] define DEFAULT_USER_ID and ensure_user_dir startup
ef45678 [SPEC-A-009] backfill PROGRESS commit SHA -> abcd123
```

## What it does

1. Confirms something is staged (refuses to run with an empty index).
2. Creates the task commit `[<task_id>] <subject>`.
3. Captures the short SHA.
4. Finds the entry titled `## [<task_id>]` in PROGRESS.md.
5. Replaces that entry's `- **Commit**:` placeholder
   (`pending`, `(see below)`, `TBD`, or empty) with
   `<short-sha> [<task_id>] <subject>`.
6. Creates a second commit recording the PROGRESS backfill.

## Why two commits, not one with `--amend`

A git commit's SHA is a hash of its tree and parent -- it cannot contain
itself. To put a commit's SHA into PROGRESS.md, the commit must already
exist. Using `git commit --amend` after backfilling would change the SHA
again, immediately invalidating what was just written into PROGRESS.md.
Two commits is the only construction that converges.

## Pre-conditions

- Run from the repo root (script reads `PROGRESS.md` from `$PWD`).
- The task card's `allowed_files` are already staged via `git add`.
- PROGRESS.md contains an entry `## [<task_id>]` whose Commit field is one of:
  `pending`, `(see below)`, `TBD`, or blank.
- Verification commands from the task card have already passed (this script
  does NOT run them -- HARNESS section 9.3.3 requires real verification
  output before marking DONE).

## What it does NOT do

- Does NOT run `git add -A`. You decide what enters the commit -- this
  prevents accidental staging of forbidden files (HARNESS section 1.2) or
  unrelated in-flight work.
- Does NOT push. Local commits only.
- Does NOT run tests, lints, or any verification.
- Does NOT modify the task card or any file other than PROGRESS.md.

## Failure modes

- **Nothing staged**: script exits 1 with a message. Stage files and retry.
- **No PROGRESS entry for task_id**: script logs a note and exits after
  the task commit, without a second commit. Add the PROGRESS entry, then
  manually backfill or re-run the relevant section.
- **No placeholder Commit field**: same as above -- task commit succeeds,
  backfill is skipped with a note.

## Integration with the dev loop (HARNESS section 4.4)

```
Pick task card
  -> Read allowed_files / acceptance_criteria
  -> Write failing test (RED)
  -> Implement minimum code (GREEN)
  -> Refactor (REFACTOR)
  -> Run verification_commands from task card
  -> Append PROGRESS.md entry with Commit field set to `pending`
  -> git add <allowed_files> PROGRESS.md
  -> ./commit-task.sh <task_id> "<subject>"   <-- this script
  -> Pick next task card
```
