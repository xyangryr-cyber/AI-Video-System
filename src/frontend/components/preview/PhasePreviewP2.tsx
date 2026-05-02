/**
 * [SPEC-GAPFIX-032] P2 Preview — Script generation / data point anchoring.
 */
import type { FC } from "react";

export interface PhasePreviewP2Props {
  projectId: string;
}

export const PhasePreviewP2: FC<PhasePreviewP2Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p2" data-testid="phase-p2">
      <h3>Phase 2 — Script Generation</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">Script segments with key data points</div>
      </section>
    </div>
  );
};

export default PhasePreviewP2;
