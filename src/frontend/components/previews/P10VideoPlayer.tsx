import { useRef, useState, useCallback } from 'react';
import { Play, Pause, Film, Video } from 'lucide-react';

interface P10VideoPlayerProps {
  video_url?: string;
  duration_sec?: number;
  subtitles_url?: string;
}

const MOCK_BROLL_ITEMS = [
  { id: 1, filename: 'broll_gold_bars.mp4', duration: '15s', match: '匹配: "华尔街金库/金砖实拍"', license: 'Pexels (CC0)' },
  { id: 2, filename: 'broll_market_fluctuation.mp4', duration: '22s', match: '匹配: "大盘曲线一路上扬"', license: 'Pexels (CC0)' },
  { id: 3, filename: 'broll_jewelry_store.mp4', duration: '18s', match: '匹配: "散户在金店看金饰"', license: 'Pexels (CC0)' },
  { id: 4, filename: 'broll_cbank_vault.mp4', duration: '20s', match: '匹配: "各国央行购金"', license: 'Pexels (CC0)' },
  { id: 5, filename: 'broll_data_chart.mp4', duration: '14s', match: '匹配: "购金对比体量柱状图"', license: 'Pexels (CC0)' },
];

export function P10VideoPlayer({ video_url, duration_sec, subtitles_url }: P10VideoPlayerProps) {
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

  if (!video_url) {
    // B-Roll list view (no video to play)
    return (
      <div data-testid="preview-p10" className="space-y-4">
        <div className="flex flex-col items-center justify-center text-slate-400 py-4">
          <Film className="w-10 h-10 mb-2 opacity-50" />
          <p className="text-sm font-medium">等待 B-Roll 渲染完成</p>
        </div>

        {MOCK_BROLL_ITEMS.map((item) => (
          <div key={item.id} className="bg-white border-2 border-slate-200 p-4 rounded-xl flex items-start gap-4">
            <div className="w-32 aspect-video bg-slate-200 rounded-lg shrink-0 flex items-center justify-center text-slate-400 border border-slate-300">
              <Video className="w-6 h-6" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-start mb-1">
                <div className="font-bold text-sm text-slate-800 truncate">{item.filename}</div>
                <span className="text-[10px] font-bold bg-slate-100 px-2 py-0.5 rounded border border-slate-200 shrink-0">{item.duration}</span>
              </div>
              <div className="text-xs text-slate-500 mb-2">{item.match}</div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-green-600 bg-green-50 inline-block px-2 py-0.5 rounded-sm">{item.license}</div>
            </div>
          </div>
        ))}

        <div className="bg-white border-2 border-slate-200 p-4 rounded-xl text-center">
          <div className="text-sm text-slate-500">共匹配 {MOCK_BROLL_ITEMS.length} 段 B-Roll 素材，覆盖率 45%</div>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="preview-p10" className="p-4">
      <h3 className="text-lg font-semibold mb-2">P10 Video</h3>
      <div className="relative bg-black rounded overflow-hidden">
        <video
          ref={videoRef}
          src={video_url}
          className="w-full"
          onEnded={() => setPlaying(false)}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
        >
          {subtitles_url && <track src={subtitles_url} kind="subtitles" default />}
        </video>
        <button
          onClick={handleToggle}
          className="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/40 transition-colors"
          aria-label={playing ? 'Pause video' : 'Play video'}
        >
          {playing ? <Pause className="w-12 h-12 text-white" /> : <Play className="w-12 h-12 text-white" />}
        </button>
      </div>
      {duration_sec !== undefined && (
        <p className="text-sm text-gray-500 mt-2">{duration_sec}s</p>
      )}
    </div>
  );
}
