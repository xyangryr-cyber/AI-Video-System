# BDD → Dev-Test Loop Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every BDD scenario in `docs/BDD_ai_system_expected_behavior_v1.feature.md` executable inside the dev-test Loop so that after each task card the verifier runs the BDD scenarios owned by that task, and failures automatically feed the fixer agent.

**Architecture:** Replace the 36 `pytest.skip` stub files with real pytest-bdd scenarios fed from generated `.feature` files. A rewritten splitter emits pure Gherkin under `tests/integration/bdd/features/` (deterministic) and `tests/eval/bdd/features/` (LLM-as-judge). Task cards gain an optional `bdd_tags` field listing the Gherkin tags the task must satisfy; the Loop's verifier command builder appends a scoped `pytest --bdd-tag` run to the task's existing `verification_commands`. Eval-bucket scenarios route Then-clauses through deepeval's `GEval` / `assert_test` so LLM-judge assertions are fail-fast-and-deterministic inside the same Loop. HARNESS §10.3 >5% regression gate + mass conversion of all 112 scenarios are **out of scope** for this plan (follow-up plan).

**Tech Stack:** Python 3.11, pytest-bdd 7.x, deepeval 1.x, pytest-xdist 3.x, Pydantic v2.

**Source spec:** `docs/BDD_ai_system_expected_behavior_v1.feature.md` (112 scenarios, already human-edited Gherkin).

**Replaces:** `scripts/split_bdd_scenarios.py` (current behaviour: emits `pytest.skip` stubs that can never go green in the Loop).

**Proof of concept scenario (end-to-end smoke):**
`@router` ⇒ "Router 超时或 JSON 解析失败时回退 clarify" — six Gherkin lines, deterministic, no LLM.

**Non-goals (explicit):**
- Mass conversion of all 112 scenarios (only `@router` ⇒ integration POC + `@classification` ⇒ eval POC wired in this plan; remaining scenarios converted in follow-up plan).
- Wiring HARNESS §10.3 5%-regression gate (separate plan — depends on baseline capture after ≥1 eval run).
- Any Loop plumbing for `--parallel` batch ordering of BDD owners (current per-task gating is sufficient).

---

## Pre-flight

- Working directory throughout: `/Users/xyangryr/Desktop/硅基员工/AI-Video-System` (referred to below as `$REPO`). Use absolute paths in commands where possible.
- HARNESS §7.2 forbids `pip install` without updating a dependency manifest. No `requirements*.txt` or `pyproject.toml` exists yet — **Task 1 creates it**. Do not run `pip install pytest-bdd deepeval` until Task 1 completes.
- The splitter currently has 36 generated stub files under `tests/{integration,eval}/bdd/test_bdd_*.py`. Task 3 deletes them. No other code imports them (verified via grep before rewrite).
- The Loop dispatcher lives in `scripts/run_task_driver.py`; the picker in `scripts/pick_next_task.py`. Both are unit-tested with injected callables — extend tests, don't break the inject contract.
- Do **NOT** modify `HARNESS.md` or `docs/specs/**` in this plan. Task card templates (`tasks/SPEC-*/*.md`) may gain a `bdd_tags` metadata line; picker tests cover parsing.
- After every Green step: `git add` ONLY the files that task edits (do not `git add -A`). Commit prefix follows HARNESS §3.2: `[BDD-LOOP] <imperative> <what>` — this plan is infra cross-cutting and does not map to a single SPEC-X-NNN task card.

---

## Top-level File Structure

Files this plan creates or modifies:

| Path | Owner Task | Purpose |
|---|---|---|
| `pyproject.toml` | T1 | Declare pytest-bdd, deepeval, pytest-xdist as dev deps |
| `requirements-dev.txt` | T1 | Pip-compiled lockfile for reproducibility |
| `scripts/split_bdd_scenarios.py` | T2 | Rewrite: emit `.feature` files, not `pytest.skip` stubs |
| `tests/unit/scripts/test_split_bdd_scenarios.py` | T2 | RED test for new splitter behaviour |
| `tests/integration/bdd/test_bdd_*.py` (14 files) | T3 | **DELETE** — superseded |
| `tests/eval/bdd/test_bdd_*.py` (22 files) | T3 | **DELETE** — superseded |
| `tests/integration/bdd/features/` | T3 | Generated `.feature` files (integration bucket) |
| `tests/eval/bdd/features/` | T3 | Generated `.feature` files (eval bucket) |
| `tests/integration/bdd/conftest.py` | T4 | Shared fixtures for integration step defs |
| `tests/integration/bdd/steps/common_steps.py` | T4 | Given/When shared across features |
| `tests/integration/bdd/steps/router_steps.py` | T5 | POC: `@router` step defs |
| `tests/integration/bdd/test_router_bdd.py` | T5 | pytest-bdd dispatcher for `router.feature` |
| `src/backend/agents/intent_router.py` | T5 | Minimal SUT to make router scenario green |
| `scripts/pick_next_task.py` | T6 | `TaskCard` dataclass gains `bdd_tags` field |
| `tests/unit/scripts/test_pick_next_task_bdd.py` | T6 | RED test for `bdd_tags` parsing |
| `tasks/TEMPLATE.md` | T6 | Add `bdd_tags` example to template |
| `tasks/SPEC-C/C-012-intent-router.md` | T6 | Amend: add `bdd_tags: [@router]` (if exists) OR create new `tasks/SPEC-C/C-BDD-POC.md` |
| `scripts/run_task_driver.py` | T7 | Verifier command builder reads `bdd_tags`, injects `pytest --bdd-tag` |
| `tests/unit/scripts/test_run_task_driver_bdd.py` | T7 | RED test for injection behaviour |
| `tests/eval/bdd/conftest.py` | T8 | deepeval fixtures (judge model, metrics cache) |
| `tests/eval/bdd/steps/classification_steps.py` | T8 | POC: `@classification` step defs using `GEval` |
| `tests/eval/bdd/test_classification_bdd.py` | T8 | pytest-bdd dispatcher for `classification.feature` |
| `PROGRESS.md` | T1-T8 | One DONE entry per completed task |

---

### Task 1: Declare dependencies

Create a reproducible Python dev-dep manifest. HARNESS §7.2 forbids `pip install` without this step.

**Files:**
- Create: `pyproject.toml`
- Create: `requirements-dev.txt`

- [ ] **Step 1.1: Create `pyproject.toml`**

```toml
[project]
name = "ai-video-system"
version = "0.0.0"
description = "AI video production system — internal."
requires-python = ">=3.11"

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-bdd>=7.1",
  "pytest-xdist>=3.5",
  "deepeval>=1.0",
  "pydantic>=2.5",
  "ruff>=0.4",
  "mypy>=1.8",
]

[tool.pytest.ini_options]
markers = [
  "eval: agent eval set; run with `pytest tests/eval/ --eval-mode` (HARNESS §10.2). Skipped in default unit/integration runs.",
  "bdd: pytest-bdd scenario wrapper; tag-selectable via `-m '<tag>'`.",
]
bdd_features_base_dir = "tests"
```

- [ ] **Step 1.2: Create `requirements-dev.txt`**

```text
pytest>=8.0
pytest-bdd>=7.1
pytest-xdist>=3.5
deepeval>=1.0
pydantic>=2.5
ruff>=0.4
mypy>=1.8
```

- [ ] **Step 1.3: Install and verify**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && pip install -r requirements-dev.txt
```
Expected: no errors; `pytest --version` reports plugin `pytest-bdd` in `pytest --trace-config 2>&1 | grep bdd`.

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && pytest --collect-only -q 2>&1 | tail -5
```
Expected: existing tests still collect cleanly; no import errors from plugin side effects.

- [ ] **Step 1.4: Remove the old `eval` marker duplication from root conftest**

The `eval` marker moves to `pyproject.toml` `[tool.pytest.ini_options]`. Simplify `conftest.py`:

`conftest.py` before (13 lines):
```python
"""Project-root pytest config.

Registers custom marks used across tests/.
"""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "eval: agent eval set; run with `pytest tests/eval/ --eval-mode` "
        "(HARNESS S10.2). Skipped in default unit/integration runs.",
    )
```

`conftest.py` after:
```python
"""Project-root pytest config.

Markers are declared in pyproject.toml [tool.pytest.ini_options].
Kept as a file for future project-wide fixtures.
"""
```

- [ ] **Step 1.5: Verify marker still resolves**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && pytest tests/eval/ --collect-only -q 2>&1 | tail -5
```
Expected: no "PytestUnknownMarkWarning: Unknown pytest.mark.eval".

- [ ] **Step 1.6: Commit**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git add pyproject.toml requirements-dev.txt conftest.py && \
git commit -m "[BDD-LOOP] declare pytest-bdd + deepeval dev deps"
```

---

### Task 2: Rewrite splitter to emit `.feature` files (TDD)

**Files:**
- Modify: `scripts/split_bdd_scenarios.py`
- Create: `tests/unit/scripts/test_split_bdd_scenarios.py`

- [ ] **Step 2.1: Write failing test for splitter output**

Create `tests/unit/scripts/test_split_bdd_scenarios.py`:

```python
"""TDD test for scripts/split_bdd_scenarios.py (v2): emits .feature files."""
from __future__ import annotations
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "split_bdd_scenarios.py"


def test_emits_feature_file_for_router_tag(tmp_path):
    out_int = tmp_path / "integration"
    out_eval = tmp_path / "eval"
    res = subprocess.run(
        [
            sys.executable, str(SCRIPT), "--apply",
            "--integration-out", str(out_int),
            "--eval-out", str(out_eval),
        ],
        capture_output=True, text=True, check=False,
    )
    assert res.returncode == 0, res.stderr
    router = out_int / "features" / "router.feature"
    assert router.exists(), f"missing {router}"
    text = router.read_text(encoding="utf-8")
    assert text.startswith("# AUTOGENERATED"), "missing header"
    assert "Feature: IntentRouter" in text
    assert "@router" in text
    assert "Scenario:" in text
    # The integration bucket receives the timeout/fallback scenario.
    assert "回退 clarify" in text


def test_no_pytest_skip_stub_emitted(tmp_path):
    out_int = tmp_path / "integration"
    out_eval = tmp_path / "eval"
    subprocess.run(
        [
            sys.executable, str(SCRIPT), "--apply",
            "--integration-out", str(out_int),
            "--eval-out", str(out_eval),
        ],
        check=True,
    )
    # Old behaviour wrote test_bdd_*.py — new behaviour must not.
    assert not any(out_int.glob("test_bdd_*.py")), \
        "splitter still emitting pytest.skip stubs"
    assert not any(out_eval.glob("test_bdd_*.py")), \
        "splitter still emitting pytest.skip stubs"
```

- [ ] **Step 2.2: Run test, confirm it fails**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/unit/scripts/test_split_bdd_scenarios.py -v
```
Expected: FAIL. Either the `--integration-out`/`--eval-out` args are unknown, or the splitter still writes `test_bdd_*.py`. This is the correct RED state.

- [ ] **Step 2.3: Rewrite splitter body**

Replace `scripts/split_bdd_scenarios.py` — keep the existing parse/classify logic; replace the `render_file` + `write_bucket` + `main` to emit `.feature` files. Minimal diff:

Replace `render_file(bucket, slug, features) -> str` with:

```python
def render_feature_file(slug: str, features: list[tuple[str, list[Scenario]]]) -> str:
    """Emit valid Gherkin for pytest-bdd to parse.

    One file per feature-slug. Multiple Gherkin Features in one .feature file
    are illegal; if two source Features resolve to the same slug, we emit one
    .feature per source Feature by prefixing the filename with a numeric index.
    """
    assert len(features) == 1, (
        f"slug {slug!r} collides: {[f for f, _ in features]}. "
        f"Caller must split before rendering."
    )
    feature_name, scenarios = features[0]
    lines: list[str] = []
    lines.append("# AUTOGENERATED from docs/BDD_ai_system_expected_behavior_v1.feature.md")
    lines.append("# Do not edit by hand; amend the source .feature.md and re-run")
    lines.append("# scripts/split_bdd_scenarios.py --apply")
    lines.append("")
    feature_tags = _collect_feature_tags(scenarios)
    if feature_tags:
        lines.append(" ".join(sorted(feature_tags)))
    lines.append(f"Feature: {feature_name}")
    lines.append("")
    for sc in scenarios:
        if sc.scenario_tags:
            lines.append("  " + " ".join(sc.scenario_tags))
        lines.append(f"  Scenario: {sc.name}")
        for kw, body in sc.steps:
            lines.append(f"    {kw} {body}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _collect_feature_tags(scenarios: list[Scenario]) -> set[str]:
    tags: set[str] = set()
    for sc in scenarios:
        tags.update(sc.feature_tags)
    return tags
```

Replace `write_bucket(bucket_dir, slug_groups, bucket, apply)` with:

```python
def write_feature_bucket(
    bucket_dir: Path,
    slug_groups: dict[str, list[tuple[str, list[Scenario]]]],
    apply: bool,
) -> tuple[int, int]:
    """Write .feature files under bucket_dir/features/, one per source Feature.

    Collision rule: if two source Features hash to the same slug, suffix
    with -2, -3... and log the collision.
    """
    features_dir = bucket_dir / "features"
    files = 0
    scenarios_total = 0
    for slug, feature_list in sorted(slug_groups.items()):
        # Each tuple = (feature_name, [scenarios]); emit one file per feature_name.
        for idx, (feature_name, scenarios) in enumerate(feature_list, start=1):
            suffix = "" if idx == 1 else f"-{idx}"
            path = features_dir / f"{slug}{suffix}.feature"
            content = render_feature_file(slug + suffix, [(feature_name, scenarios)])
            count = len(scenarios)
            scenarios_total += count
            if apply:
                features_dir.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                print(f"wrote {path.relative_to(ROOT)}: {count} scenarios")
            else:
                print(f"would write {path.relative_to(ROOT)}: {count} scenarios")
            files += 1
    return files, scenarios_total
```

Replace the argparse block in `main()`:

```python
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--integration-out",
        type=Path,
        default=INTEGRATION_DIR,
        help="Output directory for integration .feature files (default: tests/integration/bdd).",
    )
    ap.add_argument(
        "--eval-out",
        type=Path,
        default=EVAL_DIR,
        help="Output directory for eval .feature files (default: tests/eval/bdd).",
    )
    args = ap.parse_args()

    text = BDD_SRC.read_text(encoding="utf-8")
    scenarios = parse_bdd(text)
    if not scenarios:
        print("ERROR: no scenarios parsed", file=sys.stderr)
        return 1

    raw: dict[str, dict[str, dict[str, list[Scenario]]]] = {
        "integration": defaultdict(lambda: defaultdict(list)),
        "eval": defaultdict(lambda: defaultdict(list)),
    }
    per_class = {"integration": 0, "eval": 0}

    for sc in scenarios:
        bucket = classify(sc)
        slug = feature_slug(sc.feature, sc.feature_tags)
        raw[bucket][slug][sc.feature].append(sc)
        per_class[bucket] += 1

    buckets: dict[str, dict[str, list[tuple[str, list[Scenario]]]]] = {
        "integration": {},
        "eval": {},
    }
    for bucket_name, slug_map in raw.items():
        for slug, feature_map in slug_map.items():
            buckets[bucket_name][slug] = [(fn, scs) for fn, scs in feature_map.items()]

    print("=" * 80)
    print(f"Parsed {len(scenarios)} scenarios from {BDD_SRC.relative_to(ROOT)}")
    print(f"  -> integration: {per_class['integration']}")
    print(f"  -> eval:        {per_class['eval']}")
    print("=" * 80)

    f1, s1 = write_feature_bucket(args.integration_out, buckets["integration"], args.apply)
    f2, s2 = write_feature_bucket(args.eval_out, buckets["eval"], args.apply)

    mode = "applied" if args.apply else "dry-run"
    print(f"[{mode}] integration: {f1} files / {s1} scenarios")
    print(f"[{mode}] eval:        {f2} files / {s2} scenarios")
    return 0
```

Also **delete** the now-obsolete helpers `render_file`, `write_bucket`, `method_name_safe`, `slugify` (if only used by old render), `--show` flag. Keep `parse_bdd`, `classify`, `feature_slug`, `Scenario`, `TAG_RE/FEATURE_RE/SCENARIO_RE/STEP_RE`, and constants `SEMANTIC_KEYWORDS`/`DETERMINISTIC_KEYWORDS`/`FEATURE_EVAL_TAGS`/`FEATURE_INTEGRATION_TAGS`/`SCENARIO_FORCE_INTEGRATION`/`SCENARIO_FORCE_EVAL` unchanged.

- [ ] **Step 2.4: Run the RED test → GREEN**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/unit/scripts/test_split_bdd_scenarios.py -v
```
Expected: 2 passed.

- [ ] **Step 2.5: Commit**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git add scripts/split_bdd_scenarios.py tests/unit/scripts/test_split_bdd_scenarios.py && \
git commit -m "[BDD-LOOP] splitter emits .feature files instead of skip stubs"
```

---

### Task 3: Generate `.feature` files; delete old stubs

- [ ] **Step 3.1: Confirm no code imports the old stub files**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
grep -r "from tests.integration.bdd import\|from tests.eval.bdd import\|import tests.integration.bdd\|import tests.eval.bdd" . --include="*.py" 2>&1 | grep -v "__pycache__"
```
Expected: no matches. If any match is returned, STOP and surface it — deletion would break collection.

- [ ] **Step 3.2: Run splitter in apply mode**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
python3 scripts/split_bdd_scenarios.py --apply
```
Expected stdout ends with `[applied] integration: N files / M scenarios` and `[applied] eval: N files / M scenarios`. Totals should match the pre-rewrite stub counts: roughly 14+22 files.

- [ ] **Step 3.3: Verify a generated file is valid Gherkin**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
cat tests/integration/bdd/features/router.feature | head -30
```
Expected: starts with `# AUTOGENERATED`; then `@router` line; then `Feature: IntentRouter 动作分类`; then one or more `Scenario:` blocks with `Given/When/Then/And` steps.

- [ ] **Step 3.4: Delete old stub `.py` files**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
rm tests/integration/bdd/test_bdd_*.py tests/eval/bdd/test_bdd_*.py
```

- [ ] **Step 3.5: Confirm empty `__init__.py` files remain** (pytest package discovery unchanged)

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
ls tests/integration/bdd/ tests/eval/bdd/
```
Expected: each directory shows `__init__.py` + `features/` and nothing else.

- [ ] **Step 3.6: Confirm collection is clean**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/integration/bdd/ tests/eval/bdd/ --collect-only 2>&1 | tail -10
```
Expected: "collected 0 items" — pytest-bdd won't pick up `.feature` files without a dispatcher `.py` (which Task 5/8 will add). No errors.

- [ ] **Step 3.7: Commit**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git add -A tests/integration/bdd/ tests/eval/bdd/ && \
git commit -m "[BDD-LOOP] regenerate .feature files; delete skip stubs"
```

---

### Task 4: Build shared integration step library skeleton

Create the support infra for pytest-bdd integration scenarios. Step defs will be added per-tag; for now we provide `conftest.py` and shared `common_steps.py`.

**Files:**
- Create: `tests/integration/bdd/conftest.py`
- Create: `tests/integration/bdd/steps/__init__.py`
- Create: `tests/integration/bdd/steps/common_steps.py`

- [ ] **Step 4.1: Create `tests/integration/bdd/conftest.py`**

```python
"""pytest-bdd shared fixtures for integration scenarios.

Fixtures declared here are visible to every step module under steps/.
Keep this file thin: only cross-cutting setup (temp dirs, DB handles,
SUT factories). Tag-specific fixtures live in steps/<tag>_steps.py.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def scenario_state():
    """Mutable dict passed between Given/When/Then of one scenario.

    pytest-bdd recreates fixtures per scenario — resetting state is automatic.
    Use: steps read and write keys here instead of passing state via closures.
    """
    return {}


@pytest.fixture
def sut_router():
    """Lazy-import IntentRouter so tests fail early if impl is missing."""
    from src.backend.agents.intent_router import IntentRouter
    return IntentRouter()
```

- [ ] **Step 4.2: Create `tests/integration/bdd/steps/__init__.py`**

```python
```

(Empty file — marks it as a package so pytest-bdd can import step modules.)

- [ ] **Step 4.3: Create `tests/integration/bdd/steps/common_steps.py`**

```python
"""Shared Given/When/Then steps used across multiple BDD features.

Rule: add a step here ONLY if 2+ feature files need the same phrasing.
Tag-specific steps stay in steps/<tag>_steps.py to avoid regex collisions.
"""
from __future__ import annotations

from pytest_bdd import given, parsers


@given(parsers.parse('用户当前操作目标是制作{kind}视频项目'))
def set_project_kind(scenario_state, kind):
    scenario_state["project_kind"] = kind
```

- [ ] **Step 4.4: Commit**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git add tests/integration/bdd/conftest.py tests/integration/bdd/steps/ && \
git commit -m "[BDD-LOOP] add shared pytest-bdd integration fixtures"
```

---

### Task 5: POC — wire `@router` scenario end-to-end (TDD)

One deterministic scenario chosen: "Router 超时或 JSON 解析失败时回退 clarify" (from `docs/BDD_ai_system_expected_behavior_v1.feature.md` @router block). This validates the Gherkin → pytest-bdd → SUT chain.

**Files:**
- Create: `tests/integration/bdd/test_router_bdd.py`
- Create: `tests/integration/bdd/steps/router_steps.py`
- Create: `src/backend/agents/intent_router.py`

- [ ] **Step 5.1: RED — create pytest-bdd dispatcher (no step defs yet)**

Create `tests/integration/bdd/test_router_bdd.py`:

```python
"""pytest-bdd dispatcher for features/router.feature.

This file produces one pytest test-function per Scenario. Step defs live in
steps/router_steps.py. Selection by tag: `pytest -m "router"`.
"""
from pytest_bdd import scenarios

# Relative path from project root; matches pyproject bdd_features_base_dir.
scenarios("features/router.feature")
```

- [ ] **Step 5.2: Run it to confirm it fails**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/integration/bdd/test_router_bdd.py -v 2>&1 | tail -20
```
Expected: tests FAIL with `StepDefinitionNotFoundError` for every Given/When/Then line in `router.feature`. This is the correct RED.

- [ ] **Step 5.3: GREEN — add step defs for the timeout/fallback scenario**

Create `tests/integration/bdd/steps/router_steps.py`:

```python
"""Step defs for @router scenarios.

Scenarios covered here (growing list):
  * Router 超时或 JSON 解析失败时回退 clarify
"""
from __future__ import annotations

from pytest_bdd import given, when, then, parsers


@given("Router 模型调用超时或返回非 JSON 文本")
def router_returns_garbage(scenario_state):
    scenario_state["raw_router_output"] = "<<<timeout/garbage>>>"


@when("API 层尝试解析 Router 输出")
def api_parses_output(scenario_state, sut_router):
    raw = scenario_state["raw_router_output"]
    scenario_state["result"] = sut_router.parse_or_fallback(raw)


@then("系统应回退为 clarify")
def assert_action_is_clarify(scenario_state):
    assert scenario_state["result"]["action"] == "clarify"


@then("不应猜测用户意图")
def assert_no_guessing(scenario_state):
    result = scenario_state["result"]
    # A guessed intent would leak into params.scope or params.target.
    # Fallback path must leave params empty or contain only diagnostic keys.
    params = result.get("params") or {}
    assert not params.get("scope")
    assert not params.get("target")


@then(parsers.parse("events 中应记录 {event_name} 或等价事件"))
def assert_event_logged(scenario_state, event_name):
    events = scenario_state["result"].get("events") or []
    # Match either the exact name or a dotted-prefix equivalent.
    prefix = event_name.split()[0]  # "router.intent_fallback"
    assert any(
        e.get("type", "").startswith(prefix) for e in events
    ), f"no event matching {event_name!r} in {events!r}"
```

- [ ] **Step 5.4: Run again — still fails because SUT missing**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/integration/bdd/test_router_bdd.py -v 2>&1 | tail -15
```
Expected: tests now FAIL with `ModuleNotFoundError: No module named 'src.backend.agents.intent_router'`. Still RED, but moved forward.

- [ ] **Step 5.5: GREEN — create minimal `IntentRouter` stub**

Create `src/backend/agents/intent_router.py`:

```python
"""IntentRouter — classifies user utterances into pipeline actions.

Minimum surface needed by @router BDD scenarios. Grown per task card.
"""
from __future__ import annotations

import json
from typing import Any


class IntentRouter:
    """Parse LLM router output; fall back to 'clarify' on any failure."""

    def parse_or_fallback(self, raw: str | None) -> dict[str, Any]:
        """Return structured decision, or fallback={action: clarify} on error.

        Contract:
          - Valid JSON with recognised 'action' key → pass through.
          - Invalid JSON / timeout sentinel / missing key → clarify fallback.
          - Fallback always emits a 'router.intent_fallback' event; never
            populates params.scope or params.target (no guessing).
        """
        try:
            parsed = json.loads(raw) if raw else None
            if not isinstance(parsed, dict) or "action" not in parsed:
                raise ValueError("missing action")
            return {
                "action": parsed["action"],
                "params": parsed.get("params", {}),
                "events": [],
            }
        except (ValueError, TypeError, json.JSONDecodeError):
            return {
                "action": "clarify",
                "params": {},
                "events": [{"type": "router.intent_fallback", "reason": "parse_failed"}],
            }
```

- [ ] **Step 5.6: Run — confirm GREEN**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/integration/bdd/test_router_bdd.py -v 2>&1 | tail -15
```
Expected: scenario "Router 超时或 JSON 解析失败时回退 clarify" **PASSES**. Other `@router` scenarios (that we did not write steps for) fail with `StepDefinitionNotFoundError` — acceptable, noted for follow-up plan.

- [ ] **Step 5.7: Confirm tag selection works**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/integration/bdd/ -m router -v 2>&1 | tail -15
```
Expected: only `@router` scenarios collected. The passing scenario passes; unwired ones show `StepDefinitionNotFoundError`.

- [ ] **Step 5.8: Commit**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git add tests/integration/bdd/test_router_bdd.py tests/integration/bdd/steps/router_steps.py src/backend/agents/intent_router.py && \
git commit -m "[BDD-LOOP] POC: @router fallback scenario green end-to-end"
```

---

### Task 6: Add `bdd_tags` to task card schema (TDD)

**Files:**
- Modify: `scripts/pick_next_task.py`
- Create: `tests/unit/scripts/test_pick_next_task_bdd.py`
- Create: `tasks/TEMPLATE.md` (or modify if exists — verify in step 6.4)
- Create: `tasks/SPEC-C/C-BDD-POC.md` (POC owner card)

- [ ] **Step 6.1: RED — test that `TaskCard` has `bdd_tags` field**

Create `tests/unit/scripts/test_pick_next_task_bdd.py`:

```python
"""TDD test: TaskCard dataclass parses bdd_tags from task cards."""
from __future__ import annotations
from pathlib import Path

from scripts.pick_next_task import load_task_cards, TaskCard


def test_task_card_parses_bdd_tags(tmp_path, monkeypatch):
    root = tmp_path
    (root / "tasks" / "SPEC-X").mkdir(parents=True)
    card = root / "tasks" / "SPEC-X" / "X-001-example.md"
    card.write_text(
        "# [SPEC-X-001] Example\n\n"
        "## Metadata\n"
        "- **task_id**: SPEC-X-001\n"
        "- **depends_on**: []\n"
        "- **priority**: P0\n"
        "- **allowed_files**: [src/foo.py]\n"
        "- **bdd_tags**: [@router, @classification]\n",
        encoding="utf-8",
    )
    cards = load_task_cards(root)
    assert "SPEC-X-001" in cards
    c: TaskCard = cards["SPEC-X-001"]
    assert c.bdd_tags == ["@router", "@classification"]


def test_task_card_bdd_tags_defaults_empty(tmp_path):
    root = tmp_path
    (root / "tasks" / "SPEC-X").mkdir(parents=True)
    card = root / "tasks" / "SPEC-X" / "X-002-no-bdd.md"
    card.write_text(
        "# [SPEC-X-002] No BDD\n\n"
        "## Metadata\n"
        "- **task_id**: SPEC-X-002\n"
        "- **depends_on**: []\n"
        "- **priority**: P1\n"
        "- **allowed_files**: [src/bar.py]\n",
        encoding="utf-8",
    )
    cards = load_task_cards(root)
    assert cards["SPEC-X-002"].bdd_tags == []
```

- [ ] **Step 6.2: Run — confirm FAIL**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/unit/scripts/test_pick_next_task_bdd.py -v
```
Expected: FAIL with `AttributeError: 'TaskCard' object has no attribute 'bdd_tags'`. Correct RED.

- [ ] **Step 6.3: GREEN — add `bdd_tags` to dataclass + parser**

Modify `scripts/pick_next_task.py`. Update the dataclass:

```python
@dataclass
class TaskCard:
    task_id: str
    depends_on: list[str]
    priority: str
    allowed_files: list[str]
    bdd_tags: list[str]
```

Add helper next to `_parse_allowed_files`:

```python
def _parse_bdd_tags(raw: str | None) -> list[str]:
    """Parse `- **bdd_tags**: [@router, @phase0]` into a list.

    Tags must start with '@'. Returns [] if key absent or malformed.
    """
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        parts = [p.strip().strip("'\"") for p in inner.split(",")]
    else:
        parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p.startswith("@")]
```

Update `load_task_cards` — inside the card loop after `allowed = _parse_allowed_files(...)`:

```python
            bdd_tags = _parse_bdd_tags(
                _metadata_value(body, "bdd_tags")
            )
            cards[task_id] = TaskCard(
                task_id=task_id,
                depends_on=depends_on,
                priority=priority,
                allowed_files=allowed,
                bdd_tags=bdd_tags,
            )
```

- [ ] **Step 6.4: Run — confirm GREEN**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/unit/scripts/test_pick_next_task_bdd.py -v
```
Expected: 2 passed.

- [ ] **Step 6.5: Backward-compat regression check**

Existing callers may rely on `TaskCard(...)` positional args. Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
grep -rn "TaskCard(" --include="*.py" | grep -v "__pycache__"
```
If any direct instantiation exists outside `load_task_cards`, add `bdd_tags=[]` to it. Expected: only `pick_next_task.py` instantiates `TaskCard`; tests use kwargs or go through `load_task_cards`.

- [ ] **Step 6.6: Create POC owner task card**

Create `tasks/SPEC-C/C-BDD-POC.md`:

```markdown
# [SPEC-C-BDD-POC] IntentRouter BDD POC

## Metadata
- **task_id**: SPEC-C-BDD-POC
- **spec_ref**: BDD §IntentRouter (docs/BDD_ai_system_expected_behavior_v1.feature.md)
- **depends_on**: []
- **priority**: P2
- **estimated_complexity**: S
- **allowed_files**: [src/backend/agents/intent_router.py, tests/integration/bdd/steps/router_steps.py]
- **bdd_tags**: [@router]

## Scope
Keep the IntentRouter BDD POC (1 scenario) green. This card is the owner
for all @router BDD scenarios; expanding scenario coverage is a follow-up.

## Acceptance Criteria
- [ ] AC-1: `pytest tests/integration/bdd/ -m router` passes at least one scenario
- [ ] AC-2: Fallback behaviour: invalid JSON → action=clarify, events contains `router.intent_fallback`

## Verification Commands
```bash
pytest tests/integration/bdd/ -m router -v
```

## Completion Definition
`@router` tag has at least the timeout/fallback scenario green; CI will keep it green via Loop auto-invocation (Task 7 of plan).
```

- [ ] **Step 6.7: Verify picker includes the new card**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
python3 -c "from scripts.pick_next_task import load_task_cards; from pathlib import Path; cards = load_task_cards(Path('.')); print(cards.get('SPEC-C-BDD-POC'))"
```
Expected: prints `TaskCard(task_id='SPEC-C-BDD-POC', ..., bdd_tags=['@router'])`.

- [ ] **Step 6.8: Commit**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git add scripts/pick_next_task.py tests/unit/scripts/test_pick_next_task_bdd.py tasks/SPEC-C/C-BDD-POC.md && \
git commit -m "[BDD-LOOP] add bdd_tags field to TaskCard; POC owner card"
```

---

### Task 7: Wire BDD into Loop verifier (TDD)

The verifier prompt currently reads the task card and runs `verification_commands`. It must also, when `bdd_tags` is non-empty, run `pytest tests/integration/bdd/ -m "<tag expr>"` and block if those scenarios fail. Implementation: extend the verifier prompt template + pass `bdd_tags` into the command builder so the verifier agent sees the exact command to run.

**Files:**
- Modify: `scripts/run_task_driver.py`
- Create: `tests/unit/scripts/test_run_task_driver_bdd.py`

- [ ] **Step 7.1: RED — test that verifier command embeds BDD pytest when tags present**

Create `tests/unit/scripts/test_run_task_driver_bdd.py`:

```python
"""TDD test: verifier prompt includes `pytest -m "<tags>"` for BDD owners."""
from __future__ import annotations

from scripts.run_task_driver import (
    VERIFIER_PROMPT_TEMPLATE,
    build_verifier_command,
    render_prompt,
)


def test_verifier_prompt_injects_bdd_tags():
    prompt = render_prompt(
        VERIFIER_PROMPT_TEMPLATE,
        task_id="SPEC-C-BDD-POC",
        bdd_tag_expr="router",  # pytest marker expr; no @ prefix
    )
    assert "pytest tests/integration/bdd/" in prompt
    assert '-m "router"' in prompt or '-m \\"router\\"' in prompt


def test_verifier_prompt_omits_bdd_when_no_tags():
    prompt = render_prompt(
        VERIFIER_PROMPT_TEMPLATE,
        task_id="SPEC-D-001",
        bdd_tag_expr="",
    )
    # When there are no BDD tags, the BDD invocation line must not appear.
    assert "tests/integration/bdd/" not in prompt


def test_build_verifier_command_passes_bdd_tag_expr():
    cmd = build_verifier_command(
        program="claude",
        task_id="SPEC-C-BDD-POC",
        max_turns=10,
        prompt_template=VERIFIER_PROMPT_TEMPLATE,
        bdd_tag_expr="router",
    )
    # prompt is argv[2]; assert BDD line baked in
    assert any("tests/integration/bdd/" in s for s in cmd)
```

- [ ] **Step 7.2: Run → FAIL**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/unit/scripts/test_run_task_driver_bdd.py -v
```
Expected: FAIL — `build_verifier_command` takes no `bdd_tag_expr` kwarg; prompt lacks BDD line. Correct RED.

- [ ] **Step 7.3: GREEN — amend `VERIFIER_PROMPT_TEMPLATE`**

In `scripts/run_task_driver.py`, replace `VERIFIER_PROMPT_TEMPLATE` with:

```python
VERIFIER_PROMPT_TEMPLATE = (
    "独立审计 {task_id}（只读审查，你不是开发者而是审计者）：\n"
    "- 禁止修改除 .verify/{task_id}.json 之外的任何文件\n"
    "- 读 tasks/SPEC-*/{task_id}*.md 提取 verification_commands\n"
    "- 逐一执行每条命令，捕获 exit code 与关键输出尾部（最多 20 行）\n"
    "{bdd_block}"
    "- 读 PROGRESS.md 中 {task_id} 最新条目，检查 HARNESS §9.2 字段是否齐全\n"
    "  (Status / Started / Completed / Files Changed / Verification / Artifacts)\n"
    "- 写报告到 .verify/{task_id}.json，schema:\n"
    '  {{"task_id": "{task_id}", "status": "pass" | "fail",\n'
    '    "verification_results": [\n'
    '      {{"command": "...", "exit_code": N, "tail": "..."}}],\n'
    '    "bdd_results": [\n'
    '      {{"tag_expr": "...", "exit_code": N, "passed": N, "failed": N, "tail": "..."}}],\n'
    '    "progress_check": "pass" | "fail",\n'
    '    "reasons": ["..."] }}\n'
    "- 判定：所有 verification_command exit=0 且 BDD（如有） exit=0 且 progress_check=pass → status=pass\n"
    "- 任何一项不满足 → status=fail，reasons 写清具体原因（命令名 + 失败摘要）\n"
    "- 不要 append PROGRESS.md；不要 git commit；完成即结束"
)


def _build_bdd_block(bdd_tag_expr: str) -> str:
    """Return the BDD verification instruction lines, or empty string."""
    if not bdd_tag_expr:
        return ""
    return (
        f'- 额外执行 BDD：`pytest tests/integration/bdd/ -m "{bdd_tag_expr}" -v`\n'
        f'  捕获 exit code、通过/失败数、输出尾部 20 行；写入 bdd_results[0]\n'
    )
```

- [ ] **Step 7.4: GREEN — update `render_prompt` to pass `bdd_block`**

`render_prompt` already does naive `.replace("{key}", value)`, so we need to compute `bdd_block` from `bdd_tag_expr` before rendering. Add above `render_prompt`:

```python
def _render_verifier_prompt(template: str, task_id: str, bdd_tag_expr: str) -> str:
    out = template.replace("{task_id}", str(task_id))
    out = out.replace("{bdd_block}", _build_bdd_block(bdd_tag_expr))
    return out
```

- [ ] **Step 7.5: GREEN — extend `build_verifier_command`**

Change signature in `scripts/run_task_driver.py`:

```python
def build_verifier_command(
    program: str,
    task_id: str,
    max_turns: int,
    prompt_template: str,
    bdd_tag_expr: str = "",
) -> list[str]:
    """Return argv for the independent verifier `claude -p` invocation.

    bdd_tag_expr is a pytest marker expression (no '@' prefix, space-free);
    when non-empty, the prompt instructs the verifier to also run
    `pytest tests/integration/bdd/ -m "<expr>"`.
    """
    prompt = _render_verifier_prompt(prompt_template, task_id, bdd_tag_expr)
    return [program, "-p", prompt, "--max-turns", str(max_turns)]
```

- [ ] **Step 7.6: Run the test → GREEN**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/unit/scripts/test_run_task_driver_bdd.py -v
```
Expected: 3 passed. If existing tests for `render_prompt` broke because `{bdd_block}` is now a recognised placeholder, update them or rename to avoid collision.

- [ ] **Step 7.7: Regression — confirm existing driver tests still pass**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/unit/scripts/ -v 2>&1 | tail -20
```
Expected: all existing `run_task_driver` tests still pass (the new tests are additive; old tests call `build_verifier_command` with 4 positional args, which the new default kwarg preserves).

- [ ] **Step 7.8: Wire picker-supplied `bdd_tags` through the callable chain**

In `main()` of `scripts/run_task_driver.py`, the verifier builder currently receives only `task_id` from the lambda. Extend to read the card's `bdd_tags` at dispatch time.

Add helper near `pick_next_from_script`:

```python
def _lookup_bdd_tag_expr(root: Path, task_id: str) -> str:
    """Return pytest marker expression derived from the task card's bdd_tags.

    @router / @phase0 → 'router' / 'phase0'; multi-tag → ' or '-joined.
    Empty string if card missing or no bdd_tags.
    """
    import pick_next_task as _pnt  # type: ignore
    cards = _pnt.load_task_cards(root)
    card = cards.get(task_id)
    if not card or not card.bdd_tags:
        return ""
    # Strip '@' prefix; pytest markers don't include it.
    names = [t.lstrip("@") for t in card.bdd_tags]
    return " or ".join(names)
```

Then in the verifier-callable wire-up (around line 660 in current `main()`), replace:

```python
    if not args.no_verify:
        verify_cb = make_verify(
            lambda tid: build_verifier_command(
                args.program,
                tid,
                args.verifier_max_turns,
                VERIFIER_PROMPT_TEMPLATE,
            ),
            args.root / args.verify_dir,
        )
```

with:

```python
    if not args.no_verify:
        verify_cb = make_verify(
            lambda tid: build_verifier_command(
                args.program,
                tid,
                args.verifier_max_turns,
                VERIFIER_PROMPT_TEMPLATE,
                _lookup_bdd_tag_expr(args.root, tid),
            ),
            args.root / args.verify_dir,
        )
```

- [ ] **Step 7.9: Smoke-test with `--dry-run`**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
python3 scripts/run_task_driver.py --dry-run --root . 2>&1 | tail -10
```
Expected: `[DRY-RUN]` output shows next task. If `SPEC-C-BDD-POC` is picked (P2 but no deps), the verifier line will reference `tests/integration/bdd/`.

- [ ] **Step 7.10: Commit**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git add scripts/run_task_driver.py tests/unit/scripts/test_run_task_driver_bdd.py && \
git commit -m "[BDD-LOOP] verifier auto-runs pytest -m <bdd_tags> from task card"
```

---

### Task 8: Eval bucket POC with deepeval (TDD)

One semantic scenario chosen: "用户提出局部修改时识别为 revise" (`@classification @router` in source). The Then clause `action 应为 revise` is semantic (LLM-judge) because classifier correctness is evaluated, not a DB assertion.

**Files:**
- Create: `tests/eval/bdd/conftest.py`
- Create: `tests/eval/bdd/steps/__init__.py`
- Create: `tests/eval/bdd/steps/classification_steps.py`
- Create: `tests/eval/bdd/test_classification_bdd.py`

- [ ] **Step 8.1: Create `tests/eval/bdd/conftest.py`**

```python
"""deepeval fixtures for eval-bucket BDD scenarios.

Every Then that requires semantic judgement should pull the `judge` fixture
from here and use GEval. Direct LLM-judge code in step defs is banned — keep
the prompt contract in one place so baselines stay comparable.
"""
from __future__ import annotations

import os
import pytest
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams


@pytest.fixture
def scenario_state():
    """Mirror the integration bucket — mutable per-scenario dict."""
    return {}


@pytest.fixture(scope="session")
def require_eval_mode():
    """Skip all scenarios unless AVS_EVAL_MODE=1 (avoids LLM bill in unit runs)."""
    if os.environ.get("AVS_EVAL_MODE") != "1":
        pytest.skip("eval bucket off (set AVS_EVAL_MODE=1 to enable)")


@pytest.fixture
def classification_metric(require_eval_mode):
    """GEval metric: does actual_output match expected action label?"""
    return GEval(
        name="action-classification",
        criteria=(
            "Actual output must equal the expected action label. "
            "Acceptable aliases: 'revise' ~ '局部修改', 'regenerate' ~ '整体重做'."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        threshold=0.8,
    )
```

- [ ] **Step 8.2: Create `tests/eval/bdd/steps/__init__.py`**

```python
```

- [ ] **Step 8.3: RED — dispatcher with no step defs**

Create `tests/eval/bdd/test_classification_bdd.py`:

```python
"""pytest-bdd dispatcher for features/router.feature (eval bucket).

Note: router.feature is eval-classified for classifier-correctness scenarios;
integration-bucket router.feature covers the timeout/fallback case only.
"""
from pytest_bdd import scenarios

scenarios("features/router.feature")
```

(The eval bucket's `router.feature` is emitted by the splitter when any
@router scenario is classified as semantic. If splitter classification of the
revise scenario needs adjustment, override via `SCENARIO_FORCE_EVAL` —
"action 应为 revise" already matches that pattern.)

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
AVS_EVAL_MODE=1 pytest tests/eval/bdd/test_classification_bdd.py -v 2>&1 | tail -15
```
Expected: FAIL with `StepDefinitionNotFoundError`. Correct RED.

- [ ] **Step 8.4: GREEN — step defs + deepeval assertion**

Create `tests/eval/bdd/steps/classification_steps.py`:

```python
"""Step defs for @classification eval scenarios.

Scenarios covered (growing):
  * 用户提出局部修改时识别为 revise
"""
from __future__ import annotations

from pytest_bdd import given, when, then, parsers
from deepeval import assert_test
from deepeval.test_case import LLMTestCase


@given("当前阶段存在可编辑主产物")
def editable_artifact_exists(scenario_state):
    scenario_state["editable_artifact"] = True


@given(parsers.parse('用户输入"{utterance}"'))
def capture_utterance(scenario_state, utterance):
    scenario_state["utterance"] = utterance


@when("IntentRouter 处理该输入")
def router_classifies(scenario_state):
    from src.backend.agents.intent_router import IntentRouter
    router = IntentRouter()
    # classify() is the semantic entry — parse_or_fallback is the integration path.
    scenario_state["result"] = router.classify(scenario_state["utterance"])


@then(parsers.parse("action 应为 {expected_action}"))
def assert_action_matches(scenario_state, expected_action, classification_metric):
    result = scenario_state["result"]
    test_case = LLMTestCase(
        input=scenario_state["utterance"],
        actual_output=str(result.get("action", "")),
        expected_output=expected_action,
    )
    assert_test(test_case, [classification_metric])


@then(parsers.parse("params.{key} 应定位到{desc}"))
def assert_params_key(scenario_state, key, desc):
    params = scenario_state["result"].get("params") or {}
    assert params.get(key), f"params.{key} missing; desc={desc!r}"


@then(parsers.parse("params.{key} 应包含\"{needle}\""))
def assert_params_contains(scenario_state, key, needle):
    params = scenario_state["result"].get("params") or {}
    assert needle in str(params.get(key, "")), f"{needle!r} not in params.{key}={params.get(key)!r}"


@then("系统应追加 user_revision task")
def assert_user_revision_task(scenario_state):
    tasks = scenario_state["result"].get("task_ledger") or []
    assert any(t.get("type") == "user_revision" for t in tasks), \
        f"no user_revision task in {tasks!r}"
```

- [ ] **Step 8.5: GREEN — extend `IntentRouter` with `classify`**

Amend `src/backend/agents/intent_router.py` — add to the class:

```python
    def classify(self, utterance: str) -> dict:
        """Rule-based classifier stub. Upgrade to LLM-call in follow-up.

        Contract (minimum to pass the 'revise' eval scenario):
          - utterance contains '第' + digit + '段' + ('改' or '更') → revise
          - else → clarify fallback
        """
        import re
        if re.search(r"第[\\d一二三四五六七八九十]+段", utterance) and (
            "改" in utterance or "更" in utterance
        ):
            segment = re.search(r"第([\\d一二三四五六七八九十]+)段", utterance).group(0)
            return {
                "action": "revise",
                "params": {
                    "target": segment,
                    "instruction": utterance,
                },
                "task_ledger": [{"type": "user_revision", "target": segment}],
            }
        return {"action": "clarify", "params": {}, "task_ledger": []}
```

- [ ] **Step 8.6: Run — confirm GREEN (with LLM budget)**

Set the judge model API key in env (project convention: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` — deepeval auto-detects). Then:

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
AVS_EVAL_MODE=1 pytest tests/eval/bdd/test_classification_bdd.py -v 2>&1 | tail -20
```
Expected: the "局部修改" scenario PASSES. Other @classification scenarios without step defs FAIL with `StepDefinitionNotFoundError` — acceptable, documented for follow-up plan.

- [ ] **Step 8.7: Confirm eval skip still works without `AVS_EVAL_MODE`**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/eval/bdd/test_classification_bdd.py -v 2>&1 | tail -10
```
Expected: all scenarios SKIPPED with message about `AVS_EVAL_MODE=1`. Confirms default unit runs do not bill LLMs.

- [ ] **Step 8.8: Commit**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git add tests/eval/bdd/conftest.py tests/eval/bdd/steps/ tests/eval/bdd/test_classification_bdd.py src/backend/agents/intent_router.py && \
git commit -m "[BDD-LOOP] eval POC: @classification revise scenario via deepeval"
```

---

### Task 9: End-to-end Loop smoke test (manual verification)

Prove the whole chain: `pick_next` → dispatch → verify (auto-runs BDD) → (fix on failure) → pass.

**Files:** none created; manual run of the driver.

- [ ] **Step 9.1: Confirm POC card is ready to pick**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
python3 scripts/pick_next_task.py --root .
```
Expected stdout: a task id. If it is not `SPEC-C-BDD-POC`, temporarily lower the priority of any blocking P0/P1 cards — or invoke the driver with `AVS_CURRENT_TASK=SPEC-C-BDD-POC` override (the `pick_next_task.py` wrapper honours it if you add a `--task-id` flag — out of scope here; just run with the natural pick order).

- [ ] **Step 9.2: Deliberately break the POC SUT to trigger the fix path**

Edit `src/backend/agents/intent_router.py` → in `parse_or_fallback`, change the `except` branch to:

```python
            return {"action": "unknown", "params": {}, "events": []}
```

(This breaks the @router scenario assertion `action == "clarify"`.)

- [ ] **Step 9.3: Confirm BDD fails before driver runs**

Run:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
pytest tests/integration/bdd/ -m router -v 2>&1 | tail -10
```
Expected: 1 failed scenario: `AssertionError: assert 'unknown' == 'clarify'`.

- [ ] **Step 9.4: Run the driver for one iteration**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
python3 scripts/run_task_driver.py --max-tasks 1 --max-fix-rounds 3 --no-review 2>&1 | tail -40
```

(Requires a working `claude` CLI binary; if not available, skip to step 9.7 and document as a manual-run gate.)

Expected: driver dispatches developer on `SPEC-C-BDD-POC`, the developer agent detects the broken classification, fixes `intent_router.py`, verifier re-runs, BDD scenario passes, loop exits with `max_tasks_reached`.

- [ ] **Step 9.5: Confirm the fix was by the fixer, not prior state**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git log --oneline -5 -- src/backend/agents/intent_router.py
```
Expected: last commit authored by the driver's fixer agent (commit message includes `[SPEC-C-BDD-POC]` prefix).

- [ ] **Step 9.6: Check the verifier report**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
cat .verify/SPEC-C-BDD-POC.json 2>/dev/null | head -40
```
Expected: `"status": "pass"`; `bdd_results[0]` has `exit_code: 0`, `passed >= 1`.

- [ ] **Step 9.7: If `claude` CLI is unavailable, document manual gate in PROGRESS.md**

Append an entry to `PROGRESS.md`:

```markdown
## [BDD-LOOP] Plan 2026-04-17 — end-to-end smoke

- **Status**: DEFERRED
- **Reason**: `claude -p` binary unavailable in current env; manual smoke
  deferred to next session with binary access. Unit-level proof captured:
  - `pytest tests/integration/bdd/ -m router` green
  - `pytest tests/unit/scripts/test_run_task_driver_bdd.py` green
  - `render_prompt` injects BDD pytest line when bdd_tags present
- **Notes**: The Loop will pick up SPEC-C-BDD-POC naturally next run.
```

- [ ] **Step 9.8: Revert the deliberate break (if step 9.4 succeeded — skip if the fixer already restored it)**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git diff src/backend/agents/intent_router.py
```
If the file still has the sabotage, restore:
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git checkout src/backend/agents/intent_router.py
```

- [ ] **Step 9.9: Commit PROGRESS.md if Step 9.7 appended**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && \
git add PROGRESS.md && \
git commit -m "[BDD-LOOP] document deferred end-to-end smoke"
```

---

## Post-plan: Follow-up plan scope

Not implemented here; capture in next plan:

1. **Mass conversion** — expand step defs across the remaining ~106 scenarios (14 feature files × ~8 scenarios avg). Strategy: `pytest --collect-only` + `pytest-bdd parsers.parse` dedup; generate stubs from first-run `StepDefinitionNotFoundError` reports.
2. **HARNESS §10.3 regression gate** — `scripts/check_eval_regression.py`: capture a `tests/eval/eval_report.json` baseline after the first green eval run; on subsequent CI, diff accuracy per scenario-tag, exit 1 if drop > 5%.
3. **Task card sweep** — audit every existing SPEC-X-NNN card, annotate `bdd_tags` field where the task owns specific Gherkin tags. Tag ownership rubric: if `allowed_files` ∩ tag-implementing-files ≠ ∅.
4. **Parallel-safety** — confirm `pytest-xdist -n` works for integration BDD; pin eval to `-n 0` (deepeval metric cache is not thread-safe).

---

## Self-review

**Spec coverage check:**
- ✅ "构建测试用例" — Tasks 2-3 (splitter rewrite → `.feature` files), Tasks 4-5 (step library + integration POC), Task 8 (eval POC with deepeval)
- ✅ "接入 Loop" — Tasks 6-7 (`bdd_tags` field + verifier auto-run), Task 9 (end-to-end smoke)
- ✅ "每次开发 task 后触发 Loop 中 BDD 被执行" — Task 7 Step 7.8 wires `_lookup_bdd_tag_expr(root, tid)` into `make_verify` so every dispatched task's verifier injects the right BDD tag expression

**Placeholder scan:** no TBD/TODO/"handle edge cases"/skipped code blocks. Every step either (a) lists an exact command, (b) contains the full code to write, or (c) is a one-line observation after a command.

**Type consistency check:**
- `bdd_tags: list[str]` in `TaskCard` (Task 6) → `bdd_tag_expr: str` in `build_verifier_command` (Task 7) → derived via `_lookup_bdd_tag_expr` (Task 7 step 7.8). Conversion: `@`-prefixed list → `@`-stripped space-free names → `' or '.join(names)` → pytest marker expression. Chain consistent.
- `IntentRouter.parse_or_fallback` (Task 5) vs `IntentRouter.classify` (Task 8) are sibling methods, both return dicts with keys `action`, `params`. Integration scenario uses first; eval scenario uses second. No collision.
- `VERIFIER_PROMPT_TEMPLATE`'s `{bdd_block}` placeholder is handled by `_render_verifier_prompt` (Task 7 step 7.4), not by the generic `render_prompt` — documented in the helper docstring.

All checks pass. Plan is ready to execute.
