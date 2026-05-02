import { create } from "zustand";
import type { MasterAudioView } from "../types/audio_master";

interface Phase5State {
  masterAudio: MasterAudioView | null;
  selectedCandidateId: string | null;
  setMasterAudio: (audio: MasterAudioView | null) => void;
  selectCandidate: (id: string) => void;
  reset: () => void;
}

export const usePhase5Store = create<Phase5State>((set) => ({
  masterAudio: null,
  selectedCandidateId: null,
  setMasterAudio: (audio) => set({ masterAudio: audio }),
  selectCandidate: (id) => set({ selectedCandidateId: id }),
  reset: () => set({ masterAudio: null, selectedCandidateId: null }),
}));
