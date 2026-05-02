# [SPEC-C-103] ClaimExtractor + VerificationOrchestrator

## Metadata
- **task_id**: SPEC-C-103
- **spec_ref**: `SPEC-C` §C-BDD-4
- **depends_on**: [SPEC-A-100, SPEC-B-100]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现 ClaimExtractor 的 5 个触发点 + VerificationOrchestrator 调度 4 个 verifier（financial_data / fact_check / image_backed / citation），通过 (claim_type, entity, value, time_range) 去重键复用 claim_id，支持 polished_script v3→v4 增量重验，并在用户质疑后 60s 内将下游 artifacts 标记为 damaged。

## Allowed Files
- `src/backend/agents/claim_extractor.py`
- `src/backend/services/verification_orchestrator.py`
- `src/backend/services/verifiers/financial_data_verifier.py`
- `src/backend/services/verifiers/fact_check_verifier.py`
- `src/backend/services/verifiers/image_backed_verifier.py`
- `src/backend/services/verifiers/citation_verifier.py`
- `tests/integration/test_claim_lifecycle.py`

## Acceptance Criteria
- [ ] AC-1: 5 个触发点均能正确创建 Claim
- [ ] AC-2: 去重键 `(claim_type, entity, value, time_range)` 命中复用 claim_id
- [ ] AC-3: 增量重验:polished_script v3→v4 时仅新增/删除 claim 触发 verifier
- [ ] AC-4: 用户质疑 60s 内下游 artifacts 状态 = damaged

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_103.py -v
```

## Completion Definition
5 个触发点正确创建 Claim、去重键复用 claim_id、polished_script 版本演进只触发增量 verifier、用户质疑 60s 内下游 artifacts 转入 damaged，全部 AC 与集成测试通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_103.py | test_five_trigger_points_create_claim |
| AC-2 | tests/unit/backend-core/test_spec_c_103.py | test_dedup_key_reuses_claim_id |
| AC-3 | tests/unit/backend-core/test_spec_c_103.py | test_incremental_reverify_v3_to_v4 |
| AC-4 | tests/unit/backend-core/test_spec_c_103.py | test_user_challenge_marks_downstream_damaged_within_60s |
