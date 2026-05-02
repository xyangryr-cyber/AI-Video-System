/**
 * [SPEC-GAPFIX-032] P0 Preview — Requirements input form view.
 * Displays structured requirements JSON for the project.
 */
import type { FC } from "react";

export interface PhasePreviewP0Props {
  projectId: string;
}

export const PhasePreviewP0: FC<PhasePreviewP0Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p0" data-testid="phase-p0">
      <h3>Phase 0 — Requirements</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">Requirements form view</div>
      </section>
    </div>
  );
};

export default PhasePreviewP0;
