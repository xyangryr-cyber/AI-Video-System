// [SPEC-F-012] LayerToggle — 4-layer decomposition toggles.
// Layers: text, data, visual, audio.
// Each toggle immediately changes visibleLayers for instant feedback.

import type { FC } from "react";

export type LayerName = "text" | "data" | "visual" | "audio";

export interface VisibleLayers {
  text: boolean;
  data: boolean;
  visual: boolean;
  audio: boolean;
}

export interface LayerToggleProps {
  /** Current layer visibility state */
  visibleLayers: VisibleLayers;
  /** Callback when a layer toggle changes */
  onToggle: (layer: LayerName) => void;
}

const ALL_LAYERS: LayerName[] = ["text", "data", "visual", "audio"];

const LAYER_LABELS: Record<LayerName, string> = {
  text: "Text",
  data: "Data",
  visual: "Visual",
  audio: "Audio",
};

const LAYER_COLORS: Record<LayerName, string> = {
  text: "#e94560",
  data: "#0f3460",
  visual: "#16213e",
  audio: "#533483",
};

/**
 * LayerToggle renders 4 toggle buttons for text/data/visual/audio layers.
 * Each toggle immediately updates visibleLayers (AC-4).
 */
const LayerToggle: FC<LayerToggleProps> = ({ visibleLayers, onToggle }) => {
  return (
    <div
      className="layer-toggles"
      style={{
        display: "flex",
        gap: 8,
        padding: 8,
        backgroundColor: "rgba(0,0,0,0.6)",
        borderRadius: 8,
      }}
    >
      {ALL_LAYERS.map((layer) => {
        const active = visibleLayers[layer];
        return (
          <button
            key={layer}
            className={`layer-toggle layer-toggle--${layer} ${active ? "active" : ""}`}
            onClick={() => onToggle(layer)}
            title={`Toggle ${LAYER_LABELS[layer]} layer`}
            style={{
              padding: "6px 16px",
              borderRadius: 4,
              border: `2px solid ${LAYER_COLORS[layer]}`,
              backgroundColor: active ? LAYER_COLORS[layer] : "transparent",
              color: active ? "#fff" : LAYER_COLORS[layer],
              cursor: "pointer",
              fontSize: 13,
              fontWeight: active ? "bold" : "normal",
              opacity: active ? 1 : 0.5,
              transition: "all 100ms ease",
            }}
          >
            {LAYER_LABELS[layer]}
          </button>
        );
      })}
    </div>
  );
};

export default LayerToggle;
