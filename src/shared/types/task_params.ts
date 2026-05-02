// [SPEC-A-007] task_ledger.params -- TypeScript mirror of SPEC-1B schemas.
// Authority: SPEC-A-contracts.md SPEC-1B. Keep in lockstep with
// src/shared/schemas/task_params.py.

export type TaskType =
  | "generate_artifact"
  | "regenerate_section"
  | "user_revision"
  | "review"
  | "research"
  | "verify"
  | "cross_check"
  | "user_annotation";

export interface GenerateArtifactParams {
  phase_name: string;
  input_refs: string[];
}

export interface RegenerateSectionParams {
  phase_name: string;
  section_id: string;
  instruction: string;
}

export interface UserRevisionParams {
  phase_name: string;
  revision_text: string;
  target_section?: string;
}

export interface ReviewParams {
  phase_name: string;
  reviewer_name: string;
  artifact_path: string;
}

export interface ResearchParams {
  query: string;
  // Range: 3..5 (inclusive) -- validated server-side.
  max_sources: number;
}

export interface VerifyParams {
  data_point_id: string;
  claimed_value: string;
  source_url: string;
}

export interface CrossCheckParams {
  left_ref: string;
  right_ref: string;
  check_fields: string[];
}

export interface UserAnnotationParams {
  frame: number;
  time_sec: number;
  text: string;
}

export type TaskParamsByType = {
  generate_artifact: GenerateArtifactParams;
  regenerate_section: RegenerateSectionParams;
  user_revision: UserRevisionParams;
  review: ReviewParams;
  research: ResearchParams;
  verify: VerifyParams;
  cross_check: CrossCheckParams;
  user_annotation: UserAnnotationParams;
};

export type TaskParams = TaskParamsByType[TaskType];
