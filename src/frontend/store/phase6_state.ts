import { create } from "zustand";
import type { MasterAudioView } from "../types/audio_master";

export type StepState = 1 | 2 | 3;

interface Phase6State {
  step: StepState;
  userConfirmedLayout: boolean;
  finalMaster: MasterAudioView | null;
  confirmLayout: () => void;
  advanceToStep: (step: StepState) => void;
  setFinalMaster: (audio: MasterAudioView | null) => void;
  reset: () => void;
}

export const usePhase6Store = create<Phase6State>((set) => ({
  step: 1,
  userConfirmedLayout: false,
  finalMaster: null,
  confirmLayout: () => set({ userConfirmedLayout: true, step: 2 }),
  advanceToStep: (step) => set({ step }),
  setFinalMaster: (audio) => set({ finalMaster: audio, step: audio ? 3 : 2 }),
  reset: () => set({ step: 1, userConfirmedLayout: false, finalMaster: null }),
}));
