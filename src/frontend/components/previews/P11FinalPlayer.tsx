import type { Cover } from "@frontend/types/preview";
import { useState, useRef, useCallback } from "react";
import { Play, Pause, Download, CheckCircle2, FileText } from "lucide-react";

interface P11FinalPlayerProps {
  video_url?: string;
  covers?: Cover[];
  download_urls?: Record<string, string>;
}

export function P11FinalPlayer({ video_url, covers, download_urls }: P11FinalPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [playing, setPlaying] = useState(false);

  const handleToggle = useCallback(() => {
    if (!videoRef.current) return;
    if (playing) {
      videoRef.current.pause();
      setPlaying(false);
    } else {
      videoRef.current.play().catch(() => {});
      setPlaying(true);
    }
  }, [playing]);

  return (
    <div data-testid="preview-p11" className="space-y-5">
      {/* Completion section */}
      <div className="bg-white border-2 border-slate-200 rounded-xl overflow-hidden p-1 shadow-sm">
        <div className="bg-slate-50 rounded-lg p-6 text-center border border-slate-100">
          <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4 border-[3px] border-green-200 shadow-sm">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-1">视频精剪完成!</h3>
          <p className="text-slate-500 text-sm">项目《最终视频》已就绪</p>
        </div>
      </div>

      {/* Embedded video player */}
      {video_url ? (
        <div className="relative bg-black rounded overflow-hidden">
          <video
            ref={videoRef}
            src={video_url}
            data-testid="final-video-player"
            className="w-full"
            onEnded={() => setPlaying(false)}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
          />
          <button
            onClick={handleToggle}
            className="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/40 transition-colors"
            aria-label={playing ? "Pause video" : "Play video"}
          >
            {playing ? (
              <Pause className="w-12 h-12 text-white" />
            ) : (
              <Play className="w-12 h-12 text-white" />
            )}
          </button>
        </div>
      ) : (
        <div className="bg-slate-100 rounded-lg text-center text-slate-400 py-6">
          <p className="text-sm">无视频数据</p>
        </div>
      )}

      {/* Cover images */}
      {covers && covers.length > 0 && (
        <div className="mb-2">
          <div className="flex gap-2 overflow-x-auto">
            {covers.map((cover, i) => (
              <div key={i} className="flex-shrink-0 border rounded overflow-hidden w-32">
                <img
                  src={cover.url}
                  alt={`cover ${i}`}
                  className="w-full h-18 object-cover"
                  loading="lazy"
                />
                <div className="p-1 text-xs text-center text-gray-500">{cover.aspect_ratio}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Platform download buttons */}
      <div className="grid grid-cols-2 gap-4">
        <a
          href={download_urls?.["bilibili"] || "#"}
          download={download_urls?.["bilibili"] ? "video_bilibili.mp4" : undefined}
          className="bg-white border-2 border-slate-200 hover:border-blue-400 hover:bg-blue-50 transition-all rounded-xl p-4 flex flex-col items-center justify-center gap-3 text-center group no-underline"
        >
          <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
            <Download className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-800">下载 B 站版本</div>
            <div className="text-[10px] font-mono text-slate-500 mt-1">1080P | H.264 | 180MB</div>
          </div>
        </a>
        <a
          href={download_urls?.["douyin"] || "#"}
          download={download_urls?.["douyin"] ? "video_douyin.mp4" : undefined}
          className="bg-white border-2 border-slate-200 hover:border-blue-400 hover:bg-blue-50 transition-all rounded-xl p-4 flex flex-col items-center justify-center gap-3 text-center group no-underline"
        >
          <div className="w-10 h-10 bg-slate-100 text-slate-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
            <Download className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-800">下载抖音版本</div>
            <div className="text-[10px] font-mono text-slate-500 mt-1">
              竖屏 | 1080x1920 | 165MB
            </div>
          </div>
        </a>
      </div>

      {/* SRT subtitle row */}
      <div className="bg-white border-2 border-slate-200 rounded-xl p-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-slate-400" />
          <span className="text-sm font-bold text-slate-700">配套字幕文件 (SRT)</span>
        </div>
        <a
          href={download_urls?.["srt"] || "#"}
          download={download_urls?.["srt"] ? "subtitles.srt" : undefined}
          className="text-blue-600 font-bold text-xs uppercase tracking-wider hover:underline underline-offset-4 no-underline"
        >
          Download
        </a>
      </div>
    </div>
  );
}
