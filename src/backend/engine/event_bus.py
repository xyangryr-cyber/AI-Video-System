"""[SPEC-C-001] EventBus -- stateless helper for writing WS events.

SPEC-3.1 requires that ``EventBus`` is a pure function with no hidden
subscriber state and no module-level registry. This module exposes a
single class whose ``publish`` is a ``@staticmethod``; the class exists
only as an import namespace and carries no instance attributes.

The entry point takes an ``EventSink`` callable rather than owning a
DB connection, so the bus stays testable in isolation and so payload
validation (against ``src/shared/schemas/events.py``) can run before
any side effect.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from src.shared.constants.event_types import EventType
from src.shared.schemas.events import validate_event_payload

EventSink = Callable[[str, str, str], int]
"""Contract: ``(project_id, event_type_value, payload_json) -> row_id``.

``WorkflowEngine`` supplies a connection-backed implementation; tests
may inject a capture list or raise to prove error handling.
"""


class EventBus:
    """Namespace for stateless event dispatch helpers."""

    __slots__ = ()

    @staticmethod
    def publish(
        sink: EventSink,
        project_id: str,
        event_type: EventType,
        payload: Mapping[str, Any],
    ) -> int:
        """Validate ``payload`` against SPEC-11A schemas and forward it
        to ``sink``. Returns the inserted event row id.

        Raises:
            KeyError: ``event_type`` has no registered payload model.
            pydantic.ValidationError: payload violates the schema.
        """
        payload_dict: dict[str, Any] = dict(payload)
        validate_event_payload(event_type, payload_dict)
        return sink(project_id, event_type.value, json.dumps(payload_dict))


__all__ = ["EventBus", "EventSink"]
