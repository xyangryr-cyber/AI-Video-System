// [SPEC-A-015] ShotMaterialBindings types (TypeScript mirror).
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-3.
//
// Keep in lockstep with src/shared/schemas/shot_material_bindings.py and
// schemas/shot_material_bindings.schema.json.

export interface ShotBinding {
  shot_id: string; // ^shot_\d{2,}$
  required_materials: string[]; // each matches ^mat_\d{3,}$
  optional_materials: string[]; // each matches ^mat_\d{3,}$
}

export interface ShotMaterialBindings {
  bindings: ShotBinding[];
}
