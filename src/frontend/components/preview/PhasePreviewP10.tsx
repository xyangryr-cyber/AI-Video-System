/**
 * [SPEC-GAPFIX-032] P10 Preview — Final video player.
 */
import type { FC } from "react";

export interface PhasePreviewP10Props {
  projectId: string;
}

export const PhasePreviewP10: FC<PhasePreviewP10Props> = ({ projectId }) => {
  return (
    <div className="phase-preview phase-p10" data-testid="phase-p10">
      <h3>Phase 10 — Final Video</h3>
      <p>Project ID: {projectId}</p>
      <section className="phase-preview-body">
        <div className="phase-placeholder">Video player with subtitles</div>
      </section>
    </div>
  );
};

export default PhasePreviewP10;
