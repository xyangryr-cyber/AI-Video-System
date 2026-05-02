import type { ReactElement } from "react";
import { Phase5CandidateCard } from "./Phase5CandidateCard";
import { Phase5MasterPlayer } from "./Phase5MasterPlayer";
import { usePhase5Store } from "@frontend/store/phase5_master";
import type { BgmCandidate } from "./Phase5CandidateCard";
import type { MasterAudioView } from "@frontend/types/audio_master";

interface Props {
  candidates: BgmCandidate[];
}

export function Phase5CandidateGrid({ candidates }: Props): ReactElement {
  const { masterAudio, selectedCandidateId, setMasterAudio, selectCandidate } =
    usePhase5Store();

  const handleSelect = (candidate: BgmCandidate) => {
    selectCandidate(candidate.id);
    const master: MasterAudioView = {
      kind: "bgm_mix_master",
      file_path: candidate.preview_url,
      based_on_phase: 5,
      derived_from_segments: [],
      total_duration_seconds: 0,
      checksum: "",
      version: 1,
      source_ref: { kind: "narration_master", checksum: "" },
    };
    setMasterAudio(master);
  };

  const handleNoBgm = () => {
    selectCandidate("no_bgm");
    const master: MasterAudioView = {
      kind: "narration_master",
      file_path: "",
      based_on_phase: 5,
      derived_from_segments: [],
      total_duration_seconds: 0,
      checksum: "",
      version: 1,
    };
    setMasterAudio(master);
  };

  return (
    <div data-testid="p5-candidate-grid">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {candidates.map((c) => (
          <Phase5CandidateCard
            key={c.id}
            candidate={c}
            isSelected={selectedCandidateId === c.id}
            onSelect={handleSelect}
          />
        ))}
      </div>

      <div className="mt-4">
        <button
          aria-label="无 BGM 回退旁白"
          className="px-3 py-1 text-sm border rounded"
          onClick={handleNoBgm}
        >
          无 BGM（回退旁白）
        </button>
      </div>

      <Phase5MasterPlayer masterAudio={masterAudio} />
    </div>
  );
}
