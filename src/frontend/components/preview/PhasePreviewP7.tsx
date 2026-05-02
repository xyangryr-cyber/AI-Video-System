/**
 * [SPEC-GAPFIX-032] P7 Preview — Storyboard view.
 */
import type { FC } from "react";

export interface PhasePreviewP7Props {
  projectId: string;
}

export const PhasePreviewP7: FC<PhasePreviewP7Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p7" data-testid="phase-p7">
      <h3>Phase 7 — Storyboard</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">Storyboard shots grid</div>
      </section>
    </div>
  );
};

export default PhasePreviewP7;
