import type { ReactElement } from "react";
import type { MasterAudioView } from "@frontend/types/audio_master";

interface Props {
  masterAudio: MasterAudioView | null;
}

export function Phase6FinalMaster({ masterAudio }: Props): ReactElement | null {
  if (!masterAudio || masterAudio.kind !== "final_audio_master") return null;

  return (
    <section
      data-testid="p6-final-master"
      className="border rounded p-4 mt-4"
    >
      <h3 className="text-sm font-medium mb-2">最终主音频</h3>
      <p className="text-xs text-gray-500 mb-2">
        基于片段: {masterAudio.derived_from_segments.join(", ")}
      </p>
      <div className="mb-2 h-16 bg-gray-100 rounded flex items-center justify-center">
        <button
          aria-label="播放最终音频"
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
        aria-label="下载最终音频"
        className="text-xs text-blue-600 underline"
      >
        下载
      </a>
    </section>
  );
}
