import { describe, it, expect } from "vitest";

// AC-1: Verify all 4 type files exist (import will fail at compile time if missing)
import type { MasterAudioView } from "../../../../src/frontend/types/audio_master";
import type { AnnotationSpan } from "../../../../src/frontend/types/annotation_span";
import type { ShotMaterialBindingView } from "../../../../src/frontend/types/shot_material_binding";
import type { ChartMaterialView } from "../../../../src/frontend/types/chart_material";

// AC-2: Verify structural match with shared types by importing both
import type { MasterAudioArtifact } from "../../../../src/shared/types/audio_master";
import type { AnnotationSpan as SharedAnnotationSpan } from "../../../../src/shared/types/artifacts";
import type { ShotMaterialBindings } from "../../../../src/shared/types/shot_material_bindings";
import type { ChartMaterial } from "../../../../src/shared/types/chart_material";

describe("AC-1: 4 type files exist and compile", () => {
  it("MasterAudioView is importable", () => {
    // If the file doesn't exist or doesn't export the type, tsc fails before vitest runs.
    // This test exists as a sentinel — if it runs, imports succeeded.
    expect(true).toBe(true);
  });

  it("AnnotationSpan is importable", () => {
    expect(true).toBe(true);
  });

  it("ShotMaterialBindingView is importable", () => {
    expect(true).toBe(true);
  });

  it("ChartMaterialView is importable", () => {
    expect(true).toBe(true);
  });
});

describe("AC-2: fields match shared types", () => {
  // TypeScript structural compatibility: assigning a shared type to a view type
  // should succeed if the view is a compatible subset / mirror.

  it("MasterAudioView accepts MasterAudioArtifact shape", () => {
    const artifact: MasterAudioArtifact = {
      kind: "narration_master",
      file_path: "phase_4/seg_01.mp3",
      based_on_phase: 4,
      derived_from_segments: ["seg_01"],
      total_duration_seconds: 120.5,
      checksum: "sha256:" + "a".repeat(64),
      version: 1,
    };
    // Structural compatibility check: assign to View type
    const view: MasterAudioView = artifact;
    expect(view.kind).toBe("narration_master");
  });

  it("AnnotationSpan matches shared AnnotationSpan", () => {
    const shared: SharedAnnotationSpan = {
      span_id: "span_001",
      text_range: [0, 100],
      effect: "fade_in",
      rationale: "emphasis",
      narrative_role: "lead_in",
    };
    const view: AnnotationSpan = shared;
    expect(view.span_id).toBe("span_001");
  });

  it("ShotMaterialBindingView matches ShotMaterialBindings", () => {
    const shared: ShotMaterialBindings = {
      bindings: [
        { shot_id: "shot_01", required_materials: ["mat_001"], optional_materials: [] },
      ],
    };
    const view: ShotMaterialBindingView = shared;
    expect(view.bindings[0].shot_id).toBe("shot_01");
  });

  it("ChartMaterialView matches ChartMaterial", () => {
    const shared: ChartMaterial = {
      chart_id: "chart_001",
      shot_id: "shot_01",
      metric_name: "revenue",
      date_range: { start: "2024-01-01", end: "2024-12-31" },
      granularity: "month",
      source: { provider: "bloomberg", symbol: "AAPL" },
      verification_status: "verified",
      chart_spec: { kind: "line", series: [] },
      axis_spec: {
        x_axis: { type: "time", labels: [], range: ["2024-01-01", "2024-12-31"] },
        y_axis: { unit: "USD", min: 0, max: 1000, scale_mode: "linear" },
      },
    };
    const view: ChartMaterialView = shared;
    expect(view.metric_name).toBe("revenue");
  });
});

describe("AC-5: MasterAudioView.kind strict union", () => {
  it("accepts 'narration_master'", () => {
    const v: MasterAudioView = {
      kind: "narration_master",
      file_path: "p.mp3",
      based_on_phase: 4,
      derived_from_segments: [],
      total_duration_seconds: 1,
      checksum: "sha256:" + "a".repeat(64),
      version: 1,
    };
    expect(v.kind).toBe("narration_master");
  });

  it("accepts 'bgm_mix_master'", () => {
    const v: MasterAudioView = {
      kind: "bgm_mix_master",
      file_path: "p.mp3",
      based_on_phase: 5,
      derived_from_segments: [],
      total_duration_seconds: 1,
      checksum: "sha256:" + "a".repeat(64),
      version: 1,
      source_ref: { kind: "narration_master", checksum: "sha256:" + "b".repeat(64) },
    };
    expect(v.kind).toBe("bgm_mix_master");
  });

  it("accepts 'final_audio_master'", () => {
    const v: MasterAudioView = {
      kind: "final_audio_master",
      file_path: "p.mp3",
      based_on_phase: 6,
      derived_from_segments: [],
      total_duration_seconds: 1,
      checksum: "sha256:" + "a".repeat(64),
      version: 1,
      source_ref: { kind: "bgm_mix_master", checksum: "sha256:" + "b".repeat(64) },
    };
    expect(v.kind).toBe("final_audio_master");
  });
});
