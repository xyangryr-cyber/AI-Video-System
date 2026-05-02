import type { ReactElement } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { CreateProjectForm } from "../components/CreateProjectForm";
import { useCreateProject } from "../hooks/useCreateProject";

export function NewProject(): ReactElement {
  const nav = useNavigate();
  const mutation = useCreateProject();
  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <button
        onClick={() => nav("/projects")}
        className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm font-medium">返回列表</span>
      </button>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">新建项目</h1>
        <p className="text-slate-500 mt-2">
          用自然语言描述您的内容需求，AI Agent 将协助您完成视频制作全流程。
        </p>
      </div>
      {mutation.error && (
        <div
          role="alert"
          className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm"
        >
          {mutation.error.message}
        </div>
      )}
      <CreateProjectForm
        isSubmitting={mutation.isPending}
        onCancel={() => nav("/projects")}
        onSubmit={(input) =>
          mutation
            .mutateAsync(input)
            .then((data) => {
              nav(`/projects/${data.id}/phases/0`);
            })
            .catch(() => {
              // error handled via mutation.error display
            })
        }
      />
    </div>
  );
}
