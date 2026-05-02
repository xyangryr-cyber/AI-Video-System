import type { ReactElement } from "react";
import { useMemo, useState } from "react";
import { Save } from "lucide-react";
import { useSettingsQuery, useModelConfigMutation } from "../../hooks/useSettings";

export function ApiConfigTab(): ReactElement {
  const { data, isLoading } = useSettingsQuery();
  const saveMutation = useModelConfigMutation();
  const [draft, setDraft] = useState<Record<string, unknown>>({});

  const config = useMemo(() => {
    if (data?.model_config_data && draft !== undefined) {
      return { ...data.model_config_data, ...draft };
    }
    return {};
  }, [data, draft]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl border-2 border-slate-200 p-6">
        <p className="text-slate-500 text-sm">加载中...</p>
      </div>
    );
  }

  return (
    <div data-testid="api-config-tab" className="bg-white rounded-2xl border-2 border-slate-200 overflow-hidden flex flex-col">
      {/* Card Header */}
      <div className="p-6 border-b border-slate-200">
        <h2 className="text-[0.85rem] font-bold text-[#1e293b] uppercase tracking-[0.05em]">
          API 密钥配置 (全局)
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          配置全局 AI 模型 API 密钥与连接参数
        </p>
      </div>

      {/* Form Body */}
      <div className="p-6 flex-1">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {Object.entries(config).map(([key, value]) => (
            <div key={key}>
              <label
                htmlFor={`config-${key}`}
                className="block mb-2 text-sm font-medium text-slate-700"
              >
                {key}
              </label>
              <input
                id={`config-${key}`}
                type="text"
                value={String(value ?? "")}
                onChange={(e) =>
                  setDraft((prev) => ({ ...prev, [key]: e.target.value }))
                }
                className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="p-6 border-t border-slate-200 flex justify-end">
        <button
          onClick={() =>
            saveMutation.mutate({ ...data?.model_config_data, ...draft })
          }
          disabled={saveMutation.isPending}
          className="flex items-center gap-2 px-6 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-medium shadow-sm transition-colors disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          保存配置
        </button>
      </div>
    </div>
  );
}
