import type { ReactElement } from "react";
import type { MasterAudioView } from "@frontend/types/audio_master";

interface Props {
  masterAudio: MasterAudioView | null;
}

export function Phase5MasterPlayer({ masterAudio }: Props): ReactElement | null {
  if (!masterAudio) return null;

  return (
    <section
      role="region"
      aria-label="P5 主播放器"
      data-testid="p5-master-player"
      className="border rounded p-4 mt-4"
    >
      <h3 className="text-sm font-medium mb-2">
        {masterAudio.kind === "bgm_mix_master"
          ? "BGM 混音主音频"
          : "旁白主音频"}
      </h3>

      <div className="mb-2 h-16 bg-gray-100 rounded flex items-center justify-center">
        <button
          aria-label="播放主音频"
          className="px-3 py-1 border rounded text-sm"
          onClick={() => {
            const a = new Audio(masterAudio.file_path);
            a.play();
          }}
        >
          播放
        </button>
      </div>

      <a
        href={masterAudio.file_path}
        download
        aria-label="下载主音频"
        className="text-xs text-blue-600 underline"
      >
        下载
      </a>
    </section>
  );
}
