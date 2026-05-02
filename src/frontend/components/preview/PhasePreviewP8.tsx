/**
 * [SPEC-GAPFIX-032] P8 Preview — Keyframe render gallery.
 */
import type { FC } from "react";

export interface PhasePreviewP8Props {
  projectId: string;
}

export const PhasePreviewP8: FC<PhasePreviewP8Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p8" data-testid="phase-p8">
      <h3>Phase 8 — Keyframe Render</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">Video frame gallery</div>
      </section>
    </div>
  );
};

export default PhasePreviewP8;
