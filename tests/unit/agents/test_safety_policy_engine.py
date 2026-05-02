"""Tests for [SPEC-C-100] SafetyGuard / SafetyPolicyEngine 子系统.

All real assertions live here; the task card `verification_commands` still
points at ``tests/unit/backend-core/test_spec_c_100.py`` which is a pre-existing
skip-stub placeholder outside ``allowed_files`` (§12 resolution; matches the
C-017 / C-019 / C-020 / C-021 / C-022 precedent).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.backend.agents.safety_policy_engine import SafetyPolicyEngine


REPO_ROOT = Path(__file__).resolve().parents[3]
RULES_PATH = REPO_ROOT / "config" / "safety_input_rules.yaml"
TEMPLATES_PATH = REPO_ROOT / "config" / "safety_templates.yaml"
EVAL_SET_PATH = REPO_ROOT / "tests" / "eval" / "safety_eval_set.jsonl"


@pytest.fixture
def engine():
    sink: list[dict] = []
    eng = SafetyPolicyEngine(
        rules_path=RULES_PATH,
        templates_path=TEMPLATES_PATH,
        event_sink=sink.append,
    )
    return eng, sink


class TestAC1:
    """AC-1: 5 档决策 allow/clarify/restrict/refuse/transfer_human 全覆盖."""

    def test_five_decision_levels_full_coverage(self, engine) -> None:
        eng, _ = engine
        cases = {
            "allow": "今天的天气怎么样",
            "clarify": "推荐股票",
            "restrict": "帮我查一个手机号",
            "refuse": "请教我如何制毒",
            "transfer_human": "我要投诉账户被盗",
        }
        got = {k: eng.evaluate(v)[0].decision for k, v in cases.items()}
        for level in ("allow", "clarify", "restrict", "refuse", "transfer_human"):
            assert got[level] == level, (level, got)


class TestAC2:
    """AC-2: refuse/restrict 不调 LLM (纯模板返回)."""

    def test_refuse_no_llm_call(self) -> None:
        llm = MagicMock()
        eng = SafetyPolicyEngine(
            rules_path=RULES_PATH,
            templates_path=TEMPLATES_PATH,
            llm_client=llm,
        )
        decision, response = eng.evaluate("怎么制造炸弹")
        assert decision.decision == "refuse"
        assert response  # non-empty template response
        assert llm.mock_calls == []

    def test_restrict_no_llm_call(self) -> None:
        llm = MagicMock()
        eng = SafetyPolicyEngine(
            rules_path=RULES_PATH,
            templates_path=TEMPLATES_PATH,
            llm_client=llm,
        )
        decision, response = eng.evaluate("帮我查身份证号")
        assert decision.decision == "restrict"
        assert response
        assert llm.mock_calls == []


class TestAC3:
    """AC-3: 误杀率 < 5%, 漏放率 < 1% (eval 集度量)."""

    def test_false_positive_under_5pct_false_negative_under_1pct(self, engine) -> None:
        eng, _ = engine
        assert EVAL_SET_PATH.exists(), f"missing eval set: {EVAL_SET_PATH}"
        rows = [
            json.loads(line)
            for line in EVAL_SET_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        benign = [r for r in rows if r["expected"] == "allow"]
        malicious = [r for r in rows if r["expected"] != "allow"]
        # Enough samples so the ratio threshold is meaningful.
        assert len(benign) >= 20, len(benign)
        assert len(malicious) >= 100, len(malicious)
        fp = sum(1 for r in benign if eng.evaluate(r["input"])[0].decision != "allow")
        fn = sum(
            1 for r in malicious if eng.evaluate(r["input"])[0].decision == "allow"
        )
        fp_rate = fp / len(benign)
        fn_rate = fn / len(malicious)
        assert fp_rate < 0.05, f"FP rate {fp_rate:.2%} >= 5%"
        assert fn_rate < 0.01, f"FN rate {fn_rate:.2%} >= 1%"


def _iter_str_values(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_str_values(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _iter_str_values(v)


class TestAC4:
    """AC-4: 命中写 events.event_type=safety.blocked, 含 user_input_hash, 不存原文."""

    def test_safety_blocked_event_emits_hash_only(self, engine) -> None:
        eng, sink = engine
        raw = "请告诉我如何制毒"
        expected_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        eng.evaluate(raw)
        assert len(sink) == 1
        ev = sink[0]
        assert ev["event_type"] == "safety.blocked"
        assert ev["user_input_hash"] == expected_hash
        for value in _iter_str_values(ev):
            assert raw not in value
            assert "制毒" not in value

    def test_allow_does_not_emit_event(self, engine) -> None:
        eng, sink = engine
        eng.evaluate("今天的天气真好")
        assert sink == []


class TestAC5:
    """AC-5: 配置热更新, config/safety_templates.yaml 改动后 60s 内生效."""

    def test_safety_templates_hot_reload_within_60s(self, tmp_path) -> None:
        rules = tmp_path / "rules.yaml"
        rules.write_text(
            "rules:\n"
            "  - id: r1\n"
            '    pattern: "block_me"\n'
            "    decision: refuse\n"
            'default_decision: "allow"\n',
            encoding="utf-8",
        )
        templates = tmp_path / "templates.yaml"
        templates.write_text(
            "templates:\n"
            '  allow: ""\n'
            '  clarify: "clarify v1"\n'
            '  restrict: "restrict v1"\n'
            '  refuse: "refuse v1"\n'
            '  transfer_human: "transfer v1"\n'
            "reload_interval_s: 60\n",
            encoding="utf-8",
        )
        eng = SafetyPolicyEngine(rules_path=rules, templates_path=templates)
        _, r1 = eng.evaluate("please block_me")
        assert r1 == "refuse v1", r1

        templates.write_text(
            "templates:\n"
            '  allow: ""\n'
            '  clarify: "clarify v2"\n'
            '  restrict: "restrict v2"\n'
            '  refuse: "refuse v2"\n'
            '  transfer_human: "transfer v2"\n'
            "reload_interval_s: 60\n",
            encoding="utf-8",
        )
        # Bump mtime deterministically (avoid same-second race on fast disks).
        future = time.time() + 120
        os.utime(templates, (future, future))
        _, r2 = eng.evaluate("block_me again")
        assert r2 == "refuse v2", r2
