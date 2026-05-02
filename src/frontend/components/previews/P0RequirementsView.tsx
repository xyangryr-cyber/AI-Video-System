import type { RequirementsJSON } from '@frontend/types/preview';
import { FileText, Clock } from 'lucide-react';

interface P0RequirementsViewProps {
  requirements?: RequirementsJSON;
}

function extractField(req: RequirementsJSON, keys: string[]): string {
  for (const k of keys) {
    const v = req[k];
    if (typeof v === 'string' && v.trim() !== '') return v.trim();
  }
  return '';
}

function formatCategory(req: RequirementsJSON): string {
  const cat = req['category'];
  if (typeof cat === 'string' && cat.trim()) return cat.trim();
  if (cat && typeof cat === 'object') {
    const parts = [cat['level1'], cat['level2']].filter(Boolean);
    if (parts.length) return parts.join(' / ');
  }
  return '';
}

function formatDuration(req: RequirementsJSON): string {
  const sec = req['target_duration_seconds'];
  if (typeof sec === 'number' && sec > 0) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return s > 0 ? `${m} 分 ${s} 秒` : `${m} 分钟`;
  }
  return extractField(req, ['target_duration', 'targetDuration', 'duration']);
}

export function P0RequirementsView({ requirements }: P0RequirementsViewProps) {
  if (!requirements || Object.keys(requirements).length === 0) {
    return (
      <div
        data-testid="preview-p0"
        className="flex flex-col items-center justify-center h-64 text-slate-400"
      >
        <FileText className="w-12 h-12 mb-3 opacity-40" />
        <p className="text-sm font-medium">暂无需求数据</p>
        <p className="text-xs text-slate-400 mt-1">等待需求采集 Agent 完成初始化</p>
      </div>
    );
  }

  const title = extractField(requirements, ['title']);
  const category = formatCategory(requirements);
  const targetDuration = formatDuration(requirements);
  const platformsRaw = extractField(requirements, ['platforms', 'platform', 'target_platform']);
  const description = extractField(requirements, ['description', 'topic', 'core_brief', 'coreBrief', 'brief']);
  const narrativeTemplate = extractField(requirements, ['narrative_template']);
  const durationClass = extractField(requirements, ['duration_class']);

  const platformList = platformsRaw
    ? platformsRaw.split(/[,，]/).map((s) => s.trim()).filter(Boolean)
    : [];

  return (
    <div data-testid="preview-p0" className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">
            主题 / 标题
          </div>
          <div className="text-sm font-medium text-slate-800">
            {title || '--'}
          </div>
        </div>
        <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">
            分类定位
          </div>
          <div className="text-sm font-medium text-slate-800">
            {category || '--'}
          </div>
        </div>
        <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">
            目标时长
          </div>
          <div className="text-sm font-medium text-slate-800 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            {targetDuration || '--'}
          </div>
        </div>
        <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">
            发布平台策略
          </div>
          <div className="text-sm font-medium text-slate-800 flex gap-2 mt-1">
            {platformList.length === 0 && <span>--</span>}
            {platformList.map((p, i) => (
              <span
                key={p}
                className={
                  i === 0
                    ? 'bg-blue-100 text-blue-700 px-2 py-0.5 rounded-md text-xs'
                    : 'bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md text-xs'
                }
              >
                {p}
              </span>
            ))}
          </div>
        </div>
        {durationClass && (
          <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
            <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">
              时长分类
            </div>
            <div className="text-sm font-medium text-slate-800">
              {durationClass}
            </div>
          </div>
        )}
        {narrativeTemplate && (
          <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
            <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">
              叙事模板
            </div>
            <div className="text-sm font-medium text-slate-800">
              {narrativeTemplate}
            </div>
          </div>
        )}
      </div>
      <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
        <div className="text-xs text-slate-500 mb-2 uppercase tracking-wider font-bold">
          核心提点与需求描述
        </div>
        {description ? (
          <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100 whitespace-pre-wrap">
            {description}
          </p>
        ) : (
          <p className="text-sm text-slate-400 italic bg-slate-50 p-3 rounded-lg border border-slate-100">
            暂无描述
          </p>
        )}
      </div>
    </div>
  );
}
