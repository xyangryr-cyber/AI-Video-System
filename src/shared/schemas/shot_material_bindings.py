"""[SPEC-A-015] ShotMaterialBindings schema (Pydantic).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-3.

Companion of `material_manifest.json`. The cross-artifact invariant
(AC-3) is enforced by `validate_bindings_against_manifest(bindings,
manifest)`: every material_id listed in `required_materials` or
`optional_materials` MUST exist in `manifest.materials[].material_id`.

Keep in lockstep with `schemas/shot_material_bindings.schema.json` and
`src/shared/types/shot_material_bindings.ts`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.shared.schemas.material_manifest import MaterialManifest

_MATERIAL_ID_RE = r"^mat_\d{3,}$"
_SHOT_ID_RE = r"^shot_\d{2,}$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ShotBinding(_Strict):
    shot_id: str = Field(pattern=_SHOT_ID_RE)
    required_materials: list[str] = Field(default_factory=list)
    optional_materials: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: object) -> None:
        import re

        pat = re.compile(_MATERIAL_ID_RE)
        for bucket_name, bucket in (
            ("required_materials", self.required_materials),
            ("optional_materials", self.optional_materials),
        ):
            for mid in bucket:
                if not pat.match(mid):
                    raise ValueError(
                        f"{bucket_name} contains invalid material_id {mid!r} "
                        f"(expected pattern {_MATERIAL_ID_RE})"
                    )


class ShotMaterialBindings(_Strict):
    bindings: list[ShotBinding]


def validate_bindings_against_manifest(
    bindings: ShotMaterialBindings,
    manifest: MaterialManifest,
) -> None:
    """AC-3 cross-artifact invariant.

    Every material_id in `bindings.bindings[].required_materials` or
    `bindings.bindings[].optional_materials` MUST be present in
    `manifest.materials[].material_id`. Raises ValueError listing every
    orphan reference.
    """
    known = {m.material_id for m in manifest.materials}
    orphans: list[tuple[str, str, str]] = []
    for b in bindings.bindings:
        for mid in b.required_materials:
            if mid not in known:
                orphans.append((b.shot_id, "required", mid))
        for mid in b.optional_materials:
            if mid not in known:
                orphans.append((b.shot_id, "optional", mid))
    if orphans:
        details = ", ".join(f"{s}:{bucket}={m}" for s, bucket, m in orphans)
        raise ValueError(
            "shot_material_bindings references material_id(s) not in "
            f"material_manifest.materials: {details}"
        )


__all__ = [
    "ShotBinding",
    "ShotMaterialBindings",
    "validate_bindings_against_manifest",
]
