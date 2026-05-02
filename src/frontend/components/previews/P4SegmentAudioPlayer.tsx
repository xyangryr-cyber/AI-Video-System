import type { AudioSegment } from '@frontend/types/preview';
import { useState, useRef, useCallback } from 'react';
import { Play, Pause, Music, CheckCircle2, Download } from 'lucide-react';

interface P4SegmentAudioPlayerProps {
  segments?: AudioSegment[];
}

/** Format seconds as m:ss */
function formatTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

/** Seed-based random for stable waveform heights */
function seededRandom(seed: number): number {
  let x = Math.sin(seed * 9301 + 49297) * 233280;
  return x - Math.floor(x);
}

export function P4SegmentAudioPlayer({ segments }: P4SegmentAudioPlayerProps) {
  const [playingId, setPlayingId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleToggle = useCallback(
    (seg: AudioSegment) => {
      if (playingId === seg.id) {
        audioRef.current?.pause();
        setPlayingId(null);
      } else {
        if (audioRef.current) {
          audioRef.current.pause();
        }
        const audio = new Audio(seg.audio_url);
        audioRef.current = audio;
        audio.play().catch(() => {});
        setPlayingId(seg.id);
        audio.onended = () => setPlayingId(null);
      }
    },
    [playingId],
  );

  if (!segments || segments.length === 0) {
    return (
      <div
        data-testid="preview-p4"
        className="flex flex-col items-center justify-center h-64 text-slate-400"
      >
        <Music className="w-12 h-12 mb-2" />
        <p className="text-sm font-medium">暂无音频分段</p>
        <p className="text-xs text-slate-400 mt-1">等待语音合成 Agent 完成分段录制</p>
      </div>
    );
  }

  return (
    <div data-testid="preview-p4" className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-end mb-2">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">
          分段试听与干音确认
        </span>
      </div>

      {/* Segment rows */}
      {segments.map((seg) => {
        const isPlaying = playingId === seg.id;
        return (
          <div
            key={seg.id}
            className={`flex items-center bg-white border-2 rounded-xl p-4 ${
              seg.warn
                ? 'border-amber-200 bg-amber-50/20'
                : 'border-slate-200'
            }`}
          >
            {/* Dark play button */}
            <button
              aria-label={`${isPlaying ? 'pause' : 'play'} segment ${seg.id}`}
              onClick={() => handleToggle(seg)}
              className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center hover:bg-slate-800 transition-colors shrink-0 shadow-md"
            >
              {isPlaying ? (
                <Pause className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4 ml-0.5" />
              )}
            </button>

            {/* Waveform + label */}
            <div className="mx-4 flex-1">
              <div className="flex items-end justify-between font-bold text-sm text-slate-800 mb-2">
                <span>段落 {seg.id} 音频</span>
                <span className="text-xs text-slate-500 font-mono">
                  {formatTime(seg.duration_sec)}
                </span>
              </div>
              {/* Mock waveform bars */}
              <div className="h-6 flex items-center gap-[2px]">
                {Array.from({ length: 40 }).map((_, i) => (
                  <div
                    key={i}
                    className="bg-slate-300 w-full rounded-full"
                    style={{
                      height: `${Math.max(20, seededRandom(i * 7 + parseInt(seg.id) * 3) * 100)}%`,
                    }}
                  />
                ))}
              </div>
            </div>

            {/* CPS badge + warning */}
            <div className="shrink-0 flex flex-col items-end">
              {seg.cps !== undefined && (
                <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md uppercase tracking-wide">
                  CPS: {seg.cps}
                </span>
              )}
              {seg.warn && (
                <span className="text-[10px] text-amber-600 font-bold mt-1">
                  语速略缓
                </span>
              )}
            </div>
          </div>
        );
      })}

      {/* Footer */}
      <div className="mt-6 pt-5 border-t border-slate-200 flex justify-between items-center">
        <div className="text-sm font-bold text-slate-700 flex items-center">
          <CheckCircle2 className="w-4 h-4 text-green-500 mr-1.5" />
          全案干音 (VoiceOnly) 已生成完毕
        </div>
        <button className="flex items-center text-sm font-bold text-blue-600 bg-blue-50 border border-blue-100 px-4 py-2 rounded-lg hover:bg-blue-100 transition-colors">
          <Download className="w-4 h-4 mr-2" />
          下载完整干音版 (.wav)
        </button>
      </div>
    </div>
  );
}
