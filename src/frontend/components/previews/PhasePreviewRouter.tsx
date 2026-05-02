import type {
  RequirementsJSON,
  ScriptSegment,
  VoiceDirection,
  AudioSegment,
  SfxItem,
  StoryboardShot,
  VideoFrame,
  BrollItem,
  FinalDistribution,
} from '@frontend/types/preview';

import { P0RequirementsView } from './P0RequirementsView';
import { P1ScriptView } from './P1ScriptView';
import { P2SegmentView } from './P2SegmentView';
import { P3VoiceScriptView } from './P3VoiceScriptView';
import { P4SegmentAudioPlayer } from './P4SegmentAudioPlayer';
import { P5WaveformPlayer } from './P5WaveformPlayer';
import { P6SfxListPlayer } from './P6SfxListPlayer';
import { P7StoryboardGallery } from './P7StoryboardGallery';
import { P8FrameGallery } from './P8FrameGallery';
import { P9BrollGallery } from './P9BrollGallery';
import { P10VideoPlayer } from './P10VideoPlayer';
import { P11FinalPlayer } from './P11FinalPlayer';

interface PhasePreviewRouterProps {
  phase: number;
  artifactData?: Record<string, unknown> | null;
}

/** Build a markdown-ish content string from P1 narrative beats for P1ScriptView. */
function buildP1Content(versions: Array<Record<string, unknown>> | undefined): string {
  if (!versions || versions.length === 0) return '';
  const v = versions[0];
  const beats = v['narrative_beats'] as Array<Record<string, unknown>> | undefined;
  if (!beats || beats.length === 0) return '';
  return beats
    .map((b) => `### ${b['title'] || b['type'] || ''}\n${b['key_points'] || ''}`)
    .join('\n\n');
}

export function PhasePreviewRouter({ phase, artifactData }: PhasePreviewRouterProps) {
  switch (phase) {
    case 0:
      return (
        <P0RequirementsView
          requirements={artifactData as RequirementsJSON | undefined}
        />
      );
    case 1: {
      const versions = artifactData?.['versions'] as Array<Record<string, unknown>> | undefined;
      const content = buildP1Content(versions);
      return (
        <P1ScriptView
          content={content || undefined}
          versions={versions?.length}
        />
      );
    }
    case 2:
      return (
        <P2SegmentView
          segments={(Array.isArray(artifactData) ? artifactData : artifactData?.['segments']) as ScriptSegment[] | undefined}
        />
      );
    case 3: {
      const segments = artifactData?.['segments'] as Array<Record<string, unknown>> | undefined;
      const content = segments?.map((s) => s['content']).filter(Boolean).join('\n\n') || '';
      const voice_directions = segments
        ?.map((s) => s['voice_direction'])
        .filter(Boolean) as VoiceDirection[] | undefined;
      return (
        <P3VoiceScriptView
          content={content || undefined}
          voice_directions={voice_directions}
        />
      );
    }
    case 4:
      return (
        <P4SegmentAudioPlayer
          segments={artifactData?.['segments'] as AudioSegment[] | undefined}
        />
      );
    case 5:
      return (
        <P5WaveformPlayer
          audio_url={artifactData?.['audio_url'] as string | undefined}
          duration_sec={artifactData?.['duration_sec'] as number | undefined}
        />
      );
    case 6:
      return (
        <P6SfxListPlayer
          sfx_list={artifactData?.['sfx_list'] as SfxItem[] | undefined}
        />
      );
    case 7:
      return (
        <P7StoryboardGallery
          shots={artifactData?.['shots'] as StoryboardShot[] | undefined}
        />
      );
    case 8:
      return (
        <P8FrameGallery
          frames={artifactData?.['frames'] as VideoFrame[] | undefined}
        />
      );
    case 9:
      return (
        <P9BrollGallery
          brolls={artifactData?.['brolls'] as BrollItem[] | undefined}
        />
      );
    case 10:
      return (
        <P10VideoPlayer
          video_url={artifactData?.['video_url'] as string | undefined}
          duration_sec={artifactData?.['duration_sec'] as number | undefined}
          subtitles_url={artifactData?.['subtitles_url'] as string | undefined}
        />
      );
    case 11:
      return (
        <P11FinalPlayer
          video_url={artifactData?.['video_url'] as string | undefined}
          covers={artifactData?.['covers'] as FinalDistribution['covers'] | undefined}
          download_urls={artifactData?.['download_urls'] as Record<string, string> | undefined}
        />
      );
    default:
      return (
        <div data-testid="preview-empty" className="flex items-center justify-center h-64 text-gray-400">
          <p>Phase {phase} preview not supported</p>
        </div>
      );
  }
}
