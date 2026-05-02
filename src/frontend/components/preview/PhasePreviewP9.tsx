/**
 * [SPEC-GAPFIX-032] P9 Preview — B-Roll thumbnail grid.
 */
import type { FC } from "react";

export interface PhasePreviewP9Props {
  projectId: string;
}

export const PhasePreviewP9: FC<PhasePreviewP9Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p9" data-testid="phase-p9">
      <h3>Phase 9 — B-Roll</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">B-Roll thumbnail grid</div>
      </section>
    </div>
  );
};

export default PhasePreviewP9;
