import { useRef, useCallback, useState, type ReactElement } from "react";
import type { GetMasterAudioResponse } from "@shared/types/api_master_audio";

interface Props {
  masterAudio: GetMasterAudioResponse | null | undefined;
  onUpdate?: () => void;
}

export function MasterAudioPlayer({ masterAudio }: Props): ReactElement {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const onPlayPause = useCallback(() => {
    const a = audioRef.current;
    if (!a) return;
    if (a.paused) {
      a.play().catch(() => {});
      setPlaying(true);
    } else {
      a.pause();
      setPlaying(false);
    }
  }, []);

  const onTimeUpdate = useCallback(() => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  }, []);

  const onEnded = useCallback(() => {
    setPlaying(false);
    setCurrentTime(0);
  }, []);

  if (!masterAudio) {
    return (
      <div
        role="region"
        aria-label="主旁白播放器"
        data-testid="master-audio-skeleton"
        className="animate-pulse rounded-lg bg-gray-200 h-16 w-full"
      />
    );
  }

  const duration = 300; // placeholder; real duration from master_audio artifact

  return (
    <div role="region" aria-label="主旁白播放器" className="flex flex-col gap-2 p-3 border rounded-lg bg-white">
      <audio
        ref={audioRef}
        src={masterAudio.master_audio_url}
        onTimeUpdate={onTimeUpdate}
        onEnded={onEnded}
        preload="metadata"
      />

      {/* Waveform visualisation placeholder */}
      <div className="h-8 w-full bg-gradient-to-r from-blue-50 to-indigo-50 rounded" />

      {/* Controls row */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onPlayPause}
          aria-label={playing ? "暂停播放" : "播放"}
          className="px-3 py-1 rounded bg-blue-600 text-white text-sm hover:bg-blue-700"
        >
          {playing ? "⏸" : "▶"}
        </button>

        {/* Progress bar */}
        <div className="flex-1" role="progressbar" aria-label="播放进度" aria-valuenow={currentTime} aria-valuemin={0} aria-valuemax={duration}>
          <div className="h-1.5 bg-gray-200 rounded-full">
            <div
              className="h-1.5 bg-blue-500 rounded-full transition-all"
              style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
            />
          </div>
        </div>

        <a
          href={masterAudio.download_url}
          aria-label="下载音频文件"
          download
          className="px-3 py-1 rounded bg-gray-100 text-gray-700 text-sm hover:bg-gray-200"
        >
          下载
        </a>
      </div>
    </div>
  );
}
