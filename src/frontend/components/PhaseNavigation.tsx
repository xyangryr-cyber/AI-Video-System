import type { ReactElement } from "react"
import { ShieldCheck } from "lucide-react"

interface PhaseItem {
  phase: number
  status?: string
  artifact_status?: "ok" | "damaged" | "missing"
}

const PHASE_LABELS = [
  "需求定义", "内容主线", "口播脚本", "脚本润色",
  "人声旁白", "背景音乐", "音效设计", "分镜脚本",
  "关键画面", "B-Roll素材", "粗剪合成", "精剪交付", "最终输出",
]

interface Props {
  currentPhase: number
  phases: PhaseItem[]
  onSelectPhase: (phase: number) => void
  completedPhases: number
  onVeritasClick?: () => void
  hasNewFacts?: boolean
}

export function PhaseNavigation({ currentPhase, phases, onSelectPhase, completedPhases, onVeritasClick, hasNewFacts }: Props): ReactElement {
  const allPhases = phases.length >= 13
    ? phases.slice(0, 13)
    : [...phases, ...Array.from({ length: Math.max(0, 13 - phases.length) }, (_, i) => ({ phase: phases.length + i }) as PhaseItem)]

  return (
    <aside
      data-testid="phase-nav-sidebar"
      className="w-16 bg-white border-2 border-slate-200 rounded-2xl flex flex-col items-center py-6 shrink-0 hidden md:flex shadow-sm"
    >
      <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest vertical-rl rotate-180 mb-6 flex items-center gap-2">
        <div className="w-1 h-1 rounded-full bg-slate-300"></div>
        工作推进
        <div className="w-1 h-1 rounded-full bg-slate-300"></div>
      </div>

      <div className="flex-1 w-full flex flex-col items-center gap-4 overflow-y-auto py-2">
        {allPhases.map((p) => {
          const isCompleted = p.phase < completedPhases
          const isActive = p.phase === currentPhase
          const isCurrent = p.phase === completedPhases && !isActive

          return (
            <button
              key={p.phase}
              onClick={() => onSelectPhase(p.phase)}
              data-testid={`phase-nav-${p.phase}`}
              data-active={p.phase === currentPhase ? "true" : "false"}
              className={`group relative w-10 h-10 flex items-center justify-center rounded-xl transition-all
                ${isActive ? 'bg-[#1e293b] text-white shadow-lg scale-110' : 'text-slate-400 hover:bg-slate-100'}
                ${isCurrent ? 'border-2 border-dashed border-blue-400' : ''}
              `}
            >
              <span className={`text-[11px] font-black ${isActive ? 'opacity-100' : 'opacity-60 group-hover:opacity-100'}`}>
                P{p.phase}
              </span>

              <div className="absolute left-full ml-3 px-2 py-1 bg-[#1e293b] text-white text-[10px] rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity font-bold uppercase tracking-wider shadow-xl">
                {PHASE_LABELS[p.phase] ?? `Phase ${p.phase}`}
              </div>

              {isCompleted && (
                <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white shadow-sm"></div>
              )}
            </button>
          )
        })}
      </div>

      <div className="mt-auto pt-4 border-t border-slate-100 w-full flex flex-col items-center">
        <button
          onClick={onVeritasClick}
          className={`group relative w-10 h-10 flex items-center justify-center rounded-xl transition-all
            ${onVeritasClick ? 'bg-slate-50 text-slate-400 hover:bg-slate-200 cursor-pointer' : 'bg-slate-50 text-slate-400'}
          `}
          title="事实清单 (Veritas)"
        >
          <ShieldCheck className="w-5 h-5 text-slate-500" />
          {hasNewFacts && (
            <span className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full border-2 border-white animate-pulse"></span>
          )}
          <div className="absolute left-full ml-3 px-2 py-1 bg-[#1e293b] text-white text-[10px] rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity font-bold uppercase tracking-wider shadow-xl">
            事实清单 (Veritas)
          </div>
        </button>
      </div>
    </aside>
  )
}
