"""[SPEC-C-021] MaterialManifest on-disk repository.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-6;
schema authority: :mod:`src.shared.schemas.material_manifest` (A-015).

The P7A pipeline stores one canonical manifest at
``<project_root>/phase_7a/material_manifest.json``. Three agents mutate
the file in a strict sequence:

  StoryboardAssetPlanner -> initial write (PENDING rows).
  MaterialFetcher        -> per-material fetched_at update.
  MaterialVerifier       -> per-material verification_status update
                            (state machine enforced via A-015).

This class owns that JSON file. It is intentionally thin: no locking
beyond the atomic ``tmp-then-rename`` write; the orchestrator is
responsible for sequencing fetch/verify calls so two writers never touch
the same row concurrently in V1.
"""

from __future__ import annotations

import os
from pathlib import Path

from src.shared.schemas.material_manifest import MaterialEntry, MaterialManifest

_MANIFEST_NAME = "material_manifest.json"


class MaterialManifestRepo:
    """Read / write the phase_7a material manifest."""

    def __init__(self, project_root: Path) -> None:
        self._root = Path(project_root)
        self._path = self._root / "phase_7a" / _MANIFEST_NAME

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> MaterialManifest | None:
        if not self._path.exists():
            return None
        return MaterialManifest.model_validate_json(self._path.read_text(encoding="utf-8"))

    def save(self, manifest: MaterialManifest) -> None:
        """Atomic write: tmp file + rename."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(
            manifest.model_dump_json(indent=2, exclude_none=False),
            encoding="utf-8",
        )
        os.replace(tmp, self._path)

    def replace_entry(self, entry: MaterialEntry) -> MaterialManifest:
        """Persist a single MaterialEntry update (by material_id).

        Raises KeyError if the manifest is missing, or if ``material_id``
        is not present. Returns the persisted manifest.
        """
        manifest = self.load()
        if manifest is None:
            raise KeyError("material_manifest.json is missing; call save() first")
        replaced = False
        new_materials: list[MaterialEntry] = []
        for m in manifest.materials:
            if m.material_id == entry.material_id:
                new_materials.append(entry)
                replaced = True
            else:
                new_materials.append(m)
        if not replaced:
            raise KeyError(f"material_id={entry.material_id!r} not in manifest")
        updated = manifest.model_copy(update={"materials": new_materials})
        self.save(updated)
        return updated


__all__ = ["MaterialManifestRepo"]
