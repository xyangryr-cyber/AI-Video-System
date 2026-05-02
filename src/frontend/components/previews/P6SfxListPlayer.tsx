import type { SfxItem } from "@frontend/types/preview";
import { useState, useRef, useCallback } from "react";
import { Play, Pause, Music, Volume2, Download } from "lucide-react";

interface P6SfxListPlayerProps {
  sfx_list?: SfxItem[];
}

function makeAnnotatedPhrases(sfxList: SfxItem[]): { text: string; sfx: SfxItem | null }[] {
  const phrases: { text: string; sfx: SfxItem | null }[] = [];
  if (sfxList.length === 0) return phrases;
  phrases.push({ text: "黄金价格近期持续走高，让许多投资者感到措手不及。", sfx: null });
  const first = sfxList[0];
  if (first) {
    phrases.push({ text: first.type, sfx: first });
  }
  phrases.push({ text: "的背后，是各国央行的大规模增持。", sfx: null });
  if (sfxList.length > 1) {
    const second = sfxList[1];
    phrases.push({ text: "全球央行净购金量达到了创纪录的" + second.type, sfx: second });
  }
  phrases.push({ text: "，这个买盘力量非常恐怖，直接构筑了金价的坚固底座。", sfx: null });
  return phrases;
}

export function P6SfxListPlayer({ sfx_list }: P6SfxListPlayerProps) {
  const [playingId, setPlayingId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleToggle = useCallback(
    (item: SfxItem) => {
      const key = `${item.type}-${item.time_sec}`;
      if (playingId === key) {
        audioRef.current?.pause();
        setPlayingId(null);
      } else {
        if (audioRef.current) {
          audioRef.current.pause();
        }
        const audio = new Audio(item.audio_url);
        audioRef.current = audio;
        audio.play().catch(() => {});
        setPlayingId(key);
        audio.onended = () => setPlayingId(null);
      }
    },
    [playingId],
  );

  if (!sfx_list || sfx_list.length === 0) {
    return (
      <div
        data-testid="preview-p6"
        className="flex flex-col items-center justify-center h-64 text-slate-400"
      >
        <Music className="w-12 h-12 mb-2" />
        <p className="text-sm font-medium">暂无音效数据</p>
        <p className="text-xs text-slate-400 mt-1">等待音效叠加 Agent 完成 SFX 标注</p>
      </div>
    );
  }

  const phrases = makeAnnotatedPhrases(sfx_list);

  return (
    <div data-testid="preview-p6" className="space-y-6">
      {/* Section 1: SFX layout plan with annotated text */}
      <div className="bg-white border-2 border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-[0.85rem] font-bold tracking-widest uppercase text-slate-800 mb-2 border-b border-slate-100 pb-3">
          1. 全局音效布局规划 (脚本批注)
        </h3>
        <div className="prose prose-sm text-slate-700 max-w-none leading-loose">
          <p>
            {phrases.map((phrase, i) =>
              phrase.sfx ? (
                <span key={i} className="relative group cursor-help inline-block">
                  <span
                    className={`px-1.5 py-0.5 rounded border mr-1 font-bold ${i % 2 === 0 ? "bg-blue-100 text-blue-800 border-blue-200" : "bg-amber-100 text-amber-800 border-amber-200"}`}
                  >
                    {phrase.text}
                  </span>
                  <Volume2
                    className={`inline w-4 h-4 -mt-1 ${i % 2 === 0 ? "text-blue-600" : "text-amber-600"}`}
                  />
                  <span className="absolute hidden group-hover:block bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-slate-800 text-white text-[11px] p-2.5 rounded-lg shadow-xl z-50 leading-snug">
                    <strong>音效:</strong> {phrase.sfx.type}
                    <br />
                    <span className="text-slate-300">触发时间: {phrase.sfx.time_sec}s</span>
                  </span>
                </span>
              ) : (
                <span key={i}>{phrase.text}</span>
              ),
            )}
          </p>
        </div>
      </div>

      {/* Section 2: Segment mix preview */}
      <div className="space-y-3">
        <h3 className="text-[0.85rem] font-bold tracking-widest uppercase text-slate-800 ml-1">
          2. 分段带反馈试听 (人声+BGM+SFX)
        </h3>
        {sfx_list.map((item, i) => {
          const key = `${item.type}-${item.time_sec}`;
          const isPlaying = playingId === key;
          return (
            <div
              key={i}
              className="flex items-center bg-white border-2 border-slate-200 rounded-xl p-4 transition-shadow hover:border-blue-300"
            >
              <button
                onClick={() => handleToggle(item)}
                className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center hover:bg-slate-800 transition-colors shrink-0 shadow-md"
                aria-label={`${isPlaying ? "Pause" : "Play"} segment ${i + 1}`}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
              </button>
              <div className="mx-4 flex-1">
                <div className="flex items-end justify-between font-bold text-sm text-slate-800 mb-2">
                  <span>Segment {i + 1} (混音预览)</span>
                </div>
                <div className="h-4 flex items-center gap-[2px]">
                  {Array.from({ length: 30 }).map((_, j) => (
                    <div
                      key={j}
                      className="bg-slate-300 w-full rounded-full"
                      style={{ height: `${Math.max(20, Math.random() * 100)}%` }}
                    ></div>
                  ))}
                </div>
              </div>
              <div className="shrink-0 flex flex-col items-end">
                <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md uppercase tracking-wide border border-slate-200">
                  {item.type}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Download button */}
      <div className="pt-2 border-t border-slate-200 flex justify-end items-center">
        <button className="flex items-center text-sm font-bold text-blue-600 bg-blue-50 border border-blue-100 px-4 py-2 rounded-lg hover:bg-blue-100 transition-colors shadow-sm">
          <Download className="w-4 h-4 mr-2" />
          下载复合音频版 (.wav)
        </button>
      </div>
    </div>
  );
}
