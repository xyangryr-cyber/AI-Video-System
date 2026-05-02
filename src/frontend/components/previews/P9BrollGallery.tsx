import type { BrollItem } from "@frontend/types/preview";
import { CheckCircle2, Clock, ImageIcon, Play, Video } from "lucide-react";

interface P9BrollGalleryProps {
  brolls?: BrollItem[];
}

export function P9BrollGallery({ brolls }: P9BrollGalleryProps) {
  if (!brolls || brolls.length === 0) {
    return (
      <div
        data-testid="preview-p9"
        className="flex flex-col items-center justify-center h-64 text-slate-400"
      >
        <Video className="w-8 h-8 mb-2 opacity-50" />
        <p className="text-sm font-medium">暂无关键帧数据</p>
      </div>
    );
  }

  return (
    <div
      data-testid="preview-p9"
      className="relative border-l-2 border-slate-200 ml-4 pl-8 space-y-6 pb-4 pt-2"
    >
      {brolls.map((item) => {
        const isRendered = !item.is_placeholder;
        return (
          <div key={item.id} className="relative">
            {/* Timeline dot centered on the border */}
            <div className="absolute -left-[39.5px] top-4 w-4 h-4 rounded-full bg-white border-[3px] border-blue-500 shadow-sm z-10" />

            <div className="bg-white border-2 border-slate-200 rounded-2xl overflow-hidden shadow-sm hover:border-blue-300 transition-colors flex flex-col sm:flex-row">
              {/* Left/Top Content: Timeline info */}
              <div className="p-5 sm:w-1/2 flex flex-col justify-between border-b sm:border-b-0 sm:border-r border-slate-100">
                <div>
                  <div className="flex items-center gap-3 pb-3 mb-3 border-b border-slate-100">
                    <span className="bg-[#1e293b] text-white font-bold px-2 py-0.5 rounded text-xs tracking-widest">
                      {item.id}
                    </span>
                  </div>
                  <div className="text-[13px] text-slate-600">{item.source}</div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center">
                  {isRendered ? (
                    <span className="text-[10px] text-green-700 font-bold border border-green-200 bg-green-100 flex items-center px-2 py-0.5 rounded shadow-sm uppercase tracking-wider">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Rendered
                    </span>
                  ) : (
                    <span className="text-[10px] text-amber-700 font-bold border border-amber-200 bg-amber-50 flex items-center px-2 py-0.5 rounded shadow-sm uppercase tracking-wider">
                      <Clock className="w-3 h-3 mr-1" /> Awaiting P10
                    </span>
                  )}
                </div>
              </div>

              {/* Right/Bottom Content: Video/Placeholder */}
              <div className="sm:w-1/2 relative bg-slate-50 flex items-center justify-center min-h-[160px] group">
                {isRendered && item.thumbnail_url ? (
                  <>
                    <img
                      src={item.thumbnail_url}
                      alt={`broll ${item.id}`}
                      className="absolute inset-0 w-full h-full object-cover opacity-30"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                      <div className="w-12 h-12 bg-black/40 backdrop-blur rounded-full flex items-center justify-center group-hover:bg-blue-600 transition-colors shadow-lg">
                        <Play className="w-5 h-5 text-white ml-1" />
                      </div>
                    </div>
                    <ImageIcon className="w-10 h-10 text-slate-300 absolute" />
                    <div className="absolute bottom-2 right-2 bg-slate-900/60 text-white text-[10px] px-2 py-0.5 rounded font-mono z-10">
                      Keyframe_{item.id}.mp4
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center text-slate-400 p-4 text-center">
                    <Video className="w-8 h-8 mb-2 opacity-50" />
                    <span className="text-[11px] font-bold uppercase tracking-wider">
                      等待 B-Roll 库填充
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
