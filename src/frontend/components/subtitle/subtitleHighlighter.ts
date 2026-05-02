// [SPEC-F-010] Subtitle keyword highlighter — programmatic, zero API calls.
// Priority: key_data_point > percentage > number > proper_noun.
// When a word matches multiple rules, only the highest-priority rule applies.

import type { HighlightRuleType, HighlightRule } from "./subtitleStyle";

export interface HighlightedWord {
  word: string;
  highlight_type: HighlightRuleType | null;
  /** The rule that matched (highest priority only) */
  matched_rule: HighlightRule | null;
}

/**
 * Highlight rules ordered by priority (highest first).
 * key_data_point=0, percentage=1, number=2, proper_noun=3.
 */
const RULES_BY_PRIORITY: HighlightRuleType[] = [
  "key_data_point",
  "percentage",
  "number",
  "proper_noun",
];

/**
 * Check if a word is a percentage (e.g. "15%", "3.5%").
 */
function isPercentage(word: string): boolean {
  return /^\d+(\.\d+)?%$/.test(word);
}

/**
 * Check if a word is a number (integer or decimal, with optional commas).
 */
function isNumber(word: string): boolean {
  return /^[\d,]+(\.\d+)?$/.test(word) || /^\d+(\.\d+)?[万亿]$/.test(word);
}

/**
 * Check if a word is a proper noun (capitalized, CJK not applicable).
 * For CJK: proper nouns are detected by a known-names list.
 */
function isProperNoun(word: string, knownNouns: Set<string>): boolean {
  if (knownNouns.has(word)) return true;
  // Latin proper nouns: capitalized first letter
  return /^[A-Z][a-z]+$/.test(word);
}

/**
 * Determine the single highest-priority highlight type for a word.
 * Returns null if no rule matches.
 */
export function getHighlightType(
  word: string,
  keyDataPointWords: Set<string>,
  knownProperNouns: Set<string> = new Set()
): HighlightedWord {
  // Check rules in priority order — first match wins
  for (const ruleType of RULES_BY_PRIORITY) {
    let matched = false;

    switch (ruleType) {
      case "key_data_point":
        matched = keyDataPointWords.has(word.toLowerCase());
        break;
      case "percentage":
        matched = isPercentage(word);
        break;
      case "number":
        matched = isNumber(word);
        break;
      case "proper_noun":
        matched = isProperNoun(word, knownProperNouns);
        break;
    }

    if (matched) {
      return {
        word,
        highlight_type: ruleType,
        matched_rule: {
          type: ruleType,
          priority: RULES_BY_PRIORITY.indexOf(ruleType),
        },
      };
    }
  }

  return { word, highlight_type: null, matched_rule: null };
}

/**
 * Highlight all words in a sentence.
 * Each word gets at most one highlight type (highest priority wins).
 */
export function highlightWords(
  words: string[],
  keyDataPointWords: Set<string>
): HighlightedWord[] {
  return words.map((word) => getHighlightType(word, keyDataPointWords));
}

/**
 * Check whether a highlighted word's value is consistent with key_data_point.
 * Returns true if consistent, false on mismatch.
 */
export function checkKeyDataPointConsistency(
  word: string,
  highlightType: HighlightRuleType | null,
  keyDataPointValue: string | number | undefined
): boolean {
  if (highlightType === "key_data_point" && keyDataPointValue !== undefined) {
    const normalized = String(keyDataPointValue).toLowerCase();
    return word.toLowerCase().includes(normalized) || normalized.includes(word.toLowerCase());
  }
  return true;
}
