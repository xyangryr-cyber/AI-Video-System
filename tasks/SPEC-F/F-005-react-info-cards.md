# [SPEC-F-005] React Community Components: News Card, Quote Card, Policy Comparison

## Metadata
- **task_id**: SPEC-F-005
- **spec_ref**: SPEC-18.2.1
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement 3 information visualization templates using Framer Motion: `news_card` (slide-in + staggerChildren + Lottie sentiment icon), `quote_card` (motion.span word-by-word + Lottie quotation animation), `policy_comparison` (AnimatePresence + layout animation row-by-row fill + motion.tr highlight row scale). All must implement `React.FC<TemplateProps>`.

## Allowed Files
- `src/frontend/components/templates/react/NewsCard.tsx`
- `src/frontend/components/templates/react/QuoteCard.tsx`
- `src/frontend/components/templates/react/PolicyComparison.tsx`
- `src/frontend/components/templates/template_registry.ts`
- `tests/unit/media-render/test_react_info_cards.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `news_card` uses Framer Motion `<motion.div>` slide-in + `staggerChildren` for line-by-line fade-in
- [ ] AC-2: `news_card` uses Lottie for sentiment icon animation
- [ ] AC-3: `quote_card` uses `<motion.span>` for word-by-word display
- [ ] AC-4: `quote_card` uses Lottie for quotation mark expand animation
- [ ] AC-5: `policy_comparison` uses `<AnimatePresence>` + `layout` animation for row-by-row fill
- [ ] AC-6: `policy_comparison` uses `<motion.tr>` for highlight row scale
- [ ] AC-7: All 3 implement `React.FC<TemplateProps>` and are registered in `template_registry.ts`
- [ ] AC-8: No `react-vertical-timeline` or `react-force-graph` in dependencies

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_005.py -v
npx tsc --noEmit
grep -r "react-vertical-timeline\|react-force-graph" package.json && exit 1 || echo "OK: no excluded deps"
```

## Completion Definition
Three Framer Motion-based info visualization components render correctly, are registered in template_registry, use correct animation techniques, and no excluded libraries are present. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_005.py | test_news_card_stagger_children |
| AC-2 | tests/unit/media-render/test_spec_f_005.py | test_news_card_lottie_sentiment |
| AC-3 | tests/unit/media-render/test_spec_f_005.py | test_quote_card_word_by_word |
| AC-4 | tests/unit/media-render/test_spec_f_005.py | test_quote_card_lottie_quotation |
| AC-5 | tests/unit/media-render/test_spec_f_005.py | test_policy_comparison_animate_presence |
| AC-6 | tests/unit/media-render/test_spec_f_005.py | test_policy_comparison_highlight_row |
| AC-7 | tests/unit/media-render/test_spec_f_005.py | test_all_implement_template_props |
| AC-8 | tests/unit/media-render/test_spec_f_005.py | test_no_excluded_dependencies |
