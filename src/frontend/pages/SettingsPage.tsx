import type { ReactElement, ReactNode } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Shield, Cpu, HardDrive } from "lucide-react";
import { ApiConfigTab } from "../components/settings/ApiConfigTab";
import { PreferencesTab } from "../components/settings/PreferencesTab";
import { ModelsTab } from "../components/settings/ModelsTab";

type TabId = "api" | "models" | "preferences";

interface TabDef {
  id: TabId;
  label: string;
  icon: ReactNode;
}

const TABS: TabDef[] = [
  { id: "api", label: "API 密钥配置", icon: <Shield className="w-4 h-4" /> },
  { id: "models", label: "模型与策略", icon: <Cpu className="w-4 h-4" /> },
  { id: "preferences", label: "偏好全局快照", icon: <HardDrive className="w-4 h-4" /> },
];

function renderActive(tab: TabId): ReactElement {
  switch (tab) {
    case "api":
      return <ApiConfigTab />;
    case "models":
      return <ModelsTab />;
    case "preferences":
      return <PreferencesTab />;
  }
}

export function SettingsPage(): ReactElement {
  const [activeTab, setActiveTab] = useState<TabId>("api");
  const navigate = useNavigate();

  return (
    <div className="max-w-4xl mx-auto py-12 px-6">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate("/projects")}
          className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm font-medium">返回</span>
        </button>
        <h1 className="text-2xl font-bold text-slate-900">系统设置</h1>
      </div>

      {/* Sidebar + Content */}
      <div className="flex gap-6">
        {/* Sidebar */}
        <nav className="w-64 shrink-0 bg-white border-2 border-slate-200 rounded-2xl p-4 h-fit">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 font-medium rounded-lg transition-colors ${
                activeTab === t.id ? "bg-blue-50 text-blue-600" : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              {t.icon}
              <span className="text-sm">{t.label}</span>
            </button>
          ))}
        </nav>

        {/* Content */}
        <div className="flex-1 min-w-0">{renderActive(activeTab)}</div>
      </div>
    </div>
  );
}
