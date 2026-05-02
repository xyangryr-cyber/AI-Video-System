import type { ReactElement } from "react";
import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { ChatHistory } from "@frontend/components/workflow/ChatHistory";
import { TaskCard } from "@frontend/components/workflow/TaskCard";
import { ChatInput } from "@frontend/components/workflow/ChatInput";
import { ArtifactList } from "@frontend/components/workflow/ArtifactList";
import { ArtifactModal } from "@frontend/components/workflow/ArtifactModal";
import { P0RequirementsView } from "@frontend/components/previews/P0RequirementsView";
import { PhaseNavigation } from "@frontend/components/PhaseNavigation";
import { useChat } from "@frontend/hooks/useChat";
import { useAdvance } from "@frontend/hooks/useAdvance";
import { useProjectState } from "@frontend/hooks/useProjectState";
import { useWebSocket } from "@frontend/hooks/useWebSocket";
import { apiClient } from "@frontend/api/client";
import { PHASE_LABELS } from "@shared/constants/phaseLabels";
import type { RequirementsJSON } from "@frontend/types/preview";
import type { WorkflowTask } from "@frontend/components/workflow/mockData";
import { MOCK_CURRENT_TASK_TITLE, MOCK_TASKS } from "@frontend/components/workflow/mockData";

export function WorkflowPage(): ReactElement {
  const { id = "", phase = "0" } = useParams<{ id: string; phase: string }>();
  const currentPhase = Number(phase);
  const navigate = useNavigate();

  const [modalPhase, setModalPhase] = useState<number | null>(null);
  const [advanceError, setAdvanceError] = useState<string | null>(null);
  const [completedPhases, setCompletedPhases] = useState<number>(0);
  const phaseLabel = PHASE_LABELS[currentPhase] ?? `Phase ${currentPhase}`;
  const { messages, sendMessage, isLoading: isChatLoading, highlightConfirm } = useChat(id);
  const { advance, isAdvancing } = useAdvance(id);

  // T011: Real project title from API
  const { data: projectState, isLoading: isProjectLoading } = useProjectState(id);

  // T012: Real artifact data for P0
  interface ArtifactResponse {
    artifact_data: RequirementsJSON;
  }
  const [artifactData, setArtifactData] = useState<ArtifactResponse | null>(null);
  useEffect(() => {
    if (!id) return;
    apiClient
      .get<ArtifactResponse>(`/api/projects/${id}/phases/0/artifact`)
      .then(setArtifactData)
      .catch(console.error);
  }, [id]);

  // T019: Review verdict from WebSocket + task polling
  interface ReviewVerdict {
    verdict: string;
    blocking_issues?: string[];
  }
  const [reviewVerdict, setReviewVerdict] = useState<ReviewVerdict | null>(null);

  // T013: Real task data with 3s polling fallback
  interface TaskItem {
    task_id: string;
    type: string;
    status: string;
    result_ref?: string;
    result?: string;
  }
  interface TasksResponse {
    project_id: string;
    tasks: TaskItem[];
    current_task: { id: string; type: string; status: string } | null;
  }
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [currentTask, setCurrentTask] = useState<TasksResponse["current_task"]>(null);
  const fetchTasks = useCallback(() => {
    if (!id) return;
    apiClient
      .get<TasksResponse>(`/api/projects/${id}/tasks?phase=0`)
      .then((data) => {
        setTasks(data?.tasks ?? []);
        setCurrentTask(data?.current_task ?? null);
      })
      .catch(console.error);
  }, [id]);
  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 3000);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  // T019: Fallback — extract review verdict from polled tasks when no WebSocket event yet
  useEffect(() => {
    if (reviewVerdict) return;
    const reviewTask = tasks.find((t) => t.type === "review" && t.status === "succeeded");
    if (!reviewTask) return;
    const raw = reviewTask.result_ref ?? reviewTask.result;
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      if (parsed?.verdict) {
        setReviewVerdict({
          verdict: parsed.verdict,
          blocking_issues: parsed.blocking_issues,
        });
      }
    } catch {
      // result_ref may not be JSON; ignore parse failure
    }
  }, [tasks, reviewVerdict]);

  // T015: WebSocket for real-time updates
  const handleWsMessage = useCallback(
    (data: unknown) => {
      const event = data as { type?: string };
      if (!event?.type) return;
      switch (event.type) {
        case "task.started":
        case "task.completed":
        case "task.failed":
          fetchTasks();
          break;
        case "artifact.updated":
          if (!id) return;
          apiClient
            .get<ArtifactResponse>(`/api/projects/${id}/phases/0/artifact`)
            .then(setArtifactData)
            .catch(console.error);
          break;
        case "review.completed": {
          const reviewEvent = data as {
            payload?: { verdict?: string; blocking_issues?: string[] };
          };
          if (reviewEvent?.payload) {
            setReviewVerdict({
              verdict: reviewEvent.payload.verdict || "UNKNOWN",
              blocking_issues: reviewEvent.payload.blocking_issues,
            });
          }
          fetchTasks();
          break;
        }
        case "phase.completed":
          setCompletedPhases((prev) => Math.max(prev, currentPhase));
          navigate(`/projects/${id}/phases/${currentPhase + 1}`);
          break;
      }
    },
    [id, fetchTasks, navigate, currentPhase],
  );
  const wsEnabled = typeof process === "undefined" || process.env?.NODE_ENV !== "test";
  useWebSocket(`ws://localhost:8000/ws/${id}`, { onMessage: handleWsMessage, enabled: wsEnabled });

  // T028: Determine why advance button is blocked
  function getAdvanceBlockedReason(
    reviewVerdict: ReviewVerdict | null,
    tasks: TaskItem[],
    artifactData: ArtifactResponse | null,
  ): string | null {
    if (!artifactData?.artifact_data) return "需求产物尚未生成";
    if (reviewVerdict?.verdict === "FAIL") return "审核未通过";
    if (tasks.some((t) => t.status === "running" || t.status === "queued"))
      return "仍有任务正在执行中，请等待完成";
    return null;
  }

  const handleAdvance = async () => {
    setAdvanceError(null);
    try {
      const res = await advance();
      if (res.status === "advanced" || res.status === "already_advanced") {
        setCompletedPhases((prev) => Math.max(prev, res.current_phase));
        navigate(`/projects/${id}/phases/${res.current_phase}`);
      } else if (res.status === "gate_failed") {
        setAdvanceError(res.error_code ?? "门禁校验未通过，请检查以下项目");
      }
    } catch (e: unknown) {
      const err = e as { message?: string };
      setAdvanceError(err.message ?? "推进失败，请重试");
    }
  };

  const blockReason = getAdvanceBlockedReason(reviewVerdict, tasks, artifactData);
  const advanceEnabled = highlightConfirm && !blockReason;
  const advanceDisabled = !advanceEnabled || isAdvancing;

  // T023: Handle clarification answer from P0RequirementsView
  const handleClarificationAnswer = useCallback(
    (dimension: string, answer: string) => {
      sendMessage(`关于${dimension}：${answer}`);
    },
    [sendMessage],
  );

  return (
    <div className="h-screen flex flex-col bg-[#f8fafc] overflow-hidden p-4 sm:p-5 gap-5 text-[#1e293b]">
      <div className="flex-1 flex overflow-hidden gap-4">
        <PhaseNavigation
          currentPhase={currentPhase}
          phases={PHASE_LABELS.map((_, i) => ({ phase: i }))}
          onSelectPhase={(phase) => navigate(`/projects/${id}/phases/${phase}`)}
          completedPhases={completedPhases}
        />
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
                {isProjectLoading ? (
                  <span className="inline-flex items-center gap-1.5 text-slate-400">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    加载中...
                  </span>
                ) : (
                  projectState?.project?.title || id || "—"
                )}
                <span className="text-slate-400 font-normal ml-2 text-xs">{id}</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-2 py-1 bg-slate-100 rounded">
                P{currentPhase} · {phaseLabel}
              </div>
              {/* T019: Review verdict badge */}
              {currentPhase === 0 &&
                (reviewVerdict === null ? (
                  <span
                    className="text-[10px] font-bold text-yellow-700 bg-yellow-100 px-2 py-1 rounded cursor-default"
                    title="等待审核完成..."
                  >
                    审核中...
                  </span>
                ) : reviewVerdict.verdict === "PASS" ? (
                  <span className="text-[10px] font-bold text-green-700 bg-green-100 px-2 py-1 rounded cursor-default">
                    审核通过
                  </span>
                ) : (
                  <span
                    className="text-[10px] font-bold text-red-700 bg-red-100 px-2 py-1 rounded cursor-default"
                    title={
                      reviewVerdict.blocking_issues?.length
                        ? `阻塞项:\n${reviewVerdict.blocking_issues.join("\n")}`
                        : undefined
                    }
                  >
                    审核未通过
                  </span>
                ))}
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
            <div
              role="alert"
              className="mx-5 mt-3 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs"
            >
              {advanceError}
            </div>
          )}

          <div className="px-5 py-3 bg-white border-t border-slate-100 shrink-0">
            <button
              type="button"
              data-testid="advance-button"
              disabled={advanceDisabled}
              onClick={handleAdvance}
              title={
                advanceDisabled && !isAdvancing ? (blockReason ?? "等待门禁条件满足") : undefined
              }
              className={`w-full py-2.5 rounded-xl text-sm font-bold transition-all
                ${
                  advanceEnabled
                    ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md"
                    : "bg-slate-100 text-slate-400 cursor-not-allowed"
                }
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
            {advanceDisabled && !isAdvancing && blockReason && (
              <p className="text-[10px] text-slate-400 text-center mt-1.5">
                {blockReason}
                {reviewVerdict?.verdict === "FAIL" && reviewVerdict.blocking_issues?.length
                  ? `（${reviewVerdict.blocking_issues.join("；")}）`
                  : ""}
              </p>
            )}
          </div>

          <div className="p-5 bg-white border-t border-slate-100 shrink-0 relative flex flex-col gap-3">
            <TaskCard
              currentTaskTitle={
                currentTask?.type ??
                (Array.isArray(tasks)
                  ? tasks.find((t) => t.status !== "succeeded")?.type
                  : undefined) ??
                MOCK_CURRENT_TASK_TITLE
              }
              tasks={
                Array.isArray(tasks) && tasks.length > 0
                  ? tasks.map(
                      (t): WorkflowTask => ({ title: t.type, completed: t.status === "succeeded" }),
                    )
                  : MOCK_TASKS
              }
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
          <P0RequirementsView
            requirements={artifactData?.artifact_data}
            onClarificationAnswer={handleClarificationAnswer}
          />
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
  );
}
