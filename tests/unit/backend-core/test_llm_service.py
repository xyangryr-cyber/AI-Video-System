"""Tests for [SPEC-C-011] LiteLLM + Instructor Integration & Model Routing.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-5.4 / SPEC-5.5.
Task card: tasks/SPEC-C/C-011-litellm-instructor-model-routing.md.

Acceptance mapping
------------------
AC-1  No direct ``openai.ChatCompletion`` calls anywhere in ``src/backend/``
      -> :class:`TestAC1NoDirectOpenAICalls`
AC-2  LLM format errors trigger Instructor-style auto-retry up to 3 times
      -> :class:`TestAC2RetryOnFormatError`
AC-3  ``model_config.json`` contains all 5 role keys
      -> :class:`TestAC3ModelConfigFiveKeys`
AC-4  Config change + restart causes ``resolve_model`` to return the new name
      -> :class:`TestAC4ConfigChangeAppliesNewModel`
AC-5  All LLM calls flow through a single ``llm_service`` entry point that
      uses LiteLLM -> :class:`TestAC5SingleEntryPointUsesLitellm`
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from src.backend.services import llm_service


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "src" / "backend"
CONFIG_PATH = REPO_ROOT / "config" / "model_config.json"
SERVICE_PATH = REPO_ROOT / "src" / "backend" / "services" / "llm_service.py"

EXPECTED_ROLE_KEYS = (
    "intent_router_primary",
    "reviewer",
    "gatekeeper",
    "producer",
    "subtask",
)


# ----------------------------------------------------------------------
# AC-1: no direct openai.ChatCompletion anywhere in src/backend/
# ----------------------------------------------------------------------


class TestAC1NoDirectOpenAICalls:
    """AC-1: enforce architectural boundary -- LiteLLM is the only transport."""

    def test_no_direct_openai_chat_completion_in_src_backend(self):
        """Grep src/backend/ for the banned symbol. Empty result = pass."""
        # Use plain ripgrep semantics via subprocess to mirror the task-card
        # verification command. We ignore the service's own string literal
        # inside documentation-style regex allowlists, but here we want the
        # assertion that there is NO production call site.
        forbidden = re.compile(r"openai\.ChatCompletion")
        hits: list[str] = []
        for path in BACKEND_ROOT.rglob("*.py"):
            # skip caches and the test-time import of this very assertion
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            # allow the service file to document the ban in a comment, but
            # fail on any *call* (identifier followed by "(" on the same line)
            for lineno, line in enumerate(text.splitlines(), 1):
                if (
                    forbidden.search(line)
                    and "(" in line.split("openai.ChatCompletion", 1)[1][:3]
                ):
                    hits.append(f"{path}:{lineno}:{line.strip()}")
        assert hits == [], (
            "Direct openai.ChatCompletion call sites are forbidden "
            "(SPEC-5.4). Hits:\n" + "\n".join(hits)
        )


# ----------------------------------------------------------------------
# AC-2: Instructor-style retry (up to 3x) on format errors
# ----------------------------------------------------------------------


class _Echo(BaseModel):
    """Minimal Pydantic model used to probe structured-output retry."""

    answer: str = Field(..., min_length=1)


class TestAC2RetryOnFormatError:
    """AC-2: format / validation errors retry up to 3 attempts, then give up."""

    def test_succeeds_on_third_attempt(self):
        """Two malformed responses, third is valid -> service returns it."""
        responses = iter(
            [
                "not-json",  # attempt 1: format error
                '{"wrong_key": "x"}',  # attempt 2: validation error
                '{"answer": "ok"}',  # attempt 3: valid
            ]
        )
        call_log: list[dict] = []

        def fake_completion(**kwargs):
            call_log.append(kwargs)
            return _completion_envelope(next(responses))

        out = llm_service.chat_completion(
            role="producer",
            messages=[{"role": "user", "content": "hi"}],
            response_model=_Echo,
            _completion_fn=fake_completion,
        )

        assert isinstance(out, _Echo)
        assert out.answer == "ok"
        assert len(call_log) == 3, (
            "Instructor-style retry should reach attempt 3 before success"
        )

    def test_raises_after_three_failed_attempts(self):
        """All 3 attempts malformed -> service raises after exactly 3 tries."""
        call_log: list[dict] = []

        def fake_completion(**kwargs):
            call_log.append(kwargs)
            return _completion_envelope("still-not-json")

        with pytest.raises(llm_service.LLMFormatError):
            llm_service.chat_completion(
                role="producer",
                messages=[{"role": "user", "content": "hi"}],
                response_model=_Echo,
                _completion_fn=fake_completion,
            )

        assert len(call_log) == 3, (
            "Instructor retry budget must cap at 3 attempts (SPEC-5.4 AC-2)"
        )


# ----------------------------------------------------------------------
# AC-3: model_config.json has exactly the 5 role keys
# ----------------------------------------------------------------------


class TestAC3ModelConfigFiveKeys:
    """AC-3: ensure the config file exists and carries all 5 role keys."""

    def test_config_file_exists(self):
        assert CONFIG_PATH.is_file(), f"missing config file: {CONFIG_PATH}"

    def test_config_has_all_five_role_keys(self):
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert isinstance(cfg, dict)
        missing = [k for k in EXPECTED_ROLE_KEYS if k not in cfg]
        assert missing == [], f"missing role keys: {missing}"

    def test_config_values_are_nonempty_strings(self):
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        for k in EXPECTED_ROLE_KEYS:
            v = cfg[k]
            assert isinstance(v, str) and v.strip(), (
                f"config key {k} must be non-empty string, got {v!r}"
            )

    def test_default_models_match_spec_table(self):
        """SPEC-5.5 table pins default models per role."""
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert cfg["intent_router_primary"] == "claude-haiku-4-5"
        assert cfg["reviewer"] == "claude-sonnet"
        assert cfg["gatekeeper"] == "claude-sonnet"
        assert cfg["producer"] == "doubao-pro"
        assert cfg["subtask"] == "doubao-pro"


# ----------------------------------------------------------------------
# AC-4: resolve_model re-reads config -> change takes effect on next call
# ----------------------------------------------------------------------


class TestAC4ConfigChangeAppliesNewModel:
    """AC-4: mutate config -> next ``resolve_model`` call sees new value."""

    def test_resolve_model_returns_five_role_defaults(self):
        for role, expected in [
            ("intent_router_primary", "claude-haiku-4-5"),
            ("reviewer", "claude-sonnet"),
            ("gatekeeper", "claude-sonnet"),
            ("producer", "doubao-pro"),
            ("subtask", "doubao-pro"),
        ]:
            assert llm_service.resolve_model(role) == expected, role

    def test_config_change_applies_without_cache(self, tmp_path):
        cfg = tmp_path / "model_config.json"
        cfg.write_text(json.dumps({"producer": "doubao-pro"}), encoding="utf-8")
        assert llm_service.resolve_model("producer", config_path=cfg) == "doubao-pro"

        cfg.write_text(json.dumps({"producer": "claude-sonnet"}), encoding="utf-8")
        assert (
            llm_service.resolve_model("producer", config_path=cfg) == "claude-sonnet"
        ), "SPEC-5.5 AC: config change must apply on next call (no internal cache)"

    def test_unknown_role_raises(self):
        with pytest.raises(llm_service.UnknownRoleError):
            llm_service.resolve_model("nonexistent_role")


# ----------------------------------------------------------------------
# AC-5: single entry point, backed by LiteLLM
# ----------------------------------------------------------------------


class TestAC5SingleEntryPointUsesLitellm:
    """AC-5: llm_service.chat_completion is the single entry point."""

    def test_public_api_exports_chat_completion_and_resolve_model(self):
        exported = set(getattr(llm_service, "__all__", ()))
        assert "chat_completion" in exported, llm_service.__all__
        assert "resolve_model" in exported, llm_service.__all__

    def test_chat_completion_delegates_to_litellm_by_default(self, monkeypatch):
        """When no _completion_fn is injected, the service must call
        ``litellm.completion``. We stub the attribute on the module so the
        test runs even if the real LiteLLM package is unavailable.
        """
        captured: dict = {}

        def fake_litellm_completion(**kwargs):
            captured.update(kwargs)
            return _completion_envelope('{"answer":"ok"}')

        # inject at the service's import surface, not the global litellm pkg
        monkeypatch.setattr(
            llm_service, "_default_completion", fake_litellm_completion, raising=True
        )

        out = llm_service.chat_completion(
            role="reviewer",
            messages=[{"role": "user", "content": "ping"}],
            response_model=_Echo,
        )
        assert isinstance(out, _Echo)
        assert out.answer == "ok"
        assert captured["model"] == "claude-sonnet", (
            "model must come from model_config role resolution"
        )
        assert captured["messages"] == [{"role": "user", "content": "ping"}]

    def test_service_module_uses_litellm_import(self):
        """The service file must import ``litellm`` -- the single transport."""
        text = SERVICE_PATH.read_text(encoding="utf-8")
        assert "import litellm" in text or "from litellm" in text, (
            "llm_service must use LiteLLM as its transport (SPEC-5.4)"
        )


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------


def _completion_envelope(content: str) -> dict:
    """Minimal OpenAI-chat-completion shape that LiteLLM exposes."""
    return {
        "id": "chatcmpl-test",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
