import { type ReactElement, useState, useCallback } from "react";
import { ScriptPane } from "./storyboard/ScriptPane";
import type { ScriptPaneAnchor } from "./storyboard/ScriptPane";
import { ShotCardGallery } from "./storyboard/ShotCardGallery";

export interface ShotCard {
  id: string;
  description: string;
  duration_sec: number;
  template_id: string;
  anchor_text: string;
  anchor_start: number;
  anchor_end: number;
  scene_type: string;
  claim_count: number;
  preview_state: "preview" | "production";
  preview_url?: string;
}

export interface StoryboardEditorProps {
  project_id: string;
  shots: ShotCard[];
  polished_script: string;
  selected_shot_id?: string;
  onShotSelect?: (shot_id: string) => void;
  onShotSplit?: (shot_id: string, split_offset: number) => void;
}

export function StoryboardEditor({
  project_id: _projectId,
  shots,
  polished_script,
  selected_shot_id: externalSelectedId,
  onShotSelect,
  onShotSplit,
}: StoryboardEditorProps): ReactElement {
  const [internalSelectedId, setInternalSelectedId] = useState<string | undefined>(
    externalSelectedId,
  );

  const selectedShotId =
    externalSelectedId !== undefined ? externalSelectedId : internalSelectedId;

  const selectedShot = shots.find((s) => s.id === selectedShotId);

  const anchor: ScriptPaneAnchor | undefined = selectedShot
    ? {
        start: selectedShot.anchor_start,
        end: selectedShot.anchor_end,
        shotId: selectedShot.id,
      }
    : undefined;

  const midSplitOffset = selectedShot
    ? Math.floor((selectedShot.anchor_start + selectedShot.anchor_end) / 2) -
      selectedShot.anchor_start
    : 0;

  const handleShotSelect = useCallback(
    (shotId: string) => {
      setInternalSelectedId(shotId);
      onShotSelect?.(shotId);
    },
    [onShotSelect],
  );

  const handleSplit = useCallback(
    (offset: number) => {
      if (selectedShotId) {
        onShotSplit?.(selectedShotId, offset);
      }
    },
    [selectedShotId, onShotSplit],
  );

  return (
    <div
      data-testid="storyboard-editor"
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "16px",
        height: "100%",
      }}
    >
      <div style={{ overflowY: "auto", border: "1px solid #e5e7eb", borderRadius: "8px" }}>
        <ScriptPane
          script={polished_script}
          selectedAnchor={anchor}
          splitOffset={selectedShot ? midSplitOffset : undefined}
          onSplit={selectedShot ? handleSplit : undefined}
        />
      </div>
      <div style={{ overflowY: "auto" }}>
        <ShotCardGallery
          shots={shots}
          selectedShotId={selectedShotId}
          onShotSelect={handleShotSelect}
        />
      </div>
    </div>
  );
}
