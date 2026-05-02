# [SPEC-E-100] 项目列表自动打开最新阶段

## Metadata
- **task_id**: SPEC-E-100
- **spec_ref**: SPEC-E §E-BDD-1
- **depends_on**: [SPEC-A-102]
- **priority**: P0
- **estimated_complexity**: S
- **bdd_tags**: [@navigation]

## Scope
项目卡片读取并对比 `latest_reached_phase` 与 `current_phase`，差异时显示角标；点击卡片直接跳转到最新到达阶段的详情路由，提升项目恢复效率。

## Allowed Files
- `src/frontend/components/ProjectCard.tsx`
- `src/frontend/pages/projects/index.tsx`
- `src/frontend/hooks/useLatestReachedPhase.ts`
- `tests/e2e/project_list_autoopen.spec.ts`

## Acceptance Criteria
- [ ] AC-1: 卡片显示 latest_reached_phase vs current_phase 角标(差异时)
- [ ] AC-2: 点击卡片 100% 跳转 `/projects/{id}/phases/{latest_reached_phase}`
- [ ] AC-3: current_phase === latest_reached_phase 时无角标

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_100.py -v
npx playwright test tests/e2e/project_list_autoopen.spec.ts
```

## Completion Definition
项目列表卡片正确显示阶段差异角标，点击行为按 latest_reached_phase 跳转，且无差异时不显示角标，所有 e2e 用例通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_100.py | shows_phase_diff_badge_when_phases_differ |
| AC-2 | tests/unit/frontend/test_spec_e_100.py | clicks_card_routes_to_latest_reached_phase |
| AC-3 | tests/unit/frontend/test_spec_e_100.py | hides_badge_when_phases_equal |
