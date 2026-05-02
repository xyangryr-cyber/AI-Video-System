# SPEC-A Tests Redo Plan — replace skip stubs with real assertions

> **Owner**: whichever AI picks this up next.
> **Status**: active as of 2026-04-20.
> **Scope**: 11 task IDs with merged implementation but skip-stub tests.
> **Do NOT modify implementation files** unless a real test uncovers a concrete bug.
> This plan supersedes the per-card "completion" marked in earlier PROGRESS.md snapshots.

---

## 1. Problem

`PROGRESS.md` (pre-2026-04-20) listed these 11 SPEC-A tasks as Done, but every
acceptance test in their test file is a single `pytest.skip("NOT IMPLEMENTED -- waiting for [SPEC-A-XXX]")`.
The implementation (Pydantic / JSON Schema / TS / registry / DDL / FastAPI routes)
exists and is referenced throughout the repo; only the tests are missing.

Violates HARNESS §4.2.5 ("Would a stub pass this test?") and user memory
`feedback_acceptance_complete_criteria` + `feedback_stub_test_coverage`.

## 2. Task list (11 tasks, 108 test methods to rewrite)

| Task ID | Title | Test file | Stubs to replace |
|---|---|---|---|
| SPEC-A-001 | Artifact JSON Schemas (requirements, timeline, style_lock) | `tests/unit/contracts/test_spec_a_001.py` | 11 |
| SPEC-A-002 | Candidate & ProjectState Contracts | `tests/unit/contracts/test_spec_a_002.py` | 8 |
| SPEC-A-004 | Cross-Module Shared Type Definitions | `tests/unit/contracts/test_spec_a_004.py` | 11 |
| SPEC-A-007 | SQLite Database Schema DDL (10 Tables) | `tests/unit/contracts/test_spec_a_007.py` | 12 |
| SPEC-A-010 | WebSocket Event Payload Schemas (17 Events) | `tests/unit/contracts/test_spec_a_010.py` | 11 |
| SPEC-A-011 | HTTP Error Code System (SPEC-13A) | `tests/unit/contracts/test_spec_a_011.py` | 8 |
| SPEC-A-014 | SfxLayoutPlan + SfxMixSegments schemas | `tests/unit/contracts/test_spec_a_014.py` | 9 |
| SPEC-A-015 | MaterialManifest + ShotMaterialBindings schemas | `tests/unit/contracts/test_spec_a_015.py` | 9 |
| SPEC-A-016 | ChartMaterial schema (+ axis_spec) | `tests/unit/contracts/test_spec_a_016.py` | 9 |
| SPEC-A-017 | API GET /artifacts/master_audio + phase_7a enum | `tests/unit/contracts/test_spec_a_017.py` | 9 |
| SPEC-A-018 | Error codes render_failed / material_missing / material_unverified + phase.shot_blocked | `tests/unit/contracts/test_spec_a_018.py` | 11 |

Reference template (already real, **do not modify**):
`tests/unit/contracts/test_spec_a_009.py` — the shape every task file should end up looking like.

## 3. Environment setup (one-time per session)

System default `python3` is 3.9 on this machine; project requires ≥3.11.
**Always** use the venv interpreter:

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System
source .venv/bin/activate        # OR prefix every command with .venv/bin/python3
python --version                 # must print 3.11.x
python -m pytest --version       # sanity check
```

Verify required libs load:
```bash
python -c "import jsonschema, pydantic; print(jsonschema.__version__, pydantic.VERSION)"
```

## 4. Pattern library

These are the reusable shapes. Pick the pattern that matches the AC, fill in
the data, adapt. **Every test must have at least one `assert` that would fail
if the implementation were a stub** (HARNESS §4.2.5).

### Pattern A — JSON Schema validate (valid + invalid payload pair)

```python
import json
from pathlib import Path
import jsonschema
import pytest

SCHEMA = json.loads(Path("schemas/requirements.schema.json").read_text())

def test_valid_payload_passes():
    payload = {...}  # complete valid example
    jsonschema.validate(payload, SCHEMA)  # raises if invalid

def test_invalid_payload_rejected():
    payload = {...}  # violate one specific rule, e.g. topic="abc" (<5 chars)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, SCHEMA)
```

### Pattern B — Pydantic round-trip

```python
from src.shared.schemas.artifacts import Requirements

def test_round_trip():
    original = Requirements(project_id="p1", title="T", topic="hello", ...)
    dumped = original.model_dump()
    restored = Requirements.model_validate(dumped)
    assert restored == original
    assert restored.model_dump() == dumped
```

### Pattern C — Pydantic constraint rejection

```python
from pydantic import ValidationError
from src.shared.schemas.artifacts import Requirements

def test_short_topic_rejected():
    with pytest.raises(ValidationError) as exc:
        Requirements(project_id="p1", title="T", topic="hi", ...)
    assert "topic" in str(exc.value).lower()
```

### Pattern D — Registry / enum completeness

```python
from src.shared.schemas.artifact_registry import ARTIFACT_REGISTRY

EXPECTED_CORE_ARTIFACTS = {
    "requirements.json", "outline", "polished_script", "timeline.json",
    "style_lock.json", "keyframe_renders", "rough_cut", "final_cut",
}

def test_registry_covers_all_core_artifacts():
    missing = EXPECTED_CORE_ARTIFACTS - set(ARTIFACT_REGISTRY)
    assert missing == set(), f"Missing registry entries: {missing}"
    for name in EXPECTED_CORE_ARTIFACTS:
        entry = ARTIFACT_REGISTRY[name]
        assert entry.producer, f"{name}: producer empty"
        assert entry.consumers, f"{name}: consumers empty"
        assert entry.validation, f"{name}: validation empty"
```

**Enum completeness variant** (for EventType, ErrorCode, etc.):

```python
EXPECTED_EVENT_TYPES = {"phase.entered", "phase.completed", ...}  # exactly 17

def test_event_type_enum_exactly_17():
    from src.shared.schemas.events import EventType
    actual = {e.value for e in EventType}
    assert actual == EXPECTED_EVENT_TYPES, \
        f"Missing: {EXPECTED_EVENT_TYPES - actual}, Extra: {actual - EXPECTED_EVENT_TYPES}"
```

### Pattern E — TS/Pydantic field parity

```python
import re
from pathlib import Path
from src.shared.schemas.artifacts import Requirements

def _ts_interface_fields(ts_path: Path, interface_name: str) -> set[str]:
    text = ts_path.read_text()
    m = re.search(rf"export interface {interface_name} \{{([^}}]*)\}}", text, re.DOTALL)
    assert m, f"Interface {interface_name} not found in {ts_path}"
    body = m.group(1)
    # Extract field names (strip optional `?:` and type annotation)
    return {
        line.strip().split(":")[0].rstrip("?").strip()
        for line in body.splitlines()
        if line.strip() and not line.strip().startswith("//")
    }

def test_requirements_pydantic_ts_parity():
    py_fields = set(Requirements.model_fields.keys())
    ts_fields = _ts_interface_fields(Path("src/shared/types/artifacts.ts"), "Requirements")
    assert py_fields == ts_fields, \
        f"Py-only: {py_fields - ts_fields}, TS-only: {ts_fields - py_fields}"
```

### Pattern F — Cross-artifact referential integrity

```python
# Every material_id referenced in bindings must exist in the manifest.
def test_bindings_ids_exist_in_manifest():
    manifest = json.loads(...)
    bindings = json.loads(...)
    manifest_ids = {m["material_id"] for m in manifest["materials"]}
    referenced = set()
    for b in bindings["shots"]:
        referenced.update(b.get("required_materials", []))
        referenced.update(b.get("optional_materials", []))
    missing = referenced - manifest_ids
    assert missing == set(), f"Dangling material ids: {missing}"
```

### Pattern G — String-absence scan (no hardcoded literals)

```python
import subprocess

def test_no_hardcoded_error_code_strings_outside_module():
    result = subprocess.run(
        ["rg", "-n", r"EVID_\d{4}", "src/", "--type", "py"],
        capture_output=True, text=True,
    )
    offenders = [
        line for line in result.stdout.splitlines()
        if "src/shared/constants/error_codes" not in line
        and "# test:" not in line
    ]
    assert offenders == [], "EVID codes must be imported, not hardcoded:\n" + "\n".join(offenders)
```

### Pattern H — SQLite DDL load + CHECK constraint probe (for A-007)

```python
import sqlite3, pytest
from pathlib import Path

DDL = Path("src/backend/models/schema.sql").read_text()  # adapt to real path

def _fresh_db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(DDL)
    return conn

def test_projects_status_check_constraint():
    conn = _fresh_db()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO projects(id, title, status) VALUES (?, ?, ?)",
            ("p1", "T", "not_a_valid_status"),
        )
```

### Pattern I — FastAPI route / response-model probe (for A-017)

```python
from fastapi.testclient import TestClient
from src.backend.api.main import app   # adapt import

def test_master_audio_get_phase_validation():
    client = TestClient(app)
    resp = client.get("/artifacts/master_audio?phase=9")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_phase"
```

### Pattern J — Property-based (for A-016 AC-4)

```python
from hypothesis import given, strategies as st
# sample_rate → labels count relationship; see task card A-016 AC-4.
```

(Only A-016 AC-4 calls for Hypothesis. Every other AC can be direct-table tests.)

## 5. Execution protocol per task (TDD discipline)

For each of the 11 tasks, the AI executor does the following **in this order**:

1. **READ** the task card `tasks/SPEC-A/<task>.md` and the current test file.
   Confirm the AC → test-method mapping in the card matches the test class names.
   If the card has drifted from the test file, follow the test file's class
   docstrings (they are the `"""AC-N: ..."""` source of truth).

2. **READ** the implementation files the test will target. Know the exact
   import paths, field names, enum values before writing tests.

3. **FOR EACH test method**:
   a. **RED step** — write the real assertion body. Run:
      ```bash
      python -m pytest tests/unit/contracts/test_spec_a_<NNN>.py::<Class>::<method> -v
      ```
      Either the test fails with a clear assertion error, OR it passes
      immediately. If it passes immediately, you **must** perform a mutation
      sanity check (rename one field, confirm test now fails, revert) before
      accepting GREEN. Record the mutation result in the commit body so the
      reviewer can verify you didn't ship a stub-equivalent.
   b. **GREEN step** — minimal change to make the test pass. Since impl
      already exists, the usual outcome is: the test passes as-written once
      correct. Do **not** modify implementation unless the test legitimately
      uncovers a bug; if it does, branch: open a new `[SPEC-A-<NNN>-fix<k>]`
      commit for the impl change.
   c. **REPEAT** for next test method.

4. **RUN the full task file**:
   ```bash
   python -m pytest tests/unit/contracts/test_spec_a_<NNN>.py -v
   ```
   All tests must pass, zero skips.

5. **COMMIT** per HARNESS §9.3. Commit subject:
   `[SPEC-A-<NNN>-redo] replace skip stubs with real assertions (N tests)`.
   Commit body must include:
   - Files Changed
   - Verification (real pytest -v output, last ~30 lines)
   - Decisions (any AC-to-test reinterpretation, any mutation-test evidence)
   - Artifacts (nothing new, tests only — say so)

6. **APPEND** one row to PROGRESS.md "Recent commits" table with the new SHA,
   task id `SPEC-A-<NNN> (redo)`, title, date.

7. **MOVE** the task in PROGRESS.md "Status snapshot": add it back to the
   Done column of row A; update the reopened-count note.

## 6. Completion gate

Before any of the 11 tasks may be marked Done again, **all of these must pass**:

```bash
# 6.1 No stubs remain in the 11 files
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py

# 6.2 Full contract test suite green (zero skips in the 11 files)
.venv/bin/python3 -m pytest tests/unit/contracts/test_spec_a_001.py \
                                tests/unit/contracts/test_spec_a_002.py \
                                tests/unit/contracts/test_spec_a_004.py \
                                tests/unit/contracts/test_spec_a_007.py \
                                tests/unit/contracts/test_spec_a_010.py \
                                tests/unit/contracts/test_spec_a_011.py \
                                tests/unit/contracts/test_spec_a_014.py \
                                tests/unit/contracts/test_spec_a_015.py \
                                tests/unit/contracts/test_spec_a_016.py \
                                tests/unit/contracts/test_spec_a_017.py \
                                tests/unit/contracts/test_spec_a_018.py \
                                -v

# 6.3 Broader regression check (no other suite broke)
bash scripts/contracts/run_contract_tests.sh
```

## 7. Commit protocol

- One commit per task: `[SPEC-A-<NNN>-redo] ...`. **No bundling.** Reviewer
  needs to see one RED→GREEN cycle per commit for audit (user memory
  `feedback_tdd_audit_trail`).
- Per-file stub counts MUST drop monotonically as commits land; never re-add
  a skip stub.
- **Do not modify** any of these paths while running this plan:
  - `src/shared/schemas/**` (except bugfix branch)
  - `src/shared/types/**` (except bugfix branch)
  - `schemas/*.schema.json` (except bugfix branch)
  - `HARNESS.md`, `CLAUDE.md`, `docs/specs/**`
  - `tests/unit/contracts/test_spec_a_009.py`, `test_spec_a_013.py`
    (already real; leave alone)

## 8. Recommended order

Run in this order (smaller/simpler first to establish the pattern):

1. SPEC-A-001 (Pattern A + B + C + D + E) — canonical schema task.
2. SPEC-A-011 (Pattern D + G) — enum + grep.
3. SPEC-A-010 (Pattern D + A) — event type enum + payload schemas.
4. SPEC-A-002 (Pattern C + D + E) — candidate constraints.
5. SPEC-A-004 (Pattern E + F) — cross-module shared types.
6. SPEC-A-018 (Pattern D + B) — extends A-011 + A-010.
7. SPEC-A-014 (Pattern A + E + F) — SFX dual-layer schemas.
8. SPEC-A-015 (Pattern A + E + F) — material manifest pair.
9. SPEC-A-016 (Pattern A + E + J) — chart material + property-based.
10. SPEC-A-017 (Pattern I + D) — needs FastAPI TestClient.
11. SPEC-A-007 (Pattern H) — SQLite DDL + CHECK constraints. Last because
    DDL loader path may need scouting.

## 9. Known hazards

- **`test_spec_a_007.py` AC-10 timestamp default** uses SQLite
  `strftime(...)` — not portable to `:memory:` without the full DDL loaded.
  Use the actual DDL file, don't reinvent.
- **A-015 AC-5 verification_status state machine** test needs a small helper
  function if one doesn't already exist — prefer asserting the schema
  comment / documented transition rather than simulating a FSM you build
  from scratch.
- **A-016 AC-4 hypothesis** — if `hypothesis` isn't installed, add a plain
  parametrized pytest case with 6-8 hand-picked (granularity, date_range)
  samples and note the deferral in Decisions.
- **Python 3.9 vs 3.11 mismatch** — if a test imports
  `src/backend/startup/ensure_user_dir.py`, that module uses 3.10+ `X | None`
  syntax. Always run via `.venv/bin/python3` (3.11).
- **Skip stubs in non-target files** (A-003/005/006/008/012/100-115) are
  OUT OF SCOPE. Leave them. Their tasks are still unimplemented, so skip is
  correct there.

## 10. Done-ness definition for this plan

This plan is complete when:

- [ ] 11 commits landed, one per task, each titled `[SPEC-A-<NNN>-redo] ...`
- [ ] `scripts/contracts/verify_no_skip_stubs.py` exits 0
- [ ] `bash scripts/contracts/run_contract_tests.sh` exits 0
- [ ] PROGRESS.md Status snapshot row A shows `Done (distinct task IDs)` = 13
- [ ] PROGRESS.md Open follow-up "[REOPENED 2026-04-20] 11 SPEC-A tasks" is
      removed (resolved)

Until all four boxes are ticked, do NOT claim SPEC-A contracts layer is
"done" in any summary.

## Verification Commands

```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_001.py \
  tests/unit/contracts/test_spec_a_002.py \
  tests/unit/contracts/test_spec_a_004.py \
  tests/unit/contracts/test_spec_a_007.py \
  tests/unit/contracts/test_spec_a_010.py \
  tests/unit/contracts/test_spec_a_011.py \
  tests/unit/contracts/test_spec_a_014.py \
  tests/unit/contracts/test_spec_a_015.py \
  tests/unit/contracts/test_spec_a_016.py \
  tests/unit/contracts/test_spec_a_017.py \
  tests/unit/contracts/test_spec_a_018.py -q
.venv/bin/python scripts/contracts/verify_no_skip_stubs.py
bash scripts/contracts/run_contract_tests.sh
```
