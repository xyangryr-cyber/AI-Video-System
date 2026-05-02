"""Tests for [SPEC-C-006] IntentRouter Core.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-4.1 / SPEC-4.2 / SPEC-4.3.

Test strategy per AC (mapped from task card; real tests live here per
``allowed_files``; the pre-existing ``test_spec_c_006.py`` skip-stub stays
in place per the SPEC-C-001..005 precedent -- task-card verification
commands still exit=0 against that file):

- AC-1 Stateless: ``IntentRouter()`` has an empty instance ``__dict__`` so
  nothing is silently cached across calls; back-to-back ``build_context``
  calls with different inputs must not bleed into each other.

- AC-2 Usable without warmup: fresh ``IntentRouter()`` immediately answers
  ``build_context(...)`` + ``resolve_model(...)`` with no init hook, no
  background thread, no DB warmup.

- AC-3 Artifact snapshot truncation: snapshot well over the 2000-token cap
  is truncated (not raised) and the returned prompt token-count stays
  within budget.

- AC-4 Conversation window: supply 10 entries, observe exactly the latest
  6 (not the oldest 6) in the assembled context.

- AC-5 No ``confirm_next`` in the action enum (SPEC-4.6: front-end hard
  button bypasses the router). Checked on both the class constant and the
  ``available_actions`` field of an assembled context.

- AC-6 Model from config, no hardcoded model literal: pointing the router
  at a freshly-written ``model_config.json`` with a sentinel model name
  yields that sentinel; scanning the source file finds no leaked literal
  other than the documented default-fallback constant line.

- AC-7 Config change + restart: write config v1 -> resolve -> write v2 ->
  new instance -> resolve returns v2 (no cached model from the prior
  instance).
"""

from __future__ import annotations

import json
from pathlib import Path


from src.backend.agents.intent_router import (
    AVAILABLE_ACTIONS,
    IntentRouter,
    load_router_model,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTER_SOURCE = REPO_ROOT / "src" / "backend" / "agents" / "intent_router.py"


# -- AC-1 -----------------------------------------------------------------


class TestAC1RouterNoInstanceState:
    def test_router_no_instance_state(self) -> None:
        r = IntentRouter()
        # Stateless: nothing bound to the instance across calls.
        assert r.__dict__ == {}, (
            f"IntentRouter instance carries state: {sorted(r.__dict__)}"
        )

    def test_calls_do_not_leak_state(self) -> None:
        """Two back-to-back calls with different inputs must be independent."""
        r = IntentRouter()
        ctx1 = r.build_context(
            project_meta={"project_id": "P1"},
            artifact_snapshot="",
            ledger_summary="",
            conversation_history=[{"role": "user", "text": "first"}],
            preference_rules=[],
            user_input="u1",
        )
        ctx2 = r.build_context(
            project_meta={"project_id": "P2"},
            artifact_snapshot="",
            ledger_summary="",
            conversation_history=[],
            preference_rules=[],
            user_input="u2",
        )
        assert ctx1["user_input"] == "u1"
        assert ctx2["user_input"] == "u2"
        assert ctx1["project_meta"]["project_id"] == "P1"
        assert ctx2["project_meta"]["project_id"] == "P2"
        assert ctx2["conversation"] == []
        # Crucially, still empty __dict__ after calls.
        assert r.__dict__ == {}


# -- AC-2 -----------------------------------------------------------------


class TestAC2RouterUsableWithoutWarmup:
    def test_router_usable_without_warmup(self) -> None:
        r = IntentRouter()  # nothing else happens at import/init time
        ctx = r.build_context(
            project_meta={"project_id": "P"},
            artifact_snapshot="",
            ledger_summary="",
            conversation_history=[],
            preference_rules=[],
            user_input="hi",
        )
        assert ctx["user_input"] == "hi"
        # Default model resolvable with no file present (via fallback)
        assert isinstance(r.resolve_model(config_path="/nonexistent/path.json"), str)


# -- AC-3 -----------------------------------------------------------------


class TestAC3ArtifactSnapshotTruncation:
    def test_artifact_snapshot_truncation(self) -> None:
        from src.backend.agents.intent_router import (
            _ARTIFACT_SNAPSHOT_MAX_TOKENS,
            _estimate_tokens,
        )

        # ~3000 tokens of filler (4 chars/token budget -> 12000 chars).
        huge = "x" * 12000
        r = IntentRouter()
        ctx = r.build_context(
            project_meta={},
            artifact_snapshot=huge,
            ledger_summary="",
            conversation_history=[],
            preference_rules=[],
            user_input="",
        )
        snap = ctx["artifact_snapshot"]
        assert isinstance(snap, str)
        assert snap != huge, "snapshot was not truncated"
        assert _estimate_tokens(snap) <= _ARTIFACT_SNAPSHOT_MAX_TOKENS, (
            f"snapshot tokens {_estimate_tokens(snap)} exceeds cap "
            f"{_ARTIFACT_SNAPSHOT_MAX_TOKENS}"
        )


# -- AC-4 -----------------------------------------------------------------


class TestAC4ConversationLatestSix:
    def test_conversation_latest_six(self) -> None:
        r = IntentRouter()
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "text": f"msg-{i}"}
            for i in range(10)
        ]
        ctx = r.build_context(
            project_meta={},
            artifact_snapshot="",
            ledger_summary="",
            conversation_history=history,
            preference_rules=[],
            user_input="",
        )
        conv = ctx["conversation"]
        assert isinstance(conv, list)
        assert len(conv) == 6
        got_texts = [m["text"] for m in conv]
        # Latest 6, in chronological order (not reversed, not oldest-6).
        assert got_texts == [
            "msg-4",
            "msg-5",
            "msg-6",
            "msg-7",
            "msg-8",
            "msg-9",
        ]

    def test_conversation_under_six_passes_through(self) -> None:
        r = IntentRouter()
        history = [{"role": "user", "text": f"m{i}"} for i in range(3)]
        ctx = r.build_context(
            project_meta={},
            artifact_snapshot="",
            ledger_summary="",
            conversation_history=history,
            preference_rules=[],
            user_input="",
        )
        assert [m["text"] for m in ctx["conversation"]] == ["m0", "m1", "m2"]


# -- AC-5 -----------------------------------------------------------------


class TestAC5ConfirmNextNotInActions:
    def test_confirm_next_not_in_class_enum(self) -> None:
        assert "confirm_next" not in IntentRouter.AVAILABLE_ACTIONS
        assert "confirm_next" not in AVAILABLE_ACTIONS

    def test_confirm_next_not_in_assembled_context(self) -> None:
        r = IntentRouter()
        ctx = r.build_context(
            project_meta={},
            artifact_snapshot="",
            ledger_summary="",
            conversation_history=[],
            preference_rules=[],
            user_input="",
        )
        assert "confirm_next" not in ctx["available_actions"]
        # But the enum should still contain at least the clarify fallback.
        assert "clarify" in ctx["available_actions"]


# -- AC-6 -----------------------------------------------------------------


class TestAC6ModelFromConfigNotHardcoded:
    def test_model_from_config(self, tmp_path: Path) -> None:
        cfg = tmp_path / "model_config.json"
        cfg.write_text(
            json.dumps({"intent_router_primary": "sentinel-model-9001"}),
            encoding="utf-8",
        )
        # Both the helper and the instance method must honour the config.
        assert load_router_model(cfg) == "sentinel-model-9001"
        assert IntentRouter().resolve_model(cfg) == "sentinel-model-9001"

    def test_missing_config_falls_back_to_default(self, tmp_path: Path) -> None:
        absent = tmp_path / "nope.json"
        # Must not raise; falls back to the documented default.
        model = load_router_model(absent)
        assert isinstance(model, str) and model  # non-empty
        # Default lives in a single named constant; scanning the source must
        # find at most ONE occurrence of the default string -- that is, the
        # definition itself. Zero occurrences would mean the test's default
        # sentinel and the source-code default have drifted.
        src = ROUTER_SOURCE.read_text(encoding="utf-8")
        hits = [ln for ln in src.splitlines() if f'"{model}"' in ln]
        assert len(hits) == 1, (
            f"default model {model!r} should appear in source exactly once "
            f"(the named constant); found {len(hits)} occurrences"
        )

    def test_malformed_config_falls_back_to_default(self, tmp_path: Path) -> None:
        bad = tmp_path / "broken.json"
        bad.write_text("{not-json", encoding="utf-8")
        # Must not propagate JSONDecodeError.
        assert isinstance(load_router_model(bad), str)


# -- AC-7 -----------------------------------------------------------------


class TestAC7ConfigChangeAppliesNewModel:
    def test_model_config_change_applied(self, tmp_path: Path) -> None:
        cfg = tmp_path / "model_config.json"
        cfg.write_text(
            json.dumps({"intent_router_primary": "model-v1"}),
            encoding="utf-8",
        )
        r1 = IntentRouter()
        assert r1.resolve_model(cfg) == "model-v1"

        # Simulate "config change + restart" (SPEC-4.3 AC-7): overwrite the
        # config, instantiate a fresh router, and re-resolve. No caching
        # across instances.
        cfg.write_text(
            json.dumps({"intent_router_primary": "model-v2"}),
            encoding="utf-8",
        )
        r2 = IntentRouter()
        assert r2.resolve_model(cfg) == "model-v2"

        # And even the original instance -- since it is stateless -- picks
        # up the new config when asked again.
        assert r1.resolve_model(cfg) == "model-v2"


# -- Regression: existing SPEC-C-101/102 surface still intact -------------


class TestExistingSurfacePreserved:
    """build_context adds to, does not replace, the existing router API."""

    def test_parse_or_fallback_still_works(self) -> None:
        r = IntentRouter()
        ok = r.parse_or_fallback('{"action": "revise", "params": {"x": 1}}')
        assert ok["action"] == "revise"
        fb = r.parse_or_fallback("not-json")
        assert fb["action"] == "clarify"

    def test_classify_still_works(self) -> None:
        r = IntentRouter()
        out = r.classify("把第3段改得更短")
        assert out["action"] == "revise"
        assert out["params"]["target"] == "第3段"
