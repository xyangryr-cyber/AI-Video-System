// [SPEC-F-102] ProductionComposition -- 1080p full animation render.
// Shared data from TemplateProps (no fork from preview mode).
// Does NOT trigger backend data re-run on mount or mode switch.

import type { FC } from "react";
import type { TemplateProps } from "@shared/types/template_props";
import { getRenderConfig } from "../utils/render_mode_controller";
import ChartTemplate from "../components/ChartTemplate";

export interface ProductionCompositionProps extends TemplateProps {
  // Mode is fixed to 'production' for this composition.
  // Shared data (data_points, axis_spec, chart_style_overrides)
  // are passed via TemplateProps and NOT duplicated/forked.
}

/**
 * ProductionComposition renders full animation at 1080p.
 *
 * Uses getRenderConfig('production') for resolution (1920x1080).
 * Full animation -- fps=30, all frames rendered.
 * Data comes from shared TemplateProps, no backend re-fetch.
 */
const ProductionComposition: FC<ProductionCompositionProps> = (props) => {
  const config = getRenderConfig("production");

  return (
    <div
      className="production-composition"
      style={{
        width: config.width,
        height: config.height,
        overflow: "hidden",
        position: "relative",
      }}
    >
      <ChartTemplate
        {...props}
        source_verified={true}
      />
    </div>
  );
};

export default ProductionComposition;
