/**
 * [SPEC-GAPFIX-032] P5 Preview — Waveform visualization.
 */
import type { FC } from "react";

export interface PhasePreviewP5Props {
  projectId: string;
}

export const PhasePreviewP5: FC<PhasePreviewP5Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p5" data-testid="phase-p5">
      <h3>Phase 5 — Waveform</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">Audio waveform visualization</div>
      </section>
    </div>
  );
};

export default PhasePreviewP5;
