import { type ReactNode, type ReactElement } from "react";
import { MasterAudioPlayer } from "@frontend/components/phase4/MasterAudioPlayer";
import type { GetMasterAudioResponse } from "@shared/types/api_master_audio";

interface Props {
  masterAudio: GetMasterAudioResponse | null | undefined;
  children?: ReactNode;
}

export function Phase4Preview({ masterAudio, children }: Props): ReactElement {
  return (
    <div className="flex flex-col gap-4">
      <MasterAudioPlayer masterAudio={masterAudio} />
      {children}
    </div>
  );
}
