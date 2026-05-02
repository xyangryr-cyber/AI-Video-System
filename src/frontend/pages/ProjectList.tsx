import type { ReactElement } from "react";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import "dayjs/locale/zh-cn";
import { Plus, Settings, Play, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { useProjects } from "../hooks/useProjects";

dayjs.extend(relativeTime);
dayjs.locale("zh-cn");

const STATUS_MAP: Record<string, { icon: ReactElement; label: string; color: string }> = {
  in_progress: {
    icon: <Play className="w-4 h-4 text-blue-500" />,
    label: "进行中",
    color: "text-blue-500",
  },
  awaiting_user: {
    icon: <Clock className="w-4 h-4 text-amber-500" />,
    label: "等用户",
    color: "text-amber-500",
  },
  completed: {
    icon: <CheckCircle className="w-4 h-4 text-green-500" />,
    label: "完成",
    color: "text-green-500",
  },
  failed: {
    icon: <AlertCircle className="w-4 h-4 text-red-500" />,
    label: "失败",
    color: "text-red-500",
  },
};

function StatusCell({ status }: { status: string }): ReactElement {
  const s = STATUS_MAP[status] ?? STATUS_MAP.failed;
  return (
    <div className="flex items-center space-x-2">
      {s.icon}
      <span className="text-sm text-slate-600">{s.label}</span>
    </div>
  );
}

function ProgressBar({ progress }: { progress: number }): ReactElement {
  return (
    <div className="flex items-center w-full max-w-[120px]">
      <div className="w-full bg-slate-200 rounded-full h-1.5 flex-1 relative overflow-hidden">
        <div
          className="bg-blue-600 h-1.5 rounded-full absolute top-0 left-0"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

function CategoryBadge({ category }: { category: string }): ReactElement {
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
      {category}
    </span>
  );
}

export function ProjectList(): ReactElement {
  const nav = useNavigate();
  const wsUrl = `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws/projects`;
  const { data, isLoading, isError } = useProjects(wsUrl);

  if (isLoading) return <div>加载中...</div>;
  if (isError || !data) return <div>加载失败</div>;

  return (
    <div className="max-w-6xl mx-auto py-8 px-6">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">AI 视频制作系统</h1>
          <p className="text-sm text-slate-500 mt-1">面向金融内容创作者的专业工作流</p>
        </div>
        <div className="flex space-x-4">
          <button
            aria-label="Settings"
            onClick={() => nav("/settings")}
            className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
          <button
            onClick={() => nav("/projects/new")}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>新建项目</span>
          </button>
        </div>
      </header>

      <div className="bg-white rounded-2xl border-2 border-slate-200 p-6 flex flex-col gap-4">
        <h2 className="text-[0.85rem] font-bold text-slate-800 uppercase tracking-[0.05em]">
          M3: 项目管理列表
        </h2>
        <div className="overflow-x-auto border border-slate-200 rounded-xl">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">
                  标题
                </th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">
                  分类
                </th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">
                  阶段
                </th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">
                  进度
                </th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">
                  状态
                </th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">
                  更新时间
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((project) => (
                <tr
                  key={project.id}
                  onClick={() => nav(`/projects/${project.id}`)}
                  className="hover:bg-slate-50 cursor-pointer transition-colors group"
                >
                  <td className="py-4 px-6 font-medium text-slate-900 group-hover:text-blue-600 transition-colors">
                    {project.title}
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-600">
                    <CategoryBadge category={project.category} />
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-600">
                    Phase {project.current_phase}
                  </td>
                  <td className="py-4 px-6">
                    <ProgressBar progress={project.progress} />
                  </td>
                  <td className="py-4 px-6">
                    <StatusCell status={project.status} />
                  </td>
                  <td className="py-4 px-6 text-sm text-slate-500 whitespace-nowrap">
                    {dayjs(project.updated_at).fromNow()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.length === 0 && (
          <div className="py-12 text-center text-slate-500">暂无项目，点击右上角新建。</div>
        )}
      </div>
    </div>
  );
}
