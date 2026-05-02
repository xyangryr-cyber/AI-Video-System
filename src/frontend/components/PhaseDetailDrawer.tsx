import type { ReactElement } from "react";
import { ArtifactList } from "./phase_detail/ArtifactList";
import { ReviewerResults } from "./phase_detail/ReviewerResults";
import { GateResult } from "./phase_detail/GateResult";
import { ClaimSnapshot } from "./phase_detail/ClaimSnapshot";
import { PreferenceSnapshot } from "./phase_detail/PreferenceSnapshot";
import { DiffView } from "./phase_detail/DiffView";
import { OperationHistoryTimeline } from "./phase_detail/OperationHistoryTimeline";

// ── Shared types for PhaseDetailView ──

export interface ArtifactEntry {
  name: string;
  version: number;
  url: string;
}

export interface ReviewerResult {
  reviewer: string;
  verdict: string;
  notes: string;
}

export interface GateCheckResult {
  check_name: string;
  passed: boolean;
  reason?: string;
}

export interface ClaimSnapshotEntry {
  claim_id: string;
  status: string;
  blocking_level: string;
}

export interface PreferenceSnapshotEntry {
  scope: string;
  key: string;
  value: string;
}

export interface DiffEntry {
  field: string;
  change_type: "added" | "removed" | "modified";
  old_value?: string;
  new_value?: string;
}

export interface TimelineEvent {
  timestamp: string;
  operator: string;
  action: string;
}

export interface PhaseDetailView {
  artifacts: ArtifactEntry[];
  reviewer_results: ReviewerResult[];
  gate_results: GateCheckResult[];
  claim_snapshot: ClaimSnapshotEntry[];
  preference_snapshot: PreferenceSnapshotEntry[];
  diff_from_prev: DiffEntry[];
  operation_timeline: TimelineEvent[];
}

// ── Props ──

interface PhaseDetailDrawerProps {
  projectId: string;
  phaseNumber: number;
  phaseData: PhaseDetailView | null;
  readOnly: boolean;
  onRevert: (phase: number) => Promise<void>;
  onClose: () => void;
  open: boolean;
}

// ── Component ──

export function PhaseDetailDrawer({
  projectId: _projectId,
  phaseNumber,
  phaseData,
  readOnly,
  onRevert,
  onClose,
  open,
}: PhaseDetailDrawerProps): ReactElement {
  if (!open) {
    return <></>;
  }

  const handleRevert = async () => {
    if (!window.confirm(`Roll back to Phase ${phaseNumber} and continue editing from this stage?`)) {
      return;
    }
    await onRevert(phaseNumber);
    onClose();
  };

  return (
    <div data-testid="phase-detail-drawer" className="fixed inset-y-0 right-0 w-96 bg-white shadow-lg z-50 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <h2 className="text-lg font-bold">
          Phase P{phaseNumber} Detail
          {readOnly && (
            <span className="ml-2 text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">
              Read Only
            </span>
          )}
        </h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          aria-label="Close drawer"
        >
          x
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <ArtifactList artifacts={phaseData?.artifacts} readOnly={readOnly} />
        <ReviewerResults results={phaseData?.reviewer_results} readOnly={readOnly} />
        <GateResult results={phaseData?.gate_results} readOnly={readOnly} />
        <ClaimSnapshot claims={phaseData?.claim_snapshot} readOnly={readOnly} />
        <PreferenceSnapshot preferences={phaseData?.preference_snapshot} readOnly={readOnly} />
        <DiffView diffs={phaseData?.diff_from_prev} readOnly={readOnly} />
        <OperationHistoryTimeline events={phaseData?.operation_timeline} readOnly={readOnly} />
      </div>

      {/* Footer */}
      {readOnly && (
        <div className="p-4 border-t">
          <button
            onClick={handleRevert}
            className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
从此阶段继续修改
          </button>
        </div>
      )}
    </div>
  );
}
