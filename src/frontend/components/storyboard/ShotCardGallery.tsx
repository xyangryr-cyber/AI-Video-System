import type { ReactElement } from "react";
import { ModeChip } from "./ModeChip";
import type { ShotCard } from "../StoryboardEditor";

export interface ShotCardGalleryProps {
  shots: ShotCard[];
  selectedShotId?: string;
  onShotSelect: (shotId: string) => void;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function sceneTypeColor(type: string): string {
  const colors: Record<string, string> = {
    intro: "#dbeafe",
    main: "#d1fae5",
    outro: "#fce7f3",
    transition: "#fef3c7",
    highlight: "#ede9fe",
  };
  return colors[type] ?? "#f3f4f6";
}

export function ShotCardGallery({
  shots,
  selectedShotId,
  onShotSelect,
}: ShotCardGalleryProps): ReactElement {
  return (
    <div
      data-testid="shot-card-gallery"
      style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "12px" }}
    >
      {shots.map((shot) => {
        const isSelected = shot.id === selectedShotId;
        return (
          <div
            key={shot.id}
            data-testid={`shot-card-${shot.id}`}
            role="button"
            tabIndex={0}
            onClick={() => onShotSelect(shot.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                onShotSelect(shot.id);
              }
            }}
            aria-pressed={isSelected}
            style={{
              padding: "10px 12px",
              border: isSelected ? "2px solid #3b82f6" : "1px solid #e5e7eb",
              borderRadius: "8px",
              backgroundColor: isSelected ? "#eff6ff" : "#ffffff",
              cursor: "pointer",
            }}
          >
            {/* Top row: scene_type badge + mode chip */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "6px",
              }}
            >
              <span
                data-testid={`shot-card-${shot.id}-scene_type`}
                style={{
                  display: "inline-block",
                  padding: "2px 6px",
                  fontSize: "11px",
                  fontWeight: 600,
                  borderRadius: "4px",
                  backgroundColor: sceneTypeColor(shot.scene_type),
                  color: "#374151",
                }}
              >
                {shot.scene_type}
              </span>
              <span data-testid={`shot-card-${shot.id}-mode`}>
                <ModeChip mode={shot.preview_state} />
              </span>
            </div>

            {/* Description */}
            <div style={{ fontSize: "13px", color: "#374151", marginBottom: "4px" }}>
              {shot.description}
            </div>

            {/* Bottom row: duration + claim count */}
            <div style={{ display: "flex", gap: "12px", fontSize: "12px", color: "#6b7280" }}>
              <span data-testid={`shot-card-${shot.id}-duration`}>
                {formatDuration(shot.duration_sec)}
              </span>
              <span data-testid={`shot-card-${shot.id}-claim_count`}>
                {shot.claim_count} claims
              </span>
            </div>

            {/* Placeholder preview */}
            <div
              data-testid={`shot-card-${shot.id}-preview`}
              style={{
                height: "60px",
                marginTop: "6px",
                backgroundColor: "#f3f4f6",
                borderRadius: "4px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "11px",
                color: "#9ca3af",
              }}
            >
              preview
            </div>
          </div>
        );
      })}
    </div>
  );
}
