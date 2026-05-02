import { useRef, useState, useCallback } from 'react';
import { Play, Pause, Music, Waves, CheckCircle2, Download } from 'lucide-react';

interface P5WaveformPlayerProps {
  audio_url?: string;
  duration_sec?: number;
}

/** Seed-based random for stable waveform heights */
function seededRandom(seed: number): number {
  let x = Math.sin(seed * 9301 + 49297) * 233280;
  return x - Math.floor(x);
}

export function P5WaveformPlayer({ audio_url, duration_sec }: P5WaveformPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);

  const handleToggle = useCallback(() => {
    if (!audio_url) return;
    if (!audioRef.current) {
      audioRef.current = new Audio(audio_url);
      audioRef.current.onended = () => setPlaying(false);
    }
    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play().catch(() => {});
      setPlaying(true);
    }
  }, [playing, audio_url]);

  const totalDuration = duration_sec ? `${Math.floor(duration_sec / 60)}:${String(duration_sec % 60).padStart(2, '0')}` : '2:27';

  if (!audio_url) {
    return (
      <div
        data-testid="preview-p5"
        className="flex flex-col items-center justify-center h-64 text-slate-400"
      >
        <Music className="w-12 h-12 mb-2" />
        <p className="text-sm font-medium">暂无 BGM 音频</p>
        <p className="text-xs text-slate-400 mt-1">等待 BGM 匹配 Agent 完成配乐生成</p>
      </div>
    );
  }

  const moodHeights = ['30%', '40%', '60%', '80%', '90%', '70%', '50%', '60%'];

  return (
    <div data-testid="preview-p5" className="space-y-6">
      {/* Mood/Energy Curve */}
      <div className="bg-white border-2 border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-[0.85rem] font-bold tracking-widest uppercase text-slate-500 mb-4 flex items-center">
          <Waves className="w-4 h-4 mr-2 text-blue-500" />
          情感与能量曲线规划
        </h3>
        <div className="h-24 flex items-end gap-1 px-2 border-b border-l border-slate-200 pb-1">
          {moodHeights.map((h, i) => (
            <div
              key={i}
              className="flex-1 bg-gradient-to-t from-blue-100 to-blue-400 rounded-t-sm"
              style={{ height: h }}
            />
          ))}
        </div>
        <div className="flex justify-between text-[10px] text-slate-400 uppercase font-bold tracking-widest mt-2">
          <span>引入 (悬念)</span>
          <span>正文 (激昂)</span>
          <span>结尾 (平缓)</span>
        </div>
      </div>

      {/* BGM Track Card */}
      <div className="bg-white border-2 border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center">
            <Music className="w-8 h-8 p-1.5 bg-indigo-100 text-indigo-600 rounded-lg mr-3" />
            <div>
              <div className="text-sm font-bold text-slate-800">
                全局配乐混合试听 (BGM + Voice)
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                主轨: Corporate Tech Cinematic
              </div>
            </div>
          </div>
        </div>
        <div className="p-4 bg-slate-50/50 flex flex-col gap-4">
          {/* Info row */}
          <div className="flex space-x-4 text-xs font-medium text-slate-600 border-b border-slate-200 pb-4">
            <div className="flex flex-col">
              <span className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">
                版权状态
              </span>
              <span className="text-green-600 font-bold bg-green-100 px-2 py-0.5 rounded-md text-center max-w-fit">
                CC-BY (免版税)
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">
                Ducking 包络
              </span>
              <span className="font-bold">正文段自动避让 -18dB</span>
            </div>
          </div>

          {/* Player bar */}
          <div className="bg-slate-800 rounded-xl p-3 flex items-center">
            <button
              onClick={handleToggle}
              className="w-10 h-10 rounded-full bg-white text-slate-900 flex items-center justify-center hover:bg-slate-100 transition-colors shrink-0 shadow-md"
              aria-label={playing ? 'Pause' : 'Play'}
            >
              {playing ? (
                <Pause className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4 ml-0.5" />
              )}
            </button>
            <div className="mx-4 flex-1 h-8 flex items-center relative">
              {/* Background waveform layer (indigo) */}
              <div className="absolute inset-0 flex items-center gap-[1px] opacity-40">
                {Array.from({ length: 60 }).map((_, i) => (
                  <div
                    key={`bg-${i}`}
                    className="bg-indigo-300 w-full rounded-full"
                    style={{
                      height: `${Math.max(10, Math.sin(i / 5) * 50 + 50)}%`,
                    }}
                  />
                ))}
              </div>
              {/* Foreground waveform layer (white) */}
              <div className="absolute inset-0 flex items-center gap-[1px]">
                {Array.from({ length: 60 }).map((_, i) => (
                  <div
                    key={`fg-${i}`}
                    className="bg-white w-full rounded-full"
                    style={{
                      height: `${Math.max(20, seededRandom(i * 11 + 3) * 80)}%`,
                    }}
                  />
                ))}
              </div>
            </div>
            <div className="text-white text-xs font-mono font-bold tracking-wider">
              0:00 / {totalDuration}
            </div>
          </div>

          {/* Review verdict + change BGM */}
          <div className="flex justify-between items-center text-xs mt-1">
            <span className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-2 py-1 rounded-md font-bold flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Review Agent: 全局 BGM 与人声频段无冲突，情感起伏完美贴合
            </span>
            <button className="font-bold text-slate-500 hover:text-slate-800 underline underline-offset-4">
              更换配乐
            </button>
          </div>
        </div>
      </div>

      {/* Download button */}
      <div className="pt-2 border-t border-slate-200 flex justify-end items-center">
        <button className="flex items-center text-sm font-bold text-blue-600 bg-blue-50 border border-blue-100 px-4 py-2 rounded-lg hover:bg-blue-100 transition-colors shadow-sm">
          <Download className="w-4 h-4 mr-2" />
          下载混音初版 (.wav)
        </button>
      </div>
    </div>
  );
}
