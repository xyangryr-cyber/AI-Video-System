// SPEC-F-008 Voice Parameter Converter
// Pure functions — zero LLM calls, deterministic only.

import type { VoiceParams, SegmentVoiceOverrides } from "@shared/types/shared_types";

export type PaceLevel = "much_slower" | "slower" | "normal" | "faster" | "much_faster";

export type EnergyLevel = "low" | "normal" | "high";

export interface VoiceDirection {
  style_degree?: number;
  pace?: PaceLevel;
  energy?: EnergyLevel;
}

/** Pace lookup table: pace level → rate_multiplier */
const PACE_TABLE: Record<PaceLevel, number> = {
  much_slower: 0.8,
  slower: 0.9,
  normal: 1.0,
  faster: 1.1,
  much_faster: 1.2,
};

/** Energy lookup table: energy level → volume adjustment (as multiplier) */
const ENERGY_TABLE: Record<EnergyLevel, number> = {
  low: 0.9,
  normal: 1.0,
  high: 1.1,
};

/**
 * Validate and clamp style_degree to [0.01, 2.0] range.
 * Returns the validated value.
 */
export function validateStyleDegree(raw: number): number {
  if (raw < 0.01) {
    throw new RangeError(`style_degree ${raw} is below minimum 0.01`);
  }
  if (raw > 2.0) {
    throw new RangeError(`style_degree ${raw} exceeds maximum 2.0`);
  }
  return raw;
}

/**
 * Convert voice_direction + voice_params → segment_voice_overrides.
 * Pure function: same input always produces same output.
 */
export function voiceDirectionToOverrides(
  direction: VoiceDirection,
  baseParams: VoiceParams,
): SegmentVoiceOverrides {
  const styleDegree =
    direction.style_degree !== undefined
      ? validateStyleDegree(direction.style_degree)
      : baseParams.style_degree;

  const paceLevel: PaceLevel = direction.pace ?? "normal";
  const rateMultiplier = PACE_TABLE[paceLevel];

  const energyLevel: EnergyLevel = direction.energy ?? "normal";
  const volumeMultiplier = ENERGY_TABLE[energyLevel];
  const volume = Math.round(baseParams.volume * volumeMultiplier);

  return {
    rate_multiplier: rateMultiplier,
    emotion: baseParams.style,
    style_degree: styleDegree,
    emphasis_words: [],
    volume,
  };
}

/**
 * Lookup pace multiplier from pace level.
 */
export function getPaceMultiplier(pace: PaceLevel): number {
  return PACE_TABLE[pace];
}

/**
 * Lookup energy volume adjustment from energy level.
 */
export function getEnergyVolume(energy: EnergyLevel): number {
  return ENERGY_TABLE[energy];
}
