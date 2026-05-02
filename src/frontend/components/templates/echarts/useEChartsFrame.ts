// Pure computation module for frame-based ECharts data progression.
// No React dependency — exported functions are deterministic and testable.
// SPEC-18.1.3: EChartsFrameController frame math + pause trigger detection.

export type EasingType = "linear" | "ease_in" | "ease_out" | "ease_in_out";

export interface PauseTriggerInput {
  at_progress: number;
  duration_sec: number;
}

export interface ComputeFrameStateInput {
  frame: number;
  fps: number;
  durationInFrames: number;
  pauseTriggers: PauseTriggerInput[];
}

export interface FrameState {
  easedProgress: number;
  isPaused: boolean;
  pauseRemainingFrames: number;
  dataIndex: number;
}

export function applyEasing(progress: number, easing: EasingType): number {
  switch (easing) {
    case "ease_in":
      return progress * progress;
    case "ease_out":
      return progress * (2 - progress);
    case "ease_in_out":
      return progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
    default:
      return progress;
  }
}

export function computeFrameState(input: ComputeFrameStateInput): FrameState {
  const { frame, fps, durationInFrames, pauseTriggers } = input;

  if (durationInFrames <= 0) {
    return {
      easedProgress: 0,
      isPaused: false,
      pauseRemainingFrames: 0,
      dataIndex: 0,
    };
  }

  const sorted = [...pauseTriggers].sort((a, b) => a.at_progress - b.at_progress);

  let totalPauseFrames = 0;

  for (const trigger of sorted) {
    const pauseFrames = Math.round(trigger.duration_sec * fps);
    const effectiveFrame = Math.max(0, frame - totalPauseFrames);
    const progress = effectiveFrame / durationInFrames;

    // AC-3: pause_trigger activates when Math.abs(easedProgress - trigger.at_progress) < 0.01
    if (Math.abs(progress - trigger.at_progress) < 0.01 || progress >= trigger.at_progress) {
      const triggerFrame = trigger.at_progress * durationInFrames + totalPauseFrames;
      const endFrame = triggerFrame + pauseFrames;

      // AC-5: during pause, easedProgress holds at trigger.at_progress
      if (frame >= triggerFrame && frame < endFrame) {
        return {
          easedProgress: trigger.at_progress,
          isPaused: true,
          pauseRemainingFrames: endFrame - frame,
          dataIndex: Math.floor(trigger.at_progress * durationInFrames),
        };
      }

      // AC-5: after pause completed, accumulate so resume continues from correct position
      if (frame >= endFrame) {
        totalPauseFrames += pauseFrames;
      }
    }
  }

  // AC-5: effective frame accounts for completed pauses
  const effectiveFrame = Math.max(0, frame - totalPauseFrames);
  const easedProgress = Math.min(effectiveFrame / durationInFrames, 1);

  return {
    easedProgress,
    isPaused: false,
    pauseRemainingFrames: 0,
    dataIndex: Math.floor(easedProgress * durationInFrames),
  };
}
