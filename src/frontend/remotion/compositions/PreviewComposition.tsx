// [SPEC-F-102] PreviewComposition -- 480p single-frame preview.
// Shared data from TemplateProps (no fork from production mode).
// Does NOT trigger backend data re-run on mount or mode switch.

import type { FC } from "react";
import type { TemplateProps } from "@shared/types/template_props";
import { getRenderConfig } from "../utils/render_mode_controller";
import ChartTemplate from "../components/ChartTemplate";

export interface PreviewCompositionProps extends TemplateProps {
  // Mode is fixed to 'preview' for this composition.
  // Shared data (data_points, axis_spec, chart_style_overrides)
  // are passed via TemplateProps and NOT duplicated/forked.
}

/**
 * PreviewComposition renders a single frame at 480p.
 *
 * Uses getRenderConfig('preview') for resolution (854x480).
 * Single frame rendering -- no animation loop (fps=1).
 * Data comes from shared TemplateProps, no backend re-fetch.
 */
const PreviewComposition: FC<PreviewCompositionProps> = (props) => {
  const config = getRenderConfig("preview");

  // Single frame: always render frame 0
  // Animation is skipped (per F-BDD-3: initial state as final render)
  return (
    <div
      className="preview-composition"
      style={{
        width: config.width,
        height: config.height,
        overflow: "hidden",
        position: "relative",
      }}
    >
      <ChartTemplate
        {...props}
        source_verified={false}
      />
    </div>
  );
};

export default PreviewComposition;
