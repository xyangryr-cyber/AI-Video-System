import type { ReactElement } from "react";
import { ArrowLeft } from "lucide-react";

interface ArtifactListProps {
  phaseLabels: readonly string[];
  currentPhase: number;
  onSelect: (phaseIndex: number) => void;
}

export function ArtifactList({
  phaseLabels,
  currentPhase,
  onSelect,
}: ArtifactListProps): ReactElement {
  const ordered = phaseLabels
    .map((phaseName, i) => ({ phaseName, originalIndex: i }))
    .filter(({ originalIndex }) => originalIndex <= currentPhase)
    .reverse();

  return (
    <section className="flex-[3] bg-white border-2 border-slate-200 rounded-2xl flex flex-col min-h-0 overflow-hidden shadow-sm relative group">
      <div className="px-5 py-4 border-b border-slate-100 bg-white flex justify-between items-center shrink-0">
        <h2 className="text-[0.75rem] font-black text-[#1e293b] uppercase tracking-[0.1em] flex items-center">
          <span className="w-2.5 h-2.5 rounded-sm bg-blue-600 mr-2"></span>
          阶段产物 (ARTIFACTS)
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 bg-slate-50">
        <div className="w-full flex flex-col gap-2" data-testid="artifact-list">
          {ordered.map(({ phaseName, originalIndex: index }) => {
            const isCurrent = index === currentPhase;
            return (
              <button
                key={index}
                type="button"
                aria-label={`查看阶段 ${index} 产物`}
                onClick={() => onSelect(index)}
                className="w-full text-left bg-white border-2 border-slate-100 rounded-xl p-4 hover:border-blue-400 hover:shadow-md transition-all flex justify-between items-center group"
              >
                <div>
                  <div className="text-[10px] font-bold text-slate-400 mb-1">
                    PHASE {index}
                    {isCurrent && (
                      <span
                        data-testid="in-progress-badge"
                        className="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded uppercase font-black tracking-widest text-[8px]"
                      >
                        In Progress
                      </span>
                    )}
                  </div>
                  <div className="text-sm font-bold text-slate-800">{phaseName}</div>
                </div>
                <div className="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center group-hover:bg-blue-50 transition-colors">
                  <ArrowLeft className="w-4 h-4 text-slate-400 group-hover:text-blue-600 rotate-180" />
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
