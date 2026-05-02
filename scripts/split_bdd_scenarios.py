#!/usr/bin/env python3
"""Split docs/BDD_*.feature.md scenarios into integration vs eval .feature files.

Rationale:
  * Scenarios whose Then/And clauses assert deterministic system state (DB rows,
    FSM transitions, file existence, numeric thresholds, error-level enums) go
    to tests/integration/bdd/features/ -- runnable with a concrete SUT, no LLM in loop.
  * Scenarios whose Then/And clauses assert agent-output semantics (classifier
    correctness, reviewer verdict quality, content faithfulness, safety
    phrasing) go to tests/eval/bdd/features/ -- HARNESS S10.3 "eval regression gate";
    evaluation needs either ground-truth labels or LLM-as-judge.

Per-scenario classification is rule-based (see `classify()`); keep rules in one
place so re-runs are deterministic and reviewable.

Emitted files are valid Gherkin .feature files for pytest-bdd to parse.

Default mode is --dry-run. Pass --apply to write files.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BDD_SRC = ROOT / "docs" / "BDD_ai_system_expected_behavior_v1.feature.md"
INTEGRATION_DIR = ROOT / "tests" / "integration" / "bdd"
EVAL_DIR = ROOT / "tests" / "eval" / "bdd"

TAG_RE = re.compile(r"^@[\w\-@ ]+$")
FEATURE_RE = re.compile(r"^Feature:\s*(.+?)\s*$")
SCENARIO_RE = re.compile(r"^\s*Scenario(?:\s+Outline)?:\s*(.+?)\s*$")
STEP_RE = re.compile(r"^\s*(Given|When|Then|And|But)\s+(.+?)\s*$")


@dataclass
class Scenario:
    feature: str
    feature_tags: list[str]
    name: str
    scenario_tags: list[str]
    steps: list[tuple[str, str]] = field(default_factory=list)

    @property
    def all_tags(self) -> list[str]:
        return self.feature_tags + self.scenario_tags

    def gherkin(self) -> str:
        lines = []
        if self.scenario_tags:
            lines.append(" ".join(self.scenario_tags))
        lines.append(f"Scenario: {self.name}")
        for kw, body in self.steps:
            lines.append(f"  {kw} {body}")
        return "\n".join(lines)


def parse_bdd(text: str) -> list[Scenario]:
    lines = text.splitlines()
    scenarios: list[Scenario] = []
    feature: str = ""
    feature_tags: list[str] = []
    pending_tags: list[str] = []
    current: Scenario | None = None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("@"):
            pending_tags.extend(tok for tok in stripped.split() if tok.startswith("@"))
            continue
        fm = FEATURE_RE.match(stripped)
        if fm:
            if current:
                scenarios.append(current)
                current = None
            feature = fm.group(1)
            feature_tags = pending_tags
            pending_tags = []
            continue
        sm = SCENARIO_RE.match(stripped)
        if sm:
            if current:
                scenarios.append(current)
            current = Scenario(
                feature=feature,
                feature_tags=list(feature_tags),
                name=sm.group(1),
                scenario_tags=pending_tags,
            )
            pending_tags = []
            continue
        stm = STEP_RE.match(line)
        if stm and current is not None:
            current.steps.append((stm.group(1), stm.group(2)))
            continue
    if current:
        scenarios.append(current)
    return scenarios


# Classification: keywords in Then/And bodies that signal semantic judgment.
# These fire -> eval bucket.
SEMANTIC_KEYWORDS = [
    # reviewer content-quality verdicts
    "verdict",
    "不应引入",
    "应保持一致",
    "应保持不变",
    "实质差异",
    "覆盖",
    "语义",
    "合理",
    "和谐",
    "可读性",
    "对比度",
    "语速",
    "口语化",
    "自然",
    "风格",
    "立场",
    "脱敏",
    "敏感",
    "拒绝",
    "拒答",
    "引导",
    "核心观点",
    "实质",
    # classifier correctness
    "action 应为",
    "subtask_type 应为",
    "candidates",
    "candidate",
    "conflicts_with",
    "confidence",
    "summary_for_user",
    "推断",
    "解释",
    "reason",
    "rationale",
    "理由",
]

# Keywords signalling deterministic integration assertions -> integration bucket.
DETERMINISTIC_KEYWORDS = [
    "async_task",
    "async_tasks",
    "task_ledger",
    "preferences_confirmed_at",
    "GateKeeper",
    "Gate ",
    "gate-p",
    "phases.current",
    "phases.phase_",
    "project.status",
    "project.completed_at",
    "只读",
    "SQLite",
    "events",
    "events 表",
    "agent_call_log",
    "P95",
    "P99",
    "延迟",
    "10 秒内",
    "sample_rate",
    "44100",
    "dB",
    "连续覆盖",
    "连续 3 个",
    "分辨率",
    "平台",
    "mp4",
    "mp3",
    "面板",
    "筛选",
    "toast",
    "模态框",
    "level 应为",
    "下载",
    "页面",
    "/",
    "async_tasks.status",
    "async_task.status",
]

# Feature-level hints.
FEATURE_EVAL_TAGS = {
    "@classification",
    "@answer",
    "@decision",
    "@preferences",
    "@revision",
    "@facts",
    "@project-init",
    "@storyboard",
    "@chart",
    "@visual",
    "@audio",
    "@scoping",
    "@data-confirmation",
    "@style",
    "@customization",
    "@preview",
    "@incremental",
    "@validation-panel",
    "@interaction",
    "@asset-supplement",
    "@script",
    "@requirements",
}
FEATURE_INTEGRATION_TAGS = {
    "@gatekeeper",
    "@error-ux",
    "@observability",
    "@security",
    "@nonfunctional",
    "@performance",
    "@ui",
    "@navigation",
    "@delivery",
    "@editing",
    "@render",
    "@broll",
    "@sfx",
    "@music",
    "@audio",  # conflict: both music+audio appear -- resolved by scenario rules below
    "@storyboard",
}

# Scenario-text overrides: phrases that uniquely decide.
SCENARIO_FORCE_INTEGRATION = [
    "GateKeeper.check",
    "不应推进",
    "应按跳过分支通过",
    "project.status",
    "async_task",
    "preferences_confirmed_at",
    "task_ledger 不新增",
    "events 中应记录",
    "落库",
    "脱敏",
    "[REDACTED]",
    "P95",
    "P99",
    "10 秒内",
    "render_results.json",
    "90%",
    "只读模式",
    "phases.current.status",
    "confirm_next",  # most confirm_next tests are gate flow
]
SCENARIO_FORCE_EVAL = [
    "verdict 应为 FAIL",
    "verdict 应为 PASS",
    "StyleReviewer",
    "StructureReviewer",
    "CompletenessReviewer",
    "MusicFitReviewer",
    "SFXReviewer",
    "VisualReviewer",
    "AVSyncReviewer",
    "FactChecker",
    "AudioQualityReviewer",
    "BRollFitReviewer",
    "FinalReviewer",
    "StoryboardReviewer",
    "action 应为",
    "subtask_type 应为",
    "confidence 应",
    "实质差异",
    "不应引入",
    "应保持一致",
    "应保持不变",
    "语义相关",
    "口语化",
    "立场",
    "拒绝",
    "拒答",
    "引导",
]


def classify(sc: Scenario) -> str:
    """Return 'eval' or 'integration'. Order: scenario force -> feature tags -> default."""
    body = sc.gherkin()

    # Scenario-level forces win.
    eval_hits = sum(1 for p in SCENARIO_FORCE_EVAL if p in body)
    integration_hits = sum(1 for p in SCENARIO_FORCE_INTEGRATION if p in body)
    if eval_hits and not integration_hits:
        return "eval"
    if integration_hits and not eval_hits:
        return "integration"
    if eval_hits > integration_hits:
        return "eval"
    if integration_hits > eval_hits:
        return "integration"

    # Feature-tag fallback.
    tags = set(sc.all_tags)
    eval_tag_hit = bool(tags & FEATURE_EVAL_TAGS)
    int_tag_hit = bool(tags & FEATURE_INTEGRATION_TAGS)
    if eval_tag_hit and not int_tag_hit:
        return "eval"
    if int_tag_hit and not eval_tag_hit:
        return "integration"

    # Keyword fallback.
    sem = sum(1 for kw in SEMANTIC_KEYWORDS if kw in body)
    det = sum(1 for kw in DETERMINISTIC_KEYWORDS if kw in body)
    if sem > det:
        return "eval"
    if det > sem:
        return "integration"

    # Tie: bias to eval because this file is about AI behavior.
    return "eval"


def slugify(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "_", text)
    s = s.strip("_").lower()
    return s[:80] if s else "unnamed"


def feature_slug(feature: str, feature_tags: list[str]) -> str:
    # Prefer primary tag (e.g. phase0, phase1, router, gatekeeper) as slug stem.
    stem = None
    priority = ["phase0", "phase1", "phase2", "phase3", "phase4", "phase5",
                "phase6", "phase7", "phase7a", "phase8", "phase9", "phase10",
                "phase11", "router", "gatekeeper", "error-ux", "observability",
                "performance", "project-init", "facts", "preferences",
                "validation-panel", "incremental", "scoping", "storyboard",
                "chart", "visual", "audio", "navigation", "script",
                "data-confirmation", "customization", "safety", "preview"]
    tagset = {t.lstrip("@").lower() for t in feature_tags}
    for k in priority:
        if k in tagset:
            stem = k
            break
    if not stem:
        stem = slugify(feature)
    return stem.replace("-", "_")


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
            try:
                display = path.relative_to(ROOT)
            except ValueError:
                display = path
            if apply:
                features_dir.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                print(f"wrote {display}: {count} scenarios")
            else:
                print(f"would write {display}: {count} scenarios")
            files += 1
    return files, scenarios_total


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


if __name__ == "__main__":
    sys.exit(main())
