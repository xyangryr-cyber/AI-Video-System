# Prototype (Read-Only Snapshot)

Source: `/Users/xyangryr/Downloads/ai-video (1)/` — Google AI Studio export, snapshot taken 2026-04-17.

## Rules

1. This tree is the **UI/UX truth** for `src/frontend/**`. Visual + interaction parity is verified by tests (Playwright snapshot, vitest + jest-image-snapshot).
2. **Forbidden:** `src/frontend/**` MUST NOT `import` from `prototype/**`. Enforced by ESLint `no-restricted-imports` and by `madge --circular` rules.
3. **Commit prefix:** `[PROTO] <description>` (snapshot refresh only). HARNESS §1.2 / §3.2 register this exemption.
4. **No SPEC-X-NNN task card** governs files under `prototype/`. To refresh the snapshot, re-run the rsync from Task 5 and commit with `[PROTO] refresh from <source-path> <date>`.
5. Contract deltas surfaced by this prototype are tracked in `docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md` and reflowed into SPEC-A.

## Index

See `PROTOTYPE_INDEX.md` (Wave 1, Task 13) for the per-component map to SPEC-E task cards and contract delta tags.
