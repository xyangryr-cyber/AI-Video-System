# [SPEC-F-006] React Community Components: Event Timeline, Relationship Graph, Map Annotation, Data Card

## Metadata
- **task_id**: SPEC-F-006
- **spec_ref**: SPEC-18.2.1, SPEC-18.2.2
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement 4 templates using pinned community libraries + Framer Motion: `event_timeline` (react-chrono ^2.6 + whileInView), `relationship_graph` (@nivo/network ^0.87 + SVG pathLength), `map_annotation` (react-simple-maps ^3.0 + Framer Motion), `data_card` (Framer Motion useSpring counter + ECharts sparkline). All must implement `React.FC<TemplateProps>`.

## Allowed Files
- `src/frontend/components/templates/react/EventTimeline.tsx`
- `src/frontend/components/templates/react/RelationshipGraph.tsx`
- `src/frontend/components/templates/react/MapAnnotation.tsx`
- `src/frontend/components/templates/react/DataCard.tsx`
- `src/frontend/components/templates/template_registry.ts`
- `package.json` (add dependencies only)
- `tests/unit/media-render/test_react_community_components.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `event_timeline` uses react-chrono ^2.6 + Framer Motion `whileInView` for node pop-in
- [ ] AC-2: `relationship_graph` uses @nivo/network ^0.87 + SVG `pathLength` for edge draw animation
- [ ] AC-3: `map_annotation` uses react-simple-maps ^3.0 + Framer Motion for marker/line/annotation animation
- [ ] AC-4: `data_card` uses Framer Motion `useSpring` for count animation + ECharts sparkline mini-chart
- [ ] AC-5: All 4 implement `React.FC<TemplateProps>` and are registered in `template_registry.ts`
- [ ] AC-6: Community library versions pinned in package.json: react-chrono ^2.6, @nivo/network ^0.87, react-simple-maps ^3.0

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_006.py -v
npx tsc --noEmit
node -e "const pkg=require('./package.json'); const d={...pkg.dependencies,...pkg.devDependencies}; console.assert(d['react-chrono']?.startsWith('^2.6')); console.assert(d['@nivo/network']?.startsWith('^0.87')); console.assert(d['react-simple-maps']?.startsWith('^3.0')); console.log('OK: deps pinned')"
```

## Completion Definition
Four community-library-based components render correctly, use pinned library versions, are registered in template_registry, and all tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_006.py | test_event_timeline_react_chrono |
| AC-2 | tests/unit/media-render/test_spec_f_006.py | test_relationship_graph_nivo_pathLength |
| AC-3 | tests/unit/media-render/test_spec_f_006.py | test_map_annotation_react_simple_maps |
| AC-4 | tests/unit/media-render/test_spec_f_006.py | test_data_card_usespring_sparkline |
| AC-5 | tests/unit/media-render/test_spec_f_006.py | test_all_implement_template_props |
| AC-6 | tests/unit/media-render/test_spec_f_006.py | test_dependency_versions_pinned |
