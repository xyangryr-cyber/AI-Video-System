"""[SPEC-C-021] MaterialFetcher — programmatic + tool-call asset fetch.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-6.

The fetcher bridges a pending MaterialEntry (kind ∈ api/url/internal) to
a file on disk under ``<project_root>/phase_7a/verified_materials/``.
It is programmatic — no LLM call. It does, however, wrap the transport
in the same retry contract as :func:`src.backend.workers.p7a_tasks
.fetch_with_retry` (3 attempts on TransientProviderError) so a single
code path governs both the synchronous V1 test runs and the Huey
fan-out.

Three provider interfaces (dependency-injected; tests supply fakes):

    api_provider.fetch(ref) -> {"payload": bytes, "ext": str}
    url_provider.fetch(ref) -> {"payload": bytes, "ext": str}
    internal_provider.fetch(ref) -> {"payload": bytes, "ext": str}

For ``kind=internal`` the default provider reads bytes from ``ref``
as a local path and derives ``ext`` from the file suffix. Custom
providers can override this behaviour.

Return contract
---------------
``fetch(entry)`` returns a NEW MaterialEntry with ``fetched_at`` set to
a UTC ISO-8601 string. Verification_status is unchanged (verifier owns
that). On exhaustion of retries for api/url kinds, the returned entry
carries ``verification_status=MISSING`` — this matches
SPEC-B-015 AC-4 and is how the orchestrator learns to skip verification
for a dead material.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from src.backend.workers.p7a_tasks import TransientProviderError
from src.shared.schemas.material_manifest import (
    MaterialEntry,
    SourceKind,
    VerificationStatus,
)

_MAX_ATTEMPTS = 3  # SPEC-B-015 material_fetch retries = 3


class _Provider(Protocol):
    def fetch(self, ref: str) -> dict[str, Any]:  # pragma: no cover - protocol
        ...


class _InternalProvider:
    """Default internal-kind provider: read bytes from a local path."""

    def fetch(self, ref: str) -> dict[str, Any]:
        p = Path(ref)
        payload = p.read_bytes()
        ext = p.suffix.lstrip(".") or "bin"
        return {"payload": payload, "ext": ext}


class MaterialFetcher:
    def __init__(
        self,
        *,
        project_root: Path,
        api_provider: _Provider | None = None,
        url_provider: _Provider | None = None,
        internal_provider: _Provider | None = None,
    ) -> None:
        self._root = Path(project_root)
        self._providers: dict[SourceKind, _Provider | None] = {
            SourceKind.API: api_provider,
            SourceKind.URL: url_provider,
            SourceKind.INTERNAL: internal_provider or _InternalProvider(),
        }

    @property
    def verified_dir(self) -> Path:
        return self._root / "phase_7a" / "verified_materials"

    def fetch(self, entry: MaterialEntry) -> MaterialEntry:
        provider = self._providers.get(entry.source.kind)
        if provider is None:
            raise ValueError(
                f"no provider configured for source.kind={entry.source.kind.value}"
            )
        try:
            result = self._fetch_with_retry(provider, entry.source.ref)
        except TransientProviderError:
            # Retry budget exhausted -> terminal missing.
            return entry.model_copy(
                update={
                    "verification_status": VerificationStatus.MISSING,
                    "fetched_at": self._now_iso(),
                }
            )

        payload = result["payload"]
        ext = result.get("ext") or "bin"
        self.verified_dir.mkdir(parents=True, exist_ok=True)
        out = self.verified_dir / f"{entry.material_id}.{ext}"
        out.write_bytes(payload)

        return entry.model_copy(update={"fetched_at": self._now_iso()})

    @staticmethod
    def _fetch_with_retry(provider: _Provider, ref: str) -> dict[str, Any]:
        last_err: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                return provider.fetch(ref)
            except TransientProviderError as err:
                last_err = err
                if attempt == _MAX_ATTEMPTS - 1:
                    raise
        # Unreachable; loop either returns or raises on the last iteration.
        raise TransientProviderError(  # pragma: no cover
            f"fetch exhausted: {last_err}"
        )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


__all__ = ["MaterialFetcher"]
