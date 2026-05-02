import type { VideoFrame } from '@frontend/types/preview';
import { CheckCircle2, Image, Sparkles } from 'lucide-react';

interface P8FrameGalleryProps {
  frames?: VideoFrame[];
}

function deriveVisualType(imageUrl: string): 'Template' | 'B-Roll' {
  const lower = imageUrl.toLowerCase();
  if (lower.includes('chart') || lower.includes('template') || lower.includes('tpl')) return 'Template';
  return 'B-Roll';
}

export function P8FrameGallery({ frames }: P8FrameGalleryProps) {
  if (!frames || frames.length === 0) {
    return (
      <div data-testid="preview-p8" className="flex flex-col items-center justify-center h-64 text-slate-400">
        <Image className="w-12 h-12 mb-2" />
        <p className="text-sm font-medium">暂无素材帧</p>
        <p className="text-xs text-slate-400 mt-1">等待素材溯源 Agent 完成关键帧提取</p>
      </div>
    );
  }

  return (
    <div data-testid="preview-p8" className="relative border-l-2 border-slate-200 ml-4 pl-8 space-y-6 pb-4 pt-2">
      {frames.map((frame) => {
        const visualType = deriveVisualType(frame.image_url);

        return (
          <div key={frame.id} className="relative">
            {/* Timeline dot centered on the border */}
            <div className="absolute -left-[39.5px] top-4 w-4 h-4 rounded-full bg-white border-[3px] border-blue-500 shadow-sm z-10"></div>

            <div className="bg-white border-2 border-slate-200 rounded-2xl p-5 shadow-sm hover:border-blue-300 transition-colors">
              {/* Header */}
              <div className="flex flex-wrap md:flex-nowrap justify-between gap-3 border-b border-slate-100 pb-3 mb-4">
                <div className="flex items-center gap-3">
                  <span className="bg-[#1e293b] text-white font-bold px-2 py-0.5 rounded text-xs tracking-widest">{frame.id}</span>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider uppercase border shrink-0 ${visualType === 'Template' ? 'bg-blue-50 text-blue-600 border-blue-200' : 'bg-emerald-50 text-emerald-600 border-emerald-200'}`}>
                  {visualType}
                </span>
              </div>

              <div className="mb-4">
                <span className="text-[13px] font-bold text-slate-700">画面规划：</span>
                <span className="text-[13px] text-slate-600 ml-1">{frame.image_url}</span>
              </div>

              {frame.is_downgraded ? (
                <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 flex items-center text-[12px] text-slate-500">
                  <CheckCircle2 className="w-4 h-4 mr-2" /> 无需额外动态数据源，将使用常规素材库
                </div>
              ) : (
                <div className="border border-blue-100 bg-blue-50/30 rounded-xl p-4 relative">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-amber-500" />
                      <span className="text-[12px] font-bold text-slate-800">AI Agent 物料溯源结果</span>
                    </div>
                    <span className="text-[10px] text-green-700 font-bold border border-green-200 bg-green-100 flex items-center px-2 py-0.5 rounded shadow-sm">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Verified
                    </span>
                  </div>

                  <div className="space-y-2 mt-3">
                    <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-2">
                      <span className="text-[11px] font-bold text-slate-500 w-16 shrink-0 mt-0.5 uppercase tracking-wide">Need:</span>
                      <span className="text-[12px] text-slate-700 font-medium">获取 {frame.id} 的相关视觉数据</span>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-2">
                      <span className="text-[11px] font-bold text-slate-500 w-16 shrink-0 mt-0.5 uppercase tracking-wide">Action:</span>
                      <span className="text-[12px] text-blue-700 bg-blue-100 px-2 py-0.5 rounded inline-block font-bold">Fetch Asset: {frame.image_url}</span>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-blue-100/50">
                    <div className="bg-[#1e293b] rounded-lg p-3 text-[11px] font-mono text-emerald-400 overflow-x-auto shadow-inner border border-slate-800">
                      {`{ "id": "${frame.id}", "image_url": "${frame.image_url}" }`}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
