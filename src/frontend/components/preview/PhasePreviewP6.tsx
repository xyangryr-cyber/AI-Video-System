/**
 * [SPEC-GAPFIX-032] P6 Preview — SFX mix interface.
 */
import type { FC } from "react";

export interface PhasePreviewP6Props {
  projectId: string;
}

export const PhasePreviewP6: FC<PhasePreviewP6Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p6" data-testid="phase-p6">
      <h3>Phase 6 — SFX Mix</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">SFX timeline with audio triggers</div>
      </section>
    </div>
  );
};

export default PhasePreviewP6;
