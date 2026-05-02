// [SPEC-E-015] ShotMaterialBindingView — frontend View type mirroring ShotMaterialBindings.
// Keep in lockstep with src/shared/types/shot_material_bindings.ts and SPEC-A-015.
export interface ShotBinding {
  shot_id: string;
  required_materials: string[];
  optional_materials: string[];
}

export interface ShotMaterialBindingView {
  bindings: ShotBinding[];
}
