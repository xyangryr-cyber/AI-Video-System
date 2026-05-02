/**
 * [SPEC-GAPFIX-032] P1 Preview — Voice direction / tone & pace selector.
 */
import type { FC } from "react";

export interface PhasePreviewP1Props {
  projectId: string;
}

export const PhasePreviewP1: FC<PhasePreviewP1Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p1" data-testid="phase-p1">
      <h3>Phase 1 — Voice Direction</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">Voice tone / pace / style selector</div>
      </section>
    </div>
  );
};

export default PhasePreviewP1;
