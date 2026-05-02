import type { ReactElement } from "react";
import { Phase6ScriptAnnotationView } from "./Phase6ScriptAnnotationView";
import { Phase6SegmentMixList } from "./Phase6SegmentMixList";
import { Phase6FinalMaster } from "./Phase6FinalMaster";
import { usePhase6Store } from "@frontend/store/phase6_state";
import type { AnnotationSpan } from "@frontend/types/annotation_span";

interface SegmentEntry {
  id: string;
  index: number;
  preview_url: string;
  text: string;
}

interface Props {
  fullText: string;
  annotationSpans: AnnotationSpan[];
  segments: SegmentEntry[];
}

export function Phase6Pipeline({ fullText, annotationSpans, segments }: Props): ReactElement {
  const { step, userConfirmedLayout, finalMaster, confirmLayout } = usePhase6Store();

  return (
    <div data-testid="p6-pipeline" className="space-y-4">
      {step >= 1 && (
        <Phase6ScriptAnnotationView
          fullText={fullText}
          annotationSpans={annotationSpans}
          onConfirm={confirmLayout}
        />
      )}

      {step >= 2 && (
        <Phase6SegmentMixList
          segments={segments}
          confirmed={userConfirmedLayout}
          onMixFeedback={() => {}}
        />
      )}

      {step >= 3 && <Phase6FinalMaster masterAudio={finalMaster} />}
    </div>
  );
}
