# [SPEC-F-010] Subtitle System: Style, Highlight & Rendering

## Metadata
- **task_id**: SPEC-F-010
- **spec_ref**: SPEC-20.1, SPEC-20.1B, SPEC-20.2
- **depends_on**: [SPEC-A-001, SPEC-F-007]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement subtitle system: `subtitle_style` in theme.json (font/color/stroke/background/position/highlight_rules/animation), keyword highlighter (programmatic, 0 LLM tokens, priority: key_data_point > percentage > number > proper_noun), Whisper word-level alignment → `subtitle_words[]` (SubtitleWord schema from SPEC-A), `SubtitleRenderer` with word-by-word and sentence modes, and AVSyncReviewer L1 check (highlight word vs key_data_point consistency, AV offset <100ms, subtitle alignment <200ms).

## Allowed Files
- `src/frontend/components/subtitle/SubtitleRenderer.tsx`
- `src/frontend/components/subtitle/subtitleHighlighter.ts`
- `src/frontend/components/subtitle/subtitleStyle.ts`
- `src/frontend/components/subtitle/AVSyncReviewer.ts`
- `tests/unit/media-render/test_subtitle_system.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `subtitle_style` config contains font, color, stroke, background, position, highlight_rules, animation fields
- [ ] AC-2: When a word matches multiple highlight rules, only the highest priority rule applies
- [ ] AC-3: `subtitle_highlighter` has zero LLM calls
- [ ] AC-4: `subtitle_words` entries contain word, start_sec, end_sec, highlight_type (matching SPEC-A SubtitleWord schema)
- [ ] AC-5: Highlight word value inconsistent with `key_data_point` triggers FAIL
- [ ] AC-6: Whisper word-level alignment error < 200ms
- [ ] AC-7: AV offset > 100ms triggers FAIL in AVSyncReviewer
- [ ] AC-8: Blank frames > 0 triggers FAIL in AVSyncReviewer

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_010.py -v
npx tsc --noEmit
```

## Completion Definition
Subtitle renderer displays word-by-word and sentence modes with correct highlight priority, AVSyncReviewer catches timing and consistency violations, all programmatic (no LLM), and all tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_010.py | test_subtitle_style_fields |
| AC-2 | tests/unit/media-render/test_spec_f_010.py | test_highlight_priority_highest_wins |
| AC-3 | tests/unit/media-render/test_spec_f_010.py | test_highlighter_no_llm_calls |
| AC-4 | tests/unit/media-render/test_spec_f_010.py | test_subtitle_words_schema |
| AC-5 | tests/unit/media-render/test_spec_f_010.py | test_highlight_key_data_point_mismatch_fail |
| AC-6 | tests/unit/media-render/test_spec_f_010.py | test_whisper_alignment_under_200ms |
| AC-7 | tests/unit/media-render/test_spec_f_010.py | test_av_offset_over_100ms_fail |
| AC-8 | tests/unit/media-render/test_spec_f_010.py | test_blank_frames_fail |
