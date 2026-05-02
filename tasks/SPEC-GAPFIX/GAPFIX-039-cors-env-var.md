# [SPEC-GAPFIX-039] CORS allow_origins 环境变量化

## Metadata
- **task_id**: SPEC-GAPFIX-039
- **spec_ref**: 第四轮扫描报告 发现 2.3; HARNESS §11.6
- **depends_on**: []
- **priority**: P2
- **estimated_complexity**: S

## Scope
`src/backend/api/main.py:25` 中 CORS `allow_origins=["http://localhost:3000"]` 硬编码。非 localhost 访问时 CORS 拒绝请求。

修复: 从环境变量 `CORS_ORIGINS` 读取, 逗号分隔, 默认 `http://localhost:3000`:
```python
import os
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, ...)
```

## Allowed Files
- `src/backend/api/main.py`

## Forbidden Files
- `src/frontend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `allow_origins` 从 `os.getenv("CORS_ORIGINS")` 读取
- [ ] AC-2: 默认值 `http://localhost:3000`
- [ ] AC-3: 支持逗号分隔多 origin
- [ ] AC-4: `pytest tests/unit/infra/test_api_main.py -v` 通过

## Verification Commands
```bash
# 验证 CORS 配置
grep -n "CORS_ORIGINS\|allow_origins" src/backend/api/main.py
# 单元测试
.venv/bin/python -m pytest tests/unit/infra/test_api_main.py -v
```

## Completion Definition
CORS allow_origins 从环境变量读取, 支持多 origin 逗号分隔。现有测试通过。

## Note
Per HARNESS §4.3, config-level changes are TDD-exempt.
