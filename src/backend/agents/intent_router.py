"""[SPEC-C-006] IntentRouter core: stateless, context-injected, config-driven.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-4.1..SPEC-4.3, SPEC-4.6.

Design
------
- **Stateless** (SPEC-4.1): no instance variables store cross-call state.
  Every ``route``/``build_context``/``resolve_model`` call reads fresh
  inputs from its arguments (which in turn come from SQLite / config
  files at call time). This makes the router trivially replayable,
  restart-safe, and free of warmup.
- **Fixed context template** (SPEC-4.2): ``build_context`` assembles
  ``system + project_meta + artifact_snapshot(<=2000 tokens)
  + ledger_summary(<=800 tokens) + latest 6 conversations
  + preference_rules(<=20 rules / <=1200 tokens) + available_actions
  + user_input``. Over-budget slices are truncated, never raised.
- **Model from config** (SPEC-4.3): ``resolve_model`` / ``load_router_model``
  read ``intent_router_primary`` from ``model_config.json`` at call
  time, falling back to ``claude-haiku-4-5`` when the file is missing,
  the key absent, or the file malformed.
- **confirm_next bypass** (SPEC-4.6): ``AVAILABLE_ACTIONS`` intentionally
  omits ``confirm_next``; the front-end hard button calls the phase
  API directly, bypassing NLP routing.

The legacy ``parse_or_fallback`` / ``classify`` surface (used by the
@router BDD scenarios) is preserved verbatim -- context-building is
additive.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.backend.agents.actions.challenge_claim import ChallengeClaimParams
from src.backend.agents.actions.insert_section import InsertSectionParams
from src.backend.agents.actions.request_chart import RequestChartParams
from src.backend.agents.actions.save_stage_preference import (
    SaveStagePreferenceParams,
)
from src.backend.agents.actions.supplement_claim import SupplementClaimParams
from src.backend.agents.actions.view_phase_detail import ViewPhaseDetailParams

if TYPE_CHECKING:
    from src.backend.agents.safety_policy_engine import SafetyPolicyEngine


# -- Config resolution (SPEC-4.3) -----------------------------------------

_CONFIG_KEY = "intent_router_primary"
_DEFAULT_CONFIG_PATH = "config/model_config.json"

# Documented fallback (single source-code occurrence, enforced by test):
_DEFAULT_MODEL = "claude-haiku-4-5"


# -- Action enum (SPEC-4.2 / SPEC-4.6) ------------------------------------
# confirm_next is NOT in this list: SPEC-4.6 routes phase advance through a
# hard front-end button, not through NLP intent classification.

AVAILABLE_ACTIONS: tuple[str, ...] = (
    "revise",
    "regenerate_section",
    "regenerate_shot",
    "challenge_claim",
    "supplement_claim",
    "request_chart",
    "view_phase_detail",
    "save_stage_preference",
    "insert_section",
    "refine_requirements",
    "clarify",
)


# -- Context-template budgets (SPEC-4.2) ----------------------------------

_ARTIFACT_SNAPSHOT_MAX_TOKENS = 2000
_LEDGER_SUMMARY_MAX_TOKENS = 800
_PREFERENCES_MAX_RULES = 20
_PREFERENCES_MAX_TOKENS = 1200
_CONVERSATION_WINDOW = 6

_SYSTEM_PROMPT = (
    "You are the AI-Video-System IntentRouter. Classify each user "
    "utterance into exactly one of the available actions. Output a JSON "
    "object with keys 'action' and 'params'. When uncertain, output "
    '{"action": "clarify"}.'
)


# -- SPEC-C-007 fallback / clarify-count helpers --------------------------

# Trigger shows candidate buttons after this many consecutive clarifies.
_CLARIFY_TRIGGER = 2

# Up to 4 actionable candidates shown to the user after repeated confusion.
_CANDIDATE_ACTIONS: tuple[str, ...] = (
    "revise",
    "regenerate_section",
    "request_chart",
    "challenge_claim",
)


def _call_with_timeout(
    llm_callable: Callable[[], str | None],
    timeout_seconds: float,
) -> tuple[str | None, bool]:
    """Run *llm_callable* in a daemon thread; return ``(raw, timed_out)``.

    Daemon threads are killed when the process exits, so a slow callable
    that outlives its timeout window does not block test teardown.
    """
    result_holder: list[str | None] = [None]
    error_holder: list[BaseException | None] = [None]
    done = threading.Event()

    def _run() -> None:
        try:
            result_holder[0] = llm_callable()
        except Exception as exc:  # noqa: BLE001
            error_holder[0] = exc
        finally:
            done.set()

    threading.Thread(target=_run, daemon=True).start()
    completed = done.wait(timeout=timeout_seconds)
    if not completed:
        return None, True
    return result_holder[0], False


def _make_clarify_result(clarify_count: int, *, reason: str) -> dict[str, Any]:
    """Build the clarify-fallback payload and emit the ``router_fallback`` event."""
    new_count = clarify_count + 1
    return {
        "action": "clarify",
        "params": {},
        "events": [{"type": "router_fallback", "reason": reason}],
        "clarify_count": new_count,
        "candidate_actions": (list(_CANDIDATE_ACTIONS) if new_count >= _CLARIFY_TRIGGER else None),
    }


# -- Legacy classifier surface (@router BDD) ------------------------------

_SEGMENT_RE = re.compile(r"第[\d一二三四五六七八九十]+段")

# Heuristic: detect when the user is providing substantive information rather
# than asking a question or being vague. Used to distinguish "the user is
# telling us something useful" from "the user needs clarification".
_QUESTION_PATTERN = re.compile(r"[?？]|怎么|如何|什么|为什么|哪里|哪个|谁")
_MIN_SUBSTANTIVE_CHARS = 20

# SPEC-G-013 keyword rules for the deterministic classify() shortcut.
# Order matters: regenerate is matched before the legacy revise rule so
# "整体重做" cannot fall through to clarify.
_REGENERATE_KEYWORDS: tuple[str, ...] = (
    "整体重做",
    "推倒重来",
    "重做",
    "重新生成",
    "重新写",
    "regenerate",
)

# Advance-intent keywords. Per SPEC-4.6 the router MUST NOT return an
# executable advance action; instead it returns clarify + highlight signal
# so the front-end hard button (confirm_next) becomes the only legitimate
# advance entry point.
_ADVANCE_KEYWORDS: tuple[str, ...] = (
    "进入下一阶段",
    "继续推进",
    "下一步",
    "推进",
    "next phase",
)


# -- Helpers --------------------------------------------------------------


def _estimate_tokens(text: str) -> int:
    """Lightweight token estimate: 1 token per 4 characters (OpenAI/Anthropic
    rule-of-thumb). Conservative for CJK-heavy text, which is fine for
    truncation budgets -- err on the side of fitting more content inside
    the cap, not less.
    """
    if not text:
        return 0
    return (len(text) + 3) // 4


def _truncate_to_token_budget(text: str, budget_tokens: int) -> str:
    """Truncate ``text`` so ``_estimate_tokens`` fits within ``budget_tokens``."""
    if _estimate_tokens(text) <= budget_tokens:
        return text
    # 4 chars/token -> keep first ``budget_tokens * 4`` chars.
    return text[: budget_tokens * 4]


def load_router_model(config_path: str | Path | None = None) -> str:
    """Resolve Router model name from ``model_config.json`` (SPEC-4.3).

    Reads key ``intent_router_primary``; falls back to ``claude-haiku-4-5``
    when the file is missing, unreadable, malformed JSON, or the key is
    absent / non-string / empty. Never raises.
    """
    path = Path(config_path) if config_path is not None else Path(_DEFAULT_CONFIG_PATH)
    try:
        with path.open(encoding="utf-8") as f:
            cfg = json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return _DEFAULT_MODEL
    if not isinstance(cfg, dict):
        return _DEFAULT_MODEL
    value = cfg.get(_CONFIG_KEY)
    if isinstance(value, str) and value:
        return value
    return _DEFAULT_MODEL


# -- Router ---------------------------------------------------------------


class IntentRouter:
    """Parse LLM router output and assemble the fixed context template.

    Stateless (SPEC-4.1): no ``__init__`` stores per-instance data.
    """

    # Class attribute (not instance state). Per SPEC-4.2 / SPEC-4.6.
    AVAILABLE_ACTIONS: tuple[str, ...] = AVAILABLE_ACTIONS

    # --- Context assembly (SPEC-4.2) -------------------------------------

    def build_context(
        self,
        *,
        project_meta: Mapping[str, Any],
        artifact_snapshot: str,
        ledger_summary: str,
        conversation_history: Iterable[Mapping[str, Any]],
        preference_rules: Iterable[Mapping[str, Any]],
        user_input: str,
    ) -> dict[str, Any]:
        """Assemble the SPEC-4.2 fixed context template.

        Returns a plain ``dict`` ready to be serialised into the LLM call
        payload. Over-budget fields are truncated silently; they MUST NOT
        raise because the router is a non-blocking read path.
        """
        conv_list = list(conversation_history)
        recent_conv: list[Mapping[str, Any]] = conv_list[-_CONVERSATION_WINDOW:]

        # Cap by rule count, then by token budget.
        prefs: list[Mapping[str, Any]] = list(preference_rules)[:_PREFERENCES_MAX_RULES]
        while (
            prefs
            and _estimate_tokens(json.dumps(list(prefs), ensure_ascii=False))
            > _PREFERENCES_MAX_TOKENS
        ):
            prefs.pop()

        return {
            "system": _SYSTEM_PROMPT,
            "project_meta": dict(project_meta),
            "artifact_snapshot": _truncate_to_token_budget(
                artifact_snapshot, _ARTIFACT_SNAPSHOT_MAX_TOKENS
            ),
            "ledger_summary": _truncate_to_token_budget(ledger_summary, _LEDGER_SUMMARY_MAX_TOKENS),
            "conversation": [dict(m) for m in recent_conv],
            "preferences": [dict(p) for p in prefs],
            "available_actions": list(self.AVAILABLE_ACTIONS),
            "user_input": user_input,
        }

    # --- Model resolution (SPEC-4.3) -------------------------------------

    def resolve_model(self, config_path: str | Path | None = None) -> str:
        """Return the Router LLM model name for THIS call.

        No caching: each call re-reads the config so a hot-reload picks up
        immediately (SPEC-4.3 AC-7). Callers that need high-frequency
        resolution can memoise externally.
        """
        return load_router_model(config_path)

    # --- Legacy output parser (@router BDD, SPEC-4.4 fallback) -----------

    def parse_or_fallback(self, raw: str | None) -> dict[str, Any]:
        """Return structured decision, or fallback={action: clarify} on error.

        Contract:
          - Valid JSON with recognised 'action' key -> pass through.
          - Invalid JSON / timeout sentinel / missing key -> clarify fallback.
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
        except (ValueError, TypeError):
            return {
                "action": "clarify",
                "params": {},
                "events": [{"type": "router.intent_fallback", "reason": "parse_failed"}],
            }

    def route(
        self,
        llm_callable: Callable[[], str | None],
        *,
        clarify_count: int = 0,
        timeout_seconds: float = 3.0,
    ) -> dict[str, Any]:
        """Route with timeout, parse-fallback, and clarify counting (SPEC-C-007).

        Args:
            llm_callable: Zero-arg callable returning raw LLM text.
            clarify_count: Consecutive clarify count *before* this call.
            timeout_seconds: Hard timeout on the LLM call (default 3 s).

        Returns::

            {
                "action": str,
                "params": dict,
                "events": list[dict],
                "clarify_count": int,       # updated count after this call
                "candidate_actions": list[str] | None,
            }
        """
        raw, timed_out = _call_with_timeout(llm_callable, timeout_seconds)
        if timed_out:
            return _make_clarify_result(clarify_count, reason="timeout")

        try:
            parsed = json.loads(raw) if raw else None
            if not isinstance(parsed, dict) or "action" not in parsed:
                raise ValueError("bad structure")
            action = str(parsed["action"])
            if action not in self.AVAILABLE_ACTIONS:
                # confirm_next and unknown actions degrade to clarify (SPEC-4.6 / AC-6)
                raise ValueError(f"unknown action: {action!r}")
            if action == "clarify":
                new_count = clarify_count + 1
                return {
                    "action": "clarify",
                    "params": parsed.get("params", {}),
                    "events": [],
                    "clarify_count": new_count,
                    "candidate_actions": (
                        list(_CANDIDATE_ACTIONS) if new_count >= _CLARIFY_TRIGGER else None
                    ),
                }
            return {
                "action": action,
                "params": parsed.get("params", {}),
                "events": [],
                "clarify_count": 0,
                "candidate_actions": None,
            }
        except (ValueError, TypeError):
            return _make_clarify_result(clarify_count, reason="parse_failed")

    def classify(self, utterance: str) -> dict[str, Any]:
        """Rule-based classifier shortcut for the @router BDD evaluation
        bucket.

        Contract (rule order — most specific first):
          1. utterance contains a regenerate keyword -> regenerate_section
             (full scope, generate_artifact ledger entry).
          2. utterance contains an advance keyword -> clarify with
             ``highlight_confirm_button=True`` and a gate-block hint.
             SPEC-4.6 forbids a real advance action from the router; the
             frontend hard button is the only legitimate entry point.
          3. utterance contains '第N段' + ('改' or '更') -> revise.
          4. otherwise -> clarify fallback.

        ``highlight_confirm_button`` is meaningful ONLY when paired with
        ``action == "clarify"``. Frontends MUST NOT key off this field for
        non-clarify actions; the BDD matcher enforces this pairing.
        """
        if any(kw in utterance for kw in _REGENERATE_KEYWORDS):
            return {
                "action": "regenerate_section",
                "params": {"scope": "full"},
                "task_ledger": [{"type": "generate_artifact", "scope": "full"}],
            }

        if any(kw in utterance for kw in _ADVANCE_KEYWORDS):
            return {
                "action": "clarify",
                "params": {},
                "task_ledger": [],
                "highlight_confirm_button": True,
                "gate_satisfied": False,
                "button_disabled_reason": "等待门禁条件满足",
                "reply_to_user": "请点击「确认进入下一阶段」按钮推进",
            }

        m = _SEGMENT_RE.search(utterance)
        if m and ("改" in utterance or "更" in utterance):
            segment = m.group(0)
            return {
                "action": "revise",
                "params": {
                    "target": segment,
                    "instruction": utterance,
                },
                "task_ledger": [{"type": "user_revision", "target": segment}],
            }

        # Substantive input that is not a question: the user is providing
        # requirements context rather than needing clarification.
        if len(utterance) >= _MIN_SUBSTANTIVE_CHARS and not _QUESTION_PATTERN.search(utterance):
            return {
                "action": "refine_requirements",
                "params": {"user_input": utterance},
                "task_ledger": [{"type": "user_refine_requirements"}],
            }

        return {"action": "clarify", "params": {}, "task_ledger": []}


# -- v3.16 action params registry (SPEC-C-101) ---------------------------

ACTION_PARAM_SCHEMAS: dict[str, type[Any]] = {
    "challenge_claim": ChallengeClaimParams,
    "supplement_claim": SupplementClaimParams,
    "request_chart": RequestChartParams,
    "view_phase_detail": ViewPhaseDetailParams,
    "save_stage_preference": SaveStagePreferenceParams,
    "insert_section": InsertSectionParams,
}


# -- v3.16 idempotency-key registry (SPEC-C-101 / C-BDD-2 table) ----------

_SECONDS_PER_MINUTE = 60
_SECONDS_PER_HOUR = 3600
_TTL_24H = 24 * _SECONDS_PER_HOUR
_TTL_1H = 1 * _SECONDS_PER_HOUR
_TTL_5MIN = 5 * _SECONDS_PER_MINUTE


def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_idempotency_key(action: str, params: Any) -> tuple[str, int]:
    """Return the ``(idempotency_key, ttl_seconds)`` pair for ``action``.

    The key uniquely identifies an action+params pair per §C-BDD-2 table;
    callers persist ``(key, ts, result)`` in a cache with ``ttl_seconds``
    and replay the result on collision. TTL ``0`` means the action is not
    idempotency-gated (``view_phase_detail`` — read-only).
    """
    if action == "challenge_claim":
        assert isinstance(params, ChallengeClaimParams), type(params)
        ev_hash = _sha256(params.evidence_url or "")
        return (
            f"challenge_claim:{params.claim_id}:{ev_hash}",
            _TTL_24H,
        )
    if action == "supplement_claim":
        assert isinstance(params, SupplementClaimParams), type(params)
        return (
            f"supplement_claim:{_sha256(params.text)}:{params.source_phase}",
            _TTL_1H,
        )
    if action == "request_chart":
        assert isinstance(params, RequestChartParams), type(params)
        return (
            f"request_chart:{_sha256(params.user_intent)}",
            _TTL_5MIN,
        )
    if action == "view_phase_detail":
        assert isinstance(params, ViewPhaseDetailParams), type(params)
        # Read-only navigation: never persisted, no idempotency key needed.
        return (f"view_phase_detail:{params.phase}", 0)
    if action == "save_stage_preference":
        assert isinstance(params, SaveStagePreferenceParams), type(params)
        stage_part = params.stage or ""
        # upsert key: (scope, stage, key) — no TTL, overwritten on next write.
        return (
            f"save_stage_preference:{params.scope}:{stage_part}:{params.key}",
            0,
        )
    if action == "insert_section":
        assert isinstance(params, InsertSectionParams), type(params)
        anchor_json = json.dumps(
            params.anchor.model_dump(exclude_none=True),
            sort_keys=True,
            ensure_ascii=False,
        )
        return (
            f"insert_section:{_sha256(anchor_json)}:{_sha256(params.content_intent)}",
            _TTL_5MIN,
        )
    raise ValueError(f"unknown action: {action!r}")


# -- SafetyGuard -> Router dispatch gate (SPEC-C-101 AC-3) ----------------

_SAFETY_ALLOWED = frozenset({"allow", "clarify"})


def dispatch_with_safety(
    *,
    user_input: str,
    safety_engine: SafetyPolicyEngine,
    router: IntentRouter,
) -> dict[str, Any]:
    """Gate Router invocation behind ``SafetyPolicyEngine`` (C-BDD-1 + C-BDD-2).

    SPEC-C §C-BDD-1 puts ``SafetyGuard`` *before* the IntentRouter: only
    ``allow`` / ``clarify`` decisions proceed to routing; ``refuse`` /
    ``restrict`` / ``transfer_human`` return the templated safety response
    and MUST NOT invoke the router.

    Return shape (stable, unit-test-asserted):
        {
          "blocked":  bool,
          "decision": <5-level SafetyDecision>,
          "safety_response": str,
          "router_result": <router.classify output | None>,
        }
    """
    decision, safety_response = safety_engine.evaluate(user_input)
    if decision.decision not in _SAFETY_ALLOWED:
        return {
            "blocked": True,
            "decision": decision.decision,
            "safety_response": safety_response,
            "router_result": None,
        }
    router_result = router.classify(user_input)
    return {
        "blocked": False,
        "decision": decision.decision,
        "safety_response": safety_response,
        "router_result": router_result,
    }


__all__ = [
    "ACTION_PARAM_SCHEMAS",
    "AVAILABLE_ACTIONS",
    "IntentRouter",
    "compute_idempotency_key",
    "dispatch_with_safety",
    "load_router_model",
]
