# Venv 修复 + Requirements 补全 实施方案交接文档

> **本文档身份**：交接给另一个 AI（实施 AI）的工作单
> **目的**：让 `.venv` 拥有全部 SPEC-A..F + SPEC-G 所需依赖，**消除 17 个 collection error**，取得干净 baseline
> **创建于**：2026-04-25
> **背景作者**：上游 AI（已和许阳达成"启动 SPEC-G 前先冷启动环境"的决策）
> **优先级**：**P0**（阻塞 SPEC-G-000-pre 之外**所有 G 子卡**——huey 不在则 G-000b/c/d 物理上写不出代码；numpy 不在则 SPEC-C-018/019/020 测试无法 collect，回归判据失效）
> **预估工时**：S（30-60 分钟）

---

## 0. 实施 AI 必读

### 0.1 任务边界（不要扩张）
- **范围**：仅修 `.venv` 与 `requirements.txt` / `requirements-dev.txt`，让 `pytest tests/unit/ -q` 0 collection error。**仅此而已**。
- **不在范围**：
  - 不要修任何业务代码（src/backend、src/frontend、tests/、scripts/）
  - 不要"顺手"升级 SPEC 已 pin 的库版本（如 `pydantic>=2.5` 不要改成 `>=2.6`）
  - 不要修 23 个历史 unit test 失败——那是 `tasks/HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF.md` 的活
  - 不要建 worktree——本任务在 **main 主分支**直接做（影响所有下游 worktree）

### 0.2 必读
1. 本文档全文
2. `HARNESS.md` §7（allowed/forbidden 命令）、§9 PROGRESS、§10 CI gate
3. 当前 `requirements.txt` + `requirements-dev.txt` + `pyproject.toml`
4. `src/backend/workers/huey_config.py`（确认对 huey 的版本依赖）

### 0.3 必须做
- 跑命令前**先看一遍当前 .venv 已装包**，避免重复安装
- 装包后用 Python 实际 import 一次确认成功
- baseline 重跑后把数字写进 commit body
- main 分支单 commit 完成，prefix `[INFRA]` 或 `[SPEC-G-prep-2]`

### 0.4 不要做
- 不要 `pip install --upgrade pip`（破坏可重复构建）
- 不要装 requirements 之外的任何包
- 不要 `pip freeze > requirements.txt`（会引入大量传递依赖污染）
- 不要 `--no-verify` 任何 git 操作

---

## 1. 现状（背景作者已验证）

### 1.1 .venv 实际缺失情况
```bash
# 验证命令
.venv/bin/python3 -c "import huey"          # ModuleNotFoundError
.venv/bin/python3 -c "import numpy"          # ModuleNotFoundError
.venv/bin/python3 -c "import jsonschema"     # ModuleNotFoundError
.venv/bin/python3 -c "import fastapi"        # ModuleNotFoundError
```
**4 个核心依赖缺失**。

### 1.2 requirements 文件现状
- `requirements.txt`：声明了 `fastapi>=0.115`、`jsonschema>=4.20`、`pydantic>=2.5` 等。**缺**：`huey`、`numpy`
- `requirements-dev.txt`：dev 依赖
- `pyproject.toml`：已有 `[project.optional-dependencies] dev`

### 1.3 collection error 现状
17 个 unit test 文件 collection error，分布：
- `tests/unit/backend-core/test_spec_c_018.py`、`019.py`、`020.py` → 缺 numpy
- `tests/unit/contracts/test_*.py`（多个）→ 缺 jsonschema
- `tests/unit/infra/test_spec_b_009.py` → 缺 fastapi
- `tests/unit/reviewers/test_music_fit_reviewer_v317.py`、`test_sfx_mix_reviewer.py` → 大概率缺 numpy
- `tests/unit/services/test_sfx_segment_mix_service.py` → 大概率缺 numpy

### 1.4 huey 用途证据
- `src/backend/workers/huey_config.py:48` `from huey import SqliteHuey`
- SPEC-B SPEC-10 异步任务队列的契约依赖
- huey 当前版本未 pin（推荐 `>=2.5` 以支持 immediate 模式参数；若使用更老版本 G-000b 实施会出错）

---

## 2. 实施步骤（顺序执行）

### Step 1：盘点当前已装
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System
.venv/bin/pip list 2>&1 | tee /tmp/venv-before.txt
```
存档供 commit body 引用。**若此命令失败**，stop，向许阳反馈"pip 本身坏掉"。

---

### Step 2：补 requirements.txt + requirements-dev.txt

**编辑 `requirements.txt`**：
- 在已有 `# Production deps` 段加：
  ```
  huey>=2.5
  numpy>=1.26
  ```
- 位置建议：放在 `pydantic>=2.5` 同段，按字母序

**编辑 `requirements-dev.txt`**：通常不需要改（huey/numpy 是 production 依赖）

**编辑 `pyproject.toml`**：检查是否需要在 `[project] dependencies` 数组里增加（**仅当**该数组已显式列出 production 依赖；若它指向 requirements.txt，则不改）。

**禁止**：
- 不要把 `>=2.5` 改成 `==2.5`（pin 应保持现状）
- 不要为了"以防万一"装额外包

---

### Step 3：执行安装
```bash
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt 2>&1 | tee /tmp/venv-install.log
```
**逐行检查输出**：
- 每个 missing 包应有 `Successfully installed ...` 行
- 任何 `ERROR` 或 `Could not find a version` → stop，反馈

---

### Step 4：单点 import 验证
```bash
.venv/bin/python3 -c "import huey; print('huey:', huey.__version__)"
.venv/bin/python3 -c "import numpy; print('numpy:', numpy.__version__)"
.venv/bin/python3 -c "import jsonschema; print('jsonschema:', jsonschema.__version__)"
.venv/bin/python3 -c "import fastapi; print('fastapi:', fastapi.__version__)"
.venv/bin/python3 -c "from huey import SqliteHuey; h = SqliteHuey('test', filename='/tmp/test_h.db', immediate=True); print('immediate=', h.immediate); import os; os.remove('/tmp/test_h.db')"
```

**全部成功**才能进 Step 5。`SqliteHuey(immediate=True)` 必须无报错——这是 G-000b 的硬性前提验证。

---

### Step 5：跑全量 baseline（不带 --ignore）
```bash
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no 2>&1 | tee /tmp/baseline-after-venv-fix.txt | tail -5
```

**期望**：
- collection error: **0**
- collected items: ~1700+（比修前的部分版本 1463 多）
- 失败数：≤ 23 + 17 个新 collected 文件中的失败数（这些新失败属于"原本就红、被 collection error 遮蔽"）

**若 collection error > 0**：去 `/tmp/baseline-after-venv-fix.txt` 看具体错误，返回 Step 2 检查 requirements 是否还有遗漏。

---

### Step 6：把数字写入 PROGRESS 与（可选）freeze 文档
- PROGRESS.md "Open follow-ups" 加一条：`Venv baseline restored on YYYY-MM-DD: X passed / Y failed / Z skipped (was 1463/23/2 with --ignore)`
- 这一步**不**写 `docs/SPEC-D-FREEZE-2026-04-25.md`——那是另一个交接的活（`SPEC-D-FREEZE-HANDOFF.md`）

---

### Step 7：Commit on main
```bash
git status --short
# 期望：
#   M requirements.txt
#   M requirements-dev.txt        # 仅当确实改了
#   M pyproject.toml               # 仅当确实改了
#   M PROGRESS.md
git add requirements.txt requirements-dev.txt pyproject.toml PROGRESS.md
# 仅 add 实际改的文件
git commit -m "$(cat <<'EOF'
[INFRA] add huey + numpy to requirements; restore .venv baseline

Files Changed:
- requirements.txt (added huey>=2.5, numpy>=1.26)
- (其他实际改动)

Verification:
- .venv/bin/pip install -r requirements.txt -r requirements-dev.txt → success
- python -c "import huey, numpy, jsonschema, fastapi" → all success
- SqliteHuey(immediate=True) → confirmed huey >= 2.5 supports immediate mode
- pytest tests/unit/ -q --tb=no → <填入 X passed / Y failed / Z skipped>
- collection errors: <填入数字, 期望 0>

Decisions:
- huey pinned at >=2.5 because G-000b requires SqliteHuey(immediate=True) parameter
  which was added in huey 2.5
- numpy pinned at >=1.26 to align with SPEC-C-018/019/020 audio-processing tests'
  numpy.fft / numpy.ndarray usage
- Did NOT upgrade pip / setuptools (risks reproducibility)
- Did NOT touch pyproject.toml [project] dependencies array if it delegates to
  requirements.txt (避免双源)

Artifacts:
- /tmp/venv-before.txt   (pre-install pip list snapshot)
- /tmp/venv-install.log  (pip install output)
- /tmp/baseline-after-venv-fix.txt (full baseline)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## 3. Acceptance Criteria
- [ ] AC-1: `.venv/bin/python3 -c "import huey; import numpy; import jsonschema; import fastapi"` 0 错
- [ ] AC-2: `SqliteHuey(immediate=True)` 可实例化（huey 版本 ≥ 2.5）
- [ ] AC-3: `pytest tests/unit/ -q --tb=no` 0 个 collection error
- [ ] AC-4: 全量 collected 数 > 部分版本 1463（应 ~1700+）
- [ ] AC-5: 全量 PASS 数 ≥ 部分版本 1463（不可降——任何 23+17 之外的新红立即调查）
- [ ] AC-6: requirements.txt 仅新增 huey + numpy 两行，不删/改其他行
- [ ] AC-7: 单 commit 完成，prefix `[INFRA]`，body 含真实数字

---

## 4. 异常路径

| 情况 | 实施 AI 应做 |
|------|------------|
| pip install 失败（如 numpy wheel 编译） | 反馈许阳，可能需要本地 toolchain（gcc 等） |
| huey 安装但 `SqliteHuey(immediate=True)` 报错 | 检查实际 huey 版本，**不要**降版要求；改 `>=2.5,<3` 锁定大版本 |
| 装完 huey/numpy 后仍有 collection error | 看具体错误的 ImportError 模块名，加到 requirements；commit body 详细说明每个新增包的来源依据（哪个 test 文件 import 了它） |
| pytest 全量跑出 ≥ 30 个新 FAILED（远超预期） | stop，**不要 commit**，反馈许阳——可能装包引入了行为变化（如 pydantic 版本漂移），需独立调查 |
| 跑出 collection error 但是不在原 17 个文件里 | 同上，反馈许阳 |
| pip 提示需要 sudo 或权限错误 | stop，反馈，**不要** sudo |

---

## 5. 完成判据（整张交接的）

- [ ] AC-1..AC-7 全过
- [ ] 1 个 commit 已合入 main，SHA 记录
- [ ] PROGRESS.md "Open follow-ups" 有 baseline 数字记录
- [ ] 实施 AI 在交接结束时给许阳：
  - commit SHA
  - 全量 baseline 三元组：`X passed / Y failed / Z skipped`
  - 一行结论：`venv 已修复，新 baseline = ...，可以启动 G-000-pre 与历史失败修复并行`

---

## 6. 与下游任务的协同

```
本交接（venv-fix）
   │
   ├─→ 取得干净 baseline 数字
   │      │
   │      └─→ 写入 docs/SPEC-D-FREEZE-2026-04-25.md
   │            （由 SPEC-D-FREEZE-HANDOFF.md 单独交接执行）
   │
   ├─→ 解锁 SPEC-G-000-pre / a / b / c / d / e
   │      （huey 可 import；G-000b 才能写 immediate 模式 fixture）
   │
   └─→ 解锁 HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF
          （干净 baseline 后才能判断每个 cluster 修复是否引入回归）
```

---

*文档版本：v1.0*
*创建：2026-04-25*
*关联文档：`tasks/SPEC-G/G-000-DECOMPOSITION-HANDOFF.md`、`tasks/HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF.md`、`tasks/SPEC-D-FREEZE-HANDOFF.md`*
