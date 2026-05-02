# [SPEC-GAPFIX-025] SQLite 备份脚本

## Metadata
- **task_id**: SPEC-GAPFIX-025
- **spec_ref**: Design Spec §6.6
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: S

## Scope
Create `scripts/backup_sqlite.py` that copies `data/db/dev.sqlite3` → `data/db/app.sqlite3.bak` using `shutil.copy2`. This is a one-shot script, called before phase advance in `phase_ops.py`.

## Allowed Files
- `scripts/backup_sqlite.py`

## Forbidden Files
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `scripts/backup_sqlite.py` 存在且可执行
- [ ] AC-2: 运行 `python3 scripts/backup_sqlite.py` 创建 `data/db/app.sqlite3.bak`
- [ ] AC-3: 备份文件与源文件内容一致
- [ ] AC-4: 数据库文件不存在时输出错误信息但不崩溃

## Verification Commands
```bash
.venv/bin/python3 scripts/backup_sqlite.py
ls -la data/db/app.sqlite3.bak  # 期望文件存在
diff <(sqlite3 data/db/dev.sqlite3 .dump) <(sqlite3 data/db/app.sqlite3.bak .dump)  # 期望无差异
```

## Completion Definition
`scripts/backup_sqlite.py` 可用，`python3 scripts/backup_sqlite.py` 创建一致的备份文件。Per HARNESS §4.3, one-off scripts are TDD-exempt.
