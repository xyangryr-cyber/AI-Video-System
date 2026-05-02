/**
 * [SPEC-GAPFIX-032] P4 Preview — TTS audio generation / segment playback.
 */
import type { FC } from "react";

export interface PhasePreviewP4Props {
  projectId: string;
}

export const PhasePreviewP4: FC<PhasePreviewP4Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p4" data-testid="phase-p4">
      <h3>Phase 4 — TTS Audio</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">Audio segments with playback</div>
      </section>
    </div>
  );
};

export default PhasePreviewP4;
