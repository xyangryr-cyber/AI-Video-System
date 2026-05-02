import type { ReactElement } from "react";
import { useEffect, useMemo, useState } from "react";
import { Save } from "lucide-react";
import { usePreferencesQuery, usePreferencesMutation } from "../../hooks/useSettings";

export function PreferencesTab(): ReactElement {
  const { data, isLoading } = usePreferencesQuery();
  const saveMutation = usePreferencesMutation();
  const [globalRules, setGlobalRules] = useState("");
  const [userPreferences, setUserPreferences] = useState("");

  useEffect(() => {
    if (data) {
      setGlobalRules(data.global_rules_md);
      setUserPreferences(data.user_preferences_md);
    }
  }, [data]);

  const snapshotPreview = useMemo(() => {
    const parts: string[] = [];
    if (globalRules.trim()) {
      parts.push("# Global Rules\n\n" + globalRules.trim());
    }
    if (userPreferences.trim()) {
      if (parts.length > 0) parts.push("\n\n---\n\n");
      parts.push("# User Preferences\n\n" + userPreferences.trim());
    }
    return parts.join("");
  }, [globalRules, userPreferences]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl border-2 border-slate-200 p-6">
        <p className="text-slate-500 text-sm">加载中...</p>
      </div>
    );
  }

  const handleExport = () => {
    const blob = new Blob([snapshotPreview], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "snapshot.md";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      data-testid="preferences-tab"
      className="bg-white rounded-2xl border-2 border-slate-200 overflow-hidden flex flex-col"
    >
      {/* Card Header */}
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[0.85rem] font-bold text-[#1e293b] uppercase tracking-[0.05em]">
              偏好全局快照 (snapshot.md)
            </h2>
            <p className="mt-1 text-sm text-slate-500">编辑全局规则与用户偏好，实时预览合并快照</p>
          </div>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            重新导出
          </button>
        </div>
      </div>

      {/* Edit Area */}
      <div className="p-6 flex-1 space-y-6">
        <div>
          <label htmlFor="global-rules" className="block mb-2 text-sm font-medium text-slate-700">
            Global Rules
          </label>
          <textarea
            id="global-rules"
            value={globalRules}
            onChange={(e) => setGlobalRules(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 font-mono min-h-[120px]"
          />
        </div>
        <div>
          <label
            htmlFor="user-preferences"
            className="block mb-2 text-sm font-medium text-slate-700"
          >
            User Preferences
          </label>
          <textarea
            id="user-preferences"
            value={userPreferences}
            onChange={(e) => setUserPreferences(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 font-mono min-h-[120px]"
          />
        </div>

        {/* Snapshot Preview */}
        <div>
          <h3 className="text-sm font-medium text-slate-700 mb-2">快照预览</h3>
          <div className="bg-white border border-slate-200 rounded-xl p-5 font-mono text-sm text-slate-800 whitespace-pre-wrap min-h-[200px]">
            {snapshotPreview || "暂无偏好数据"}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-6 border-t border-slate-200 flex justify-between items-center">
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
        >
          导出并下载 snapshot.md
        </button>
        <button
          onClick={() =>
            saveMutation.mutate({
              global_rules_md: globalRules,
              user_preferences_md: userPreferences,
            })
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
