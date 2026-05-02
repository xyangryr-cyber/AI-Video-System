import type { ReactElement } from "react"
import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft, Loader2 } from "lucide-react"
import { ChatHistory } from "@frontend/components/workflow/ChatHistory"
import { TaskCard } from "@frontend/components/workflow/TaskCard"
import { ChatInput } from "@frontend/components/workflow/ChatInput"
import { ArtifactList } from "@frontend/components/workflow/ArtifactList"
import { FactualLedger } from "@frontend/components/workflow/FactualLedger"
import { ArtifactModal } from "@frontend/components/workflow/ArtifactModal"
import { useChat } from "@frontend/hooks/useChat"
import { useAdvance } from "@frontend/hooks/useAdvance"
import { PHASE_LABELS } from "@shared/constants/phaseLabels"
import {
  MOCK_CURRENT_TASK_TITLE,
  MOCK_FACTUAL_DATA,
  MOCK_PROJECT_TITLE,
  MOCK_TASKS,
} from "@frontend/components/workflow/mockData"

export function WorkflowPage(): ReactElement {
  const { id = "", phase = "0" } = useParams<{ id: string; phase: string }>()
  const currentPhase = Number(phase)
  const navigate = useNavigate()

  const [modalPhase, setModalPhase] = useState<number | null>(null)
  const [advanceError, setAdvanceError] = useState<string | null>(null)
  const phaseLabel = PHASE_LABELS[currentPhase] ?? `Phase ${currentPhase}`
  const { messages, sendMessage, isLoading: isChatLoading, highlightConfirm, gateSatisfied, gateBlockedReason } = useChat(id)
  const { advance, isAdvancing } = useAdvance(id)

  const handleAdvance = async () => {
    setAdvanceError(null)
    try {
      const res = await advance()
      if (res.status === "advanced" || res.status === "already_advanced") {
        navigate(`/projects/${id}/phases/${res.current_phase}`)
      }
    } catch (e: unknown) {
      const err = e as { message?: string }
      setAdvanceError(err.message ?? "推进失败，请重试")
    }
  }

  const advanceEnabled = highlightConfirm && gateSatisfied
  const advanceDisabled = !advanceEnabled || isAdvancing

  return (
    <div className="h-screen flex flex-col bg-[#f8fafc] overflow-hidden p-4 sm:p-5 gap-5 text-[#1e293b]">
      <div className="flex-1 flex overflow-hidden gap-4">
        <main className="flex-1 flex flex-col min-w-0 z-10 bg-white border-2 border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-white flex justify-between items-center shrink-0">
            <div className="flex items-center space-x-3">
              <button
                type="button"
                aria-label="返回项目列表"
                onClick={() => navigate("/projects")}
                className="p-1.5 text-slate-500 hover:bg-slate-100 rounded-md transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="font-bold text-slate-800 text-base">
                {MOCK_PROJECT_TITLE}
                <span className="text-slate-400 font-normal ml-2 text-xs">
                  {id || "proj_001"}
                </span>
              </div>
            </div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-2 py-1 bg-slate-100 rounded">
              P{currentPhase} · {phaseLabel}
            </div>
          </div>

          <ChatHistory messages={messages} />

          {isChatLoading && (
            <div className="flex items-center gap-2 px-5 py-2 text-xs text-blue-600 bg-blue-50">
              <Loader2 className="w-3 h-3 animate-spin" />
              正在分析...
            </div>
          )}

          {advanceError && (
            <div role="alert" className="mx-5 mt-3 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs">
              {advanceError}
            </div>
          )}

          <div className="px-5 py-3 bg-white border-t border-slate-100 shrink-0">
            <button
              type="button"
              data-testid="advance-button"
              disabled={advanceDisabled}
              onClick={handleAdvance}
              title={advanceDisabled ? (gateBlockedReason ?? "等待门禁条件满足") : undefined}
              className={`w-full py-2.5 rounded-xl text-sm font-bold transition-all
                ${advanceEnabled
                  ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md"
                  : "bg-slate-100 text-slate-400 cursor-not-allowed"}
              `}
            >
              {isAdvancing ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  推进中...
                </span>
              ) : (
                "确认进入下一阶段"
              )}
            </button>
            {advanceDisabled && !isAdvancing && gateBlockedReason && (
              <p className="text-[10px] text-slate-400 text-center mt-1.5">{gateBlockedReason}</p>
            )}
          </div>

          <div className="p-5 bg-white border-t border-slate-100 shrink-0 relative flex flex-col gap-3">
            <TaskCard
              currentTaskTitle={MOCK_CURRENT_TASK_TITLE}
              tasks={MOCK_TASKS}
            />
            <ChatInput onSend={sendMessage} disabled={isChatLoading} />
          </div>
        </main>

        <aside className="w-[320px] lg:w-[480px] xl:w-[560px] flex flex-col min-w-0 h-full gap-4 pb-1 overflow-hidden">
          <ArtifactList
            phaseLabels={PHASE_LABELS}
            currentPhase={currentPhase}
            onSelect={(idx) => setModalPhase(idx)}
          />
          <FactualLedger facts={MOCK_FACTUAL_DATA} />
        </aside>
      </div>

      <ArtifactModal
        open={modalPhase !== null}
        projectId={id}
        phaseIndex={modalPhase ?? 0}
        phaseLabel={modalPhase !== null ? (PHASE_LABELS[modalPhase] ?? `Phase ${modalPhase}`) : ""}
        onClose={() => setModalPhase(null)}
      />
    </div>
  )
}
