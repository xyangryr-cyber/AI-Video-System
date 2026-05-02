import type { ReactElement } from "react"
import { useState } from "react"
import { CheckCircle2, ChevronDown, ChevronUp, Circle, MessageSquare } from "lucide-react"
import type { WorkflowTask } from "./mockData"

interface TaskCardProps {
  currentTaskTitle: string
  tasks: WorkflowTask[]
}

export function TaskCard({ currentTaskTitle, tasks }: TaskCardProps): ReactElement {
  const [expanded, setExpanded] = useState(false)
  const completedCount = tasks.filter((t) => t.completed).length

  return (
    <div
      data-testid="task-card"
      className="bg-slate-50 rounded-2xl flex flex-col border border-slate-200 overflow-hidden transition-all duration-300 shadow-sm"
    >
      <button
        type="button"
        aria-expanded={expanded}
        aria-label="切换任务列表"
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-100 transition-colors text-left"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-10 bg-white rounded-lg border border-slate-200 shadow-sm flex items-center justify-center shrink-0">
            <MessageSquare className="w-4 h-4 text-slate-500" />
          </div>
          <div className="flex items-center gap-3 text-slate-800 text-sm font-medium">
            <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
            <span className="truncate">{currentTaskTitle}</span>
          </div>
        </div>
        <div className="flex items-center gap-4 text-slate-500 shrink-0 ml-4">
          <span className="text-sm font-mono">
            {completedCount} / {tasks.length}
          </span>
          <span className="hover:text-slate-800 transition-colors" aria-hidden="true">
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </span>
        </div>
      </button>

      {expanded && (
        <div
          data-testid="task-list"
          className="border-t border-slate-200 bg-white p-2 max-h-[200px] overflow-y-auto"
        >
          <ul className="flex flex-col gap-1">
            {tasks.map((task, idx) => (
              <li
                key={idx}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-50 transition-colors text-slate-700 text-sm"
              >
                <div className="shrink-0 flex items-center justify-center">
                  {task.completed ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" data-testid="task-check" />
                  ) : (
                    <Circle className="w-4 h-4 text-slate-300" />
                  )}
                </div>
                <span className={task.completed ? "text-slate-500 truncate" : "truncate"}>
                  {task.title}
                </span>
                <span className="ml-auto text-xs font-mono text-slate-400 shrink-0">
                  {idx + 1} / {tasks.length}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
