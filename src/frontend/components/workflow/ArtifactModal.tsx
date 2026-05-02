import type { ReactElement } from "react";
import { useArtifact } from "@frontend/hooks/useArtifact";
import { PhasePreviewRouter } from "@frontend/components/previews/PhasePreviewRouter";

interface ArtifactModalProps {
  open: boolean;
  projectId: string;
  phaseIndex: number;
  phaseLabel: string;
  onClose: () => void;
}

export function ArtifactModal({
  open,
  projectId,
  phaseIndex,
  phaseLabel,
  onClose,
}: ArtifactModalProps): ReactElement | null {
  const { data: artifactData } = useArtifact(projectId, phaseIndex);
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      data-testid="artifact-modal"
    >
      <div
        data-testid="modal-backdrop"
        aria-hidden="true"
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-md transition-opacity cursor-pointer"
        onClick={onClose}
      />

      <div className="relative bg-white w-full max-w-4xl max-h-[85vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden workflow-modal-enter">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex flex-col">
            <h3 className="text-sm font-black text-slate-800 uppercase tracking-widest flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              阶段产物预览 / P{phaseIndex}
            </h3>
            <p className="text-xs font-bold text-slate-500 mt-1">{phaseLabel}</p>
          </div>
          <button
            type="button"
            aria-label="关闭弹窗"
            onClick={onClose}
            className="p-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-slate-500 transition-colors"
          >
            关闭
          </button>
        </div>

        <div className="flex-1 overflow-y-auto bg-[#fcfcfc] p-6 relative">
          <PhasePreviewRouter phase={phaseIndex} artifactData={artifactData ?? null} />
        </div>
      </div>
    </div>
  );
}
