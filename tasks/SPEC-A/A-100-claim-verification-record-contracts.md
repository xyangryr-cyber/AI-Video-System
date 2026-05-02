# [SPEC-A-100] Claim / VerificationRecord 统一数据模型

## Metadata
- **task_id**: SPEC-A-100
- **spec_ref**: `SPEC-A` §A-BDD-1(含 SPEC-0A.8)
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M

## Scope
定义 Claim 与 VerificationRecord 的统一数据模型,覆盖 JSON Schema、Pydantic、TypeScript 三方契约,并提供 SQLAlchemy 模型 + DDL 迁移脚本,同时兼容 v3.15 `key_data_points.data_point_id` 老 ID。

## Allowed Files
- `src/shared/schemas/claim.py`
- `src/shared/types/claim.ts`
- `schemas/claim.schema.json`
- `schemas/verification_record.schema.json`
- `src/backend/models/claim.py`
- `src/backend/models/verification_record.py`
- `migrations/V{NNN}__create_claim_tables.sql`
- `tests/unit/contracts/test_claim_schema.py`
- `tests/unit/contracts/test_claim_migration.py`

## Forbidden Files
- `src/backend/api/**`
- `src/backend/agents/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `Claim` pydantic round-trip 通过(claim_id/claim_type/text/source_phase/source_artifact/verification_status/blocking_level/created_at/updated_at)
- [ ] AC-2: `VerificationRecord` 包含 verification_id/claim_id/verifier_type/verdict/evidence/verified_at/expires_at
- [ ] AC-3: DDL 迁移脚本创建 `claims` + `verification_records` 两张表,含索引 + FK
- [ ] AC-4: v3.15 `key_data_points.data_point_id` 兼容:迁移脚本 INSERT 转换为 `Claim.claim_id`(保持旧 ID 可查)
- [ ] AC-5: TS interface 与 pydantic 字段一致(contract boundary)

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_100.py -v
```

## Completion Definition
所有 AC 通过、Claim/VerificationRecord 在三方契约一致,迁移脚本可执行且兼容 v3.15 旧 ID,所有列出的测试用例 GREEN。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_100.py | test_claim_pydantic_rejects_missing_blocking_level |
| AC-1 | tests/unit/contracts/test_spec_a_100.py | test_claim_pydantic_round_trip |
| AC-2 | tests/unit/contracts/test_spec_a_100.py | test_verification_record_pydantic_round_trip |
| AC-3 | tests/unit/contracts/test_spec_a_100.py | test_migration_creates_claims_and_verification_records_tables |
| AC-4 | tests/unit/contracts/test_spec_a_100.py | test_migration_preserves_v315_data_point_id_as_claim_id |
| AC-5 | tests/unit/contracts/test_spec_a_100.py | test_ts_interface_matches_pydantic_fields |
