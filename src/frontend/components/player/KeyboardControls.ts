// [SPEC-F-012] Keyboard controls for preview player.
// Arrow keys: frame stepping (1 frame / 10 frames with Shift).
// JKL: shuttle control. M: timeline annotation.

export type KeyboardAction =
  | "step_forward_1"
  | "step_backward_1"
  | "step_forward_10"
  | "step_backward_10"
  | "toggle_play"
  | "speed_up"
  | "speed_down"
  | "annotate"
  | "speed_0_5x"
  | "speed_1x"
  | "speed_1_5x"
  | "speed_2x";

export interface KeyboardMapping {
  key: string;
  shiftKey: boolean;
  action: KeyboardAction;
  /** Frame delta for step actions */
  frameDelta?: number;
}

export const DEFAULT_KEYBOARD_MAPPINGS: KeyboardMapping[] = [
  { key: "ArrowRight", shiftKey: false, action: "step_forward_1", frameDelta: 1 },
  { key: "ArrowLeft", shiftKey: false, action: "step_backward_1", frameDelta: -1 },
  { key: "ArrowRight", shiftKey: true, action: "step_forward_10", frameDelta: 10 },
  { key: "ArrowLeft", shiftKey: true, action: "step_backward_10", frameDelta: -10 },
  { key: " ", shiftKey: false, action: "toggle_play" },
  { key: "j", shiftKey: false, action: "speed_down" },
  { key: "k", shiftKey: false, action: "toggle_play" },
  { key: "l", shiftKey: false, action: "speed_up" },
  { key: "m", shiftKey: false, action: "annotate" },
  { key: "1", shiftKey: false, action: "speed_0_5x" },
  { key: "2", shiftKey: false, action: "speed_1x" },
  { key: "3", shiftKey: false, action: "speed_1_5x" },
  { key: "4", shiftKey: false, action: "speed_2x" },
];

/**
 * Match a keyboard event to an action.
 * Returns the matched action or null.
 */
export function matchKeyboardAction(event: KeyboardEvent): KeyboardMapping | null {
  for (const mapping of DEFAULT_KEYBOARD_MAPPINGS) {
    if (event.key === mapping.key && event.shiftKey === mapping.shiftKey) {
      return mapping;
    }
  }
  return null;
}

/**
 * Handle a keyboard event for the preview player.
 * Returns the new frame number after applying step actions.
 */
export function handleKeyboardFrameStep(
  event: KeyboardEvent,
  currentFrame: number,
  totalFrames: number,
): number {
  const mapping = matchKeyboardAction(event);
  if (!mapping || mapping.frameDelta === undefined) return currentFrame;

  const newFrame = currentFrame + mapping.frameDelta;
  return Math.max(0, Math.min(newFrame, totalFrames - 1));
}
