import type { StoryboardShot } from "@frontend/types/preview";
import { Layout, MessageSquare, MonitorPlay, FileText, Sparkles } from "lucide-react";

interface P7StoryboardGalleryProps {
  shots?: StoryboardShot[];
}

// API responses may include extra snake_case fields not in the base StoryboardShot type.
type RawShot = StoryboardShot & {
  shot_id?: string;
  time_range?: { end_seconds: number; start_seconds: number };
  narration_text?: string;
  content?: string;
  template_type?: string;
  type?: string;
};

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function deriveVisualType(templateId?: string): "Template" | "B-Roll" {
  if (!templateId) return "B-Roll";
  const lower = templateId.toLowerCase();
  if (lower.includes("chart") || lower.includes("template") || lower.includes("tpl"))
    return "Template";
  return "B-Roll";
}

export function P7StoryboardGallery({ shots }: P7StoryboardGalleryProps) {
  if (!shots || shots.length === 0) {
    return (
      <div
        data-testid="preview-p7"
        className="flex flex-col items-center justify-center h-64 text-slate-400"
      >
        <Layout className="w-12 h-12 mb-2" />
        <p className="text-sm font-medium">暂无故事板镜头</p>
        <p className="text-xs text-slate-400 mt-1">等待故事板 Agent 完成镜头规划</p>
      </div>
    );
  }

  let cumulativeSec = 0;

  return (
    <div
      data-testid="preview-p7"
      className="relative border-l-2 border-slate-200 ml-4 pl-8 space-y-6 pb-4 pt-2"
    >
      {shots.map((shot) => {
        // Normalize API data to component fields (API uses snake_case, may differ from TS type)
        const shotId = (shot as RawShot).shot_id || shot.id || "?";
        const duration =
          shot.duration_sec ||
          ((shot as RawShot).time_range?.end_seconds ?? 0) - ((shot as RawShot).time_range?.start_seconds ?? 0) ||
          0;
        const description =
          shot.description || (shot as RawShot).narration_text || (shot as RawShot).content || "";
        const templateId = shot.template_id || (shot as RawShot).template_type;
        const shotType = (shot as RawShot).type || "template";

        const start = formatTime(cumulativeSec);
        const end = formatTime(cumulativeSec + duration);
        const timeRange = `${start} - ${end}`;
        const visualType = shotType === "broll" ? "B-Roll" : deriveVisualType(templateId);
        cumulativeSec += duration;

        return (
          <div key={shot.id} className="relative">
            {/* Timeline dot centered on the border */}
            <div className="absolute -left-[39.5px] top-4 w-4 h-4 rounded-full bg-white border-[3px] border-blue-500 shadow-sm z-10"></div>

            <div className="bg-white border-2 border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 hover:border-blue-300 transition-colors">
              {/* Header */}
              <div className="flex flex-wrap md:flex-nowrap justify-between gap-3 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-3">
                  <span className="bg-[#1e293b] text-white font-bold px-2 py-0.5 rounded text-xs tracking-widest">
                    {shotId}
                  </span>
                  <span className="font-mono text-slate-500 text-[13px] font-bold">
                    {timeRange}
                  </span>
                </div>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider uppercase border shrink-0 ${visualType === "Template" ? "bg-blue-50 text-blue-600 border-blue-200" : "bg-emerald-50 text-emerald-600 border-emerald-200"}`}
                >
                  {visualType}
                </span>
              </div>

              {/* Content Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="space-y-4">
                  <div>
                    <h4 className="flex items-center text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-2">
                      <MessageSquare className="w-3.5 h-3.5 mr-1" /> 对应口播 (Script)
                    </h4>
                    <p className="text-[13px] text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100 italic leading-relaxed">
                      "{description}"
                    </p>
                  </div>
                  <div>
                    <h4 className="flex items-center text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-2">
                      <MonitorPlay className="w-3.5 h-3.5 mr-1" /> 视频画面 (Visual)
                    </h4>
                    <p className="text-sm font-bold text-slate-800">{description}</p>
                  </div>
                </div>
                <div className="space-y-4 md:border-l md:border-slate-100 md:pl-5">
                  <div>
                    <h4 className="flex items-center text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-2">
                      <FileText className="w-3.5 h-3.5 mr-1" /> 展示信息 (Info)
                    </h4>
                    <p className="text-[13px] font-medium text-slate-600">
                      模版: {templateId || shotType} / 时长: {duration}s
                    </p>
                  </div>
                  <div>
                    <h4 className="flex items-center text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-2">
                      <Sparkles className="w-3.5 h-3.5 mr-1" /> 动画/特效 (Effects)
                    </h4>
                    <p className="text-[13px] font-medium text-slate-600">淡入淡出转场效果</p>
                  </div>
                </div>
              </div>

              {/* Action Bar */}
              <div className="pt-3 border-t border-slate-100 flex justify-end mt-2">
                <button className="text-xs text-blue-600 font-bold tracking-wide hover:bg-blue-50 px-4 py-2 rounded-lg transition-colors border border-transparent hover:border-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-100">
                  针对 {shotId} 提修改要求
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
