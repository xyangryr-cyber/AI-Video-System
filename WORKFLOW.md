# AI-Video-System 开发闭环使用手册

> 目的：把 **开发 → 测试 → 修复 → 本地门禁 → CI → 提交 → PR → 合并** 串成一条可重复执行的流水线。
> 适用对象：你（项目维护者）+ Claude Code 会话。
> 与 HARNESS / CLAUDE.md 的关系：**HARNESS 定纪律，CLAUDE 定地图，本文档定操作**。三者不冲突。

---

## 1. 组件全景（一张表看完）

| # | 组件 | 职责 | 触发方式 | 当前状态 |
|---|---|---|---|---|
| 1 | **SPEC-KIT**（14 个 `/speckit-*` skill） | 新功能流程：specify→plan→tasks→implement | **你手动**输入 `/speckit-xxx` | ✅ 已装 |
| 2 | **Bug-fix 4 skill**（自建） | Bug 流程：report→analyze→fix→verify | `/fix-report` 等 | ⏳ 待建 |
| 3 | **PostToolUse hook（自动测试-修复循环）** | 我每次改代码后自动跑相关测试，失败我自动修 | Edit/Write 工具触发 | ⏳ 待配 |
| 4 | **`/done` slash command（自建）** | 完成一个 task 时自动：verify→质量门禁→commit→（必要时）开 PR | **你手动**输入 `/done SPEC-X-NNN "subject"` | ⏳ 待建 |
| 5 | **pre-commit framework**（含架构/覆盖率门禁） | 本地提交门禁：lint/type/madge/coverage/unit | `git commit` 时自动 | ⏳ 待装 |
| 6 | **GitHub Actions（分层 CI + flaky 检测）** | 远程门禁：fast 层 + slow 层（含同测试跑 3 次） | `git push` / PR 时 | ⚠️ 已有但未分层 |
| 7 | **commit-task.sh** | 提交 + PROGRESS.md SHA 反填 | 由 `/done` 自动调用 | ✅ 已有 |
| 8 | **ship.sh**（自建） | 开 PR + 等 CI + 合并提示 | 由 `/done` 在最后一个 task 完成时自动调用 | ⏳ 待建 |
| 9 | **GitHub Branch Protection + auto-merge** | 强制 CI 全绿才能合 | GitHub web 配置 | ⏳ 待配 |
| 10 | **superpowers:using-git-worktrees** | 多任务并行加速 | 按需 `/superpowers-using-git-worktrees` | ✅ 已装（按需启用） |

> 图例：✅ 可立即用 / ⏳ 待落地 / ⚠️ 部分可用
> **角色分工**：组件 1/4/10 你主动触发；2/3/5/6/7/8/9 自动触发或被动响应。

---

## 2. 日常使用：6 个典型场景

### 场景 A — 开发一个新功能（你主导，AI 在最后一公里接管）

```
阶段 1：规划（你手动驱动 SPEC-KIT，按需调用）
  /speckit-specify "X 功能..."     ← 生成 specs/<NNN>-<slug>/spec.md（自动建 git 分支）
  /speckit-clarify                 ← 可选：5 个澄清问题，单人项目可跳过
  /speckit-plan                    ← 生成 plan.md
  /speckit-tasks                   ← 生成 tasks.md（T001/T002...）
  /speckit-analyze                 ← 必跑，跨文档一致性扫描

阶段 2：开发（你 + 我协作，PostToolUse hook 自动跑测试）
  - 你写代码 / 让我写代码
  - 每次 Edit/Write 触发 → PostToolUse hook 自动跑相关测试
  - 测试失败 → 我下一轮看到失败，自动用 TDD + systematic-debugging 修
  - 连续修 3 次还红 → hook 输出 "STOP: human intervention needed"，我停下问你
  - 直到全绿（你不需要等待，看到 hook 输出就知道状态）

阶段 3：完成（你打一行命令，AI 全自动接管最后一公里）
  /done SPEC-X-NNN "implement project service"
  
  ↓ /done 自动链:
    ① 跑 task card 的 verification_commands         ← 失败 → 停，输出报告
    ② 跑质量门禁：madge 架构循环 + coverage 阈值     ← 失败 → 停，输出报告
    ③ 全过 → commit-task.sh（提交 + 反填 PROGRESS）
    ④ 检查 tasks.md：该 SPEC 还有 [ ] 未完成？
        - 是 → 提示"还剩 N 个任务"，结束
        - 否 → 自动调 ship.sh（push + 开 PR + 等 CI + 提示合并）
```

**为什么这样设计**：
- 你的反馈：开发完容易忘记 commit + PR → `/done` 是单一触发器，避免遗忘
- 你不主导 SPEC-KIT 流程时（比如只是改个小 bug），不用走 `/speckit-*`，直接进阶段 2/3

### 场景 B — 修一个 bug（待建 skill 到位后）

```
你 → Claude Code 会话:
  "P3 阶段视频渲染失败，错误日志：..."

Claude:
  /fix-report           ← 写最小复现步骤 + 失败测试（RED）
  /fix-analyze          ← 调 superpowers:systematic-debugging，4 阶段定位根因
  /fix-implement        ← TDD 修复（GREEN → REFACTOR）
  /fix-verify           ← 跑 verification → commit-task.sh

无需走完整 SPEC-KIT 5 步。这是为"非新功能"准备的轻量流程。
```

**在 4 个 skill 落地前，bug-fix 走"自由对话 + 手动 TDD"模式。**

### 场景 C — 日常 commit

**永远走 `commit-task.sh`，不要直接 `git commit`**：

```bash
# 1. 你已经 git add 了要提交的文件
git add src/backend/services/foo.py tests/unit/test_foo.py

# 2. 调 commit-task.sh（两参数：task_id + 主题）
./commit-task.sh SPEC-C-012 "implement ProjectService.create()"

# 它会做两件事：
#   ① 用 [SPEC-C-012] 前缀提交
#   ② 找 PROGRESS.md 里 ## [SPEC-C-012] 段，把 "Commit: pending" 替换为短 SHA
#   ③ 再创建一个反填 commit
```

**前提**：跑 commit 前你必须已经手动跑过 task card 的 `verification_commands` 并通过——HARNESS §4.4 要求。

### 场景 D — 开 PR 并合并（待 ship.sh 落地后）

```bash
# 在 feature 分支上，确认本地全绿后：
./scripts/ship.sh

# ship.sh 会做：
#   ① 检查未提交改动 → 阻断
#   ② git push -u origin <branch>
#   ③ gh pr create --fill（PR body 从 commit messages 自动生成）
#   ④ gh pr checks --watch（阻塞等 CI）
#   ⑤ CI 红 → 拉失败日志，提示你回 Claude Code 修
#   ⑥ CI 绿 → 提示 "PR ready, please merge via GitHub web"
#      （不自动 merge，按 AGENTS.md §决策权限矩阵 是红灯操作，需人工）
```

**配合 GitHub auto-merge**：在 PR 上点一次 "Enable auto-merge"，CI 绿后 GitHub 自动合，无需守着。

### 场景 E — 同时推 2 个 SPEC（并行）

```
你 → Claude Code:
  "同时推进 SPEC-D 和 SPEC-E"

Claude:
  /superpowers-using-git-worktrees      ← 在 ../<repo>-spec-d / ../<repo>-spec-e 各建一个 worktree
  在每个 worktree 各起一个 subagent，互不干扰
  完成后分别 commit + ship
```

**触发条件**：只有 2+ 个 SPEC 真的可以独立推进时才用。单 SPEC 不要开。

### 场景 F — AI 自动测试-修复循环（PostToolUse hook 落地后）

**这是你 Q4 要的能力。不需要你做任何操作，自动发生。**

机制：
```
我（或你）改了 src/backend/services/foo.py
  ↓ PostToolUse hook 触发（监听 Edit/Write 工具）
  ↓ 推断关联测试：tests/unit/services/test_foo.py
  ↓ 跑 pytest tests/unit/services/test_foo.py -x --tb=short
  ↓
  ├─ 全绿 → 静默继续，loop_count 清零
  └─ 红 → 失败信息打到 stdout
       ↓ 我下一轮回话自动看到失败
       ↓ 我用 superpowers:test-driven-development + systematic-debugging 修
       ↓ 修完 → 又触发 hook → 再跑 → ...
       
失控保护:
  - .claude/loop_count 文件累计连续失败次数
  - 第 3 次还红 → hook 输出加 "STOP: 3 consecutive failures, human intervention needed"
  - 我看到 STOP 信号会主动停下，告诉你"我修不动了，原因是..."
```

**不能完全自动的两类**（必须你介入）：
1. **测试本身写错**（弱测试通过但代码其实坏） → 在 ship 前用 reviewer subagent 审一次
2. **需要架构变更的 bug** → 我发现 fix 越改越复杂时会停下问你

**你的角色**：
- 平时：观察 hook 输出，看到红又绿是正常的
- STOP 信号出现：介入决策
- 重要 PR 前：手动跑一次 reviewer 看测试质量

---

## 3. 首次落地清单（按依赖顺序）

> 全部完成约 **半天工作量**。可以一次做完，也可以按需要分批。
> 每步落地后这份文档对应组件的"状态"列改成 ✅。

### Step 1️⃣ — pre-commit（含架构 + 覆盖率门禁，45 分钟）

```bash
# 1. 安装
pip install pre-commit pytest-cov
npm install -g madge   # 架构依赖循环检查

# 2. 在仓库根写 .pre-commit-config.yaml
cat > .pre-commit-config.yaml <<'YAML'
repos:
  # ── 代码风格 ──
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # ── Python 类型 ──
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        files: ^src/backend/
        additional_dependencies: [pydantic, fastapi, sqlalchemy]

  # ── 本地钩子 ──
  - repo: local
    hooks:
      - id: tsc
        name: TypeScript type check
        entry: pnpm --filter frontend exec tsc --noEmit
        language: system
        files: ^src/frontend/.*\.(ts|tsx)$
        pass_filenames: false

      # ★ 新增：架构依赖循环检查（HARNESS §10.2）
      - id: madge-backend
        name: Madge circular dependency (backend)
        entry: madge --circular src/backend
        language: system
        files: ^src/backend/.*\.py$
        pass_filenames: false
      - id: madge-frontend
        name: Madge circular dependency (frontend)
        entry: madge --circular --extensions ts,tsx src/frontend
        language: system
        files: ^src/frontend/.*\.(ts|tsx)$
        pass_filenames: false

      # ★ 新增：单测 + 覆盖率门禁
      - id: pytest-unit
        name: Pytest unit + coverage (>=80%)
        entry: pytest tests/unit -x --tb=short --cov=src/backend --cov-fail-under=80
        language: system
        files: ^(src/backend/|tests/unit/).*\.py$
        pass_filenames: false
      - id: vitest-unit
        name: Vitest + coverage (>=70%)
        entry: pnpm --filter frontend exec vitest run --coverage --coverage.thresholds.lines=70
        language: system
        files: ^src/frontend/.*\.(ts|tsx)$
        pass_filenames: false
YAML

# 3. 启用
pre-commit install

# 4. 验证（4 个测试场景）
# ① lint 错
echo "import nonexistent" >> src/backend/services/foo.py
git add . && git commit -m "test"   # 应被 ruff 拦
git restore --staged --worktree .

# ② 架构循环（手动制造一个 import 循环）
# ③ 覆盖率不足（删掉一个测试看是否 80% 触发）
# ④ TS 类型错（改 .tsx 加 const x: number = "string"）
```

**对应 HARNESS §10.1 + §10.2** —— 把那两节列的命令全部落地成自动门禁。
**性能注意**：pytest 覆盖率会比纯单测慢 2-3 倍。如果太慢，把 coverage 移到 CI fast 层，pre-commit 只跑纯单测。

### Step 2️⃣ — Claude Code Hook：自动测试-修复循环（30 分钟）

**这是实现"AI 自动测试-修复循环"的核心**。配置项目级 hook（`.claude/settings.json`），不污染全局。

```bash
# 1. 写一个智能测试 runner（按改动文件推断要跑哪些测试）
mkdir -p .claude/hooks
cat > .claude/hooks/run_related_tests.sh <<'BASH'
#!/usr/bin/env bash
# 输入：$CLAUDE_FILE_PATH（被编辑的文件绝对路径）
# 行为：推断关联测试 → 跑 → 失败计数累加 → 超阈值输出 STOP
set -uo pipefail

REPO_ROOT="/Users/xyangryr/Desktop/硅基员工/AI-Video-System"
COUNT_FILE="$REPO_ROOT/.claude/loop_count"
MAX_LOOPS=3
FILE="${CLAUDE_FILE_PATH:-}"

[ -z "$FILE" ] && exit 0
cd "$REPO_ROOT" || exit 0

# 推断测试路径
if [[ "$FILE" == *src/backend/*.py ]]; then
  REL="${FILE#*src/backend/}"
  TEST="tests/unit/${REL%.py}.py"
  TEST_ALT="tests/unit/$(dirname "$REL")/test_$(basename "$REL")"
  for t in "$TEST" "$TEST_ALT"; do
    [ -f "$t" ] && CMD="pytest $t -x --tb=short" && break
  done
elif [[ "$FILE" == *src/frontend/*.tsx || "$FILE" == *src/frontend/*.ts ]]; then
  REL="${FILE#*src/frontend/}"
  TEST="src/frontend/${REL%.*}.test.${REL##*.}"
  [ -f "$TEST" ] && CMD="pnpm --filter frontend exec vitest run $TEST"
elif [[ "$FILE" == *tests/*.py ]]; then
  CMD="pytest $FILE -x --tb=short"
fi

[ -z "${CMD:-}" ] && exit 0

# 跑测试
OUTPUT=$(eval "$CMD" 2>&1)
RC=$?

if [ $RC -eq 0 ]; then
  echo "0" > "$COUNT_FILE"
  echo "✓ Tests passed: $CMD"
else
  COUNT=$(cat "$COUNT_FILE" 2>/dev/null || echo 0)
  COUNT=$((COUNT + 1))
  echo "$COUNT" > "$COUNT_FILE"
  echo "✗ Tests failed (consecutive failures: $COUNT/$MAX_LOOPS)"
  echo "$OUTPUT" | tail -40
  if [ "$COUNT" -ge "$MAX_LOOPS" ]; then
    echo ""
    echo "STOP: $MAX_LOOPS consecutive failures, human intervention needed."
    echo "Suggest: review test correctness, check for architectural issue, or revert."
  fi
fi
exit 0
BASH
chmod +x .claude/hooks/run_related_tests.sh

# 2. 配置 .claude/settings.json
cat > .claude/settings.json <<'JSON'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/xyangryr/Desktop/硅基员工/AI-Video-System/.claude/hooks/run_related_tests.sh"
          }
        ]
      }
    ]
  }
}
JSON
```

**重启 Claude Code 会话生效**。

**验证**：
- 让我编辑一个 .py 文件 → 应看到 hook 输出 "✓ Tests passed" 或 "✗ Tests failed"
- 故意让我改坏一个函数 → 看到 ✗，我会自动尝试修
- 改坏 3 次 → 看到 STOP 信号，我会主动停下问你

**为什么用 PostToolUse 而不是 Stop**：
- Stop hook 每次回完话都跑，纯调研对话也跑很烦
- PostToolUse + Edit/Write matcher 只在改了代码时才跑
- 而且按文件路径推断关联测试，比跑全量快 10-50 倍

### Step 3️⃣ — Bug-fix 4 个 skill（半天）

在 `.claude/skills/` 下新建 4 个目录，每个含一个 `SKILL.md`：

```
.claude/skills/
├── fix-report/SKILL.md       ← 复现 + 写最小失败测试（RED）
├── fix-analyze/SKILL.md      ← 调 systematic-debugging 定位根因
├── fix-implement/SKILL.md    ← TDD 修复（GREEN→REFACTOR）
└── fix-verify/SKILL.md       ← 跑 verification + commit-task.sh
```

**模板**（以 `fix-report/SKILL.md` 为例）：

```markdown
---
name: fix-report
description: Use when starting a bug fix. Reproduces the bug and writes a minimal failing test (RED).
user-invocable: true
---

## Goal
Establish a deterministic, minimal reproduction. Output a failing test that captures the bug.

## Steps
1. Read the user's bug report. Extract: symptom, environment, expected vs actual.
2. Find the smallest input that triggers the bug. Strip everything else.
3. Write ONE test in tests/unit/<module>/ that fails for the right reason.
4. Run it. Confirm RED.
5. Output: test file path + failure message + next-skill suggestion (/fix-analyze).

## Constraints
- Do NOT write any production code in this step.
- Do NOT fix the bug. Only capture it.
- Test must be independent (no shared state with other tests).

## Done definition
- One new test file under tests/unit/.
- pytest reports it as FAILED with the expected error.
```

其余 3 个 skill 套这个结构填内容（analyze 调 systematic-debugging；implement 走 TDD 红绿；verify 调 commit-task.sh）。

### Step 4️⃣ — 分层 CI（含 flaky 检测，1.5 小时）

把现有 `.github/workflows/ci.yml` 拆成两层：

```yaml
# .github/workflows/ci.yml
name: ci
on:
  pull_request:
  push: { branches: [main] }

jobs:
  fast:                          # 应该 < 2 分钟，秒级反馈
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt jsonschema
      - name: Lint
        run: ruff check src/backend/
      - name: Architecture (no circular deps)
        run: |
          npm install -g madge
          madge --circular src/backend
          madge --circular --extensions ts,tsx src/frontend
      - name: Unit + coverage
        run: pytest tests/unit/ tests/contract/ -x --cov=src/backend --cov-fail-under=80

  slow:                          # 5-10 分钟，含 flaky 检测
    needs: fast                  # fast 没过就别跑 slow
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start services
        run: docker compose -f docker-compose.dev.yml up -d
      - name: Integration (run 3x to detect flaky)   # ★ 新增 flaky 检测
        run: |
          pip install pytest-repeat
          pytest tests/integration/ --count=3 --tb=short
      - name: Smoke
        run: curl -sf http://localhost:3000/api/projects | python3 -c "import json,sys; json.load(sys.stdin)"
      - if: always()
        run: docker compose -f docker-compose.dev.yml down

  # 可选第三层：mutation testing（每周 nightly 跑，不在 PR 上跑）
  # 已经存在 .github/workflows/eval_regression.yml，按相同模式新增 mutation.yml 即可
```

**好处**：
- lint/架构/unit 错的 PR 在 2 分钟内显红，不用等 10 分钟
- `needs: fast` 让快层失败时整个 slow 层不跑，省 CI 时间
- `pytest-repeat --count=3` 同测试跑 3 次，全过才算（flaky 检测，HARNESS §10.2 要求的延伸）

**测试质量审查**（"Would a stub pass this test?"，HARNESS §4.2）：放到 `ship.sh` 里调一次 reviewer subagent，约 $0.05/PR。不在 CI 里自动跑因为成本不可控。

### Step 5️⃣ — ship.sh（2 小时）

```bash
# scripts/ship.sh
#!/usr/bin/env bash
set -euo pipefail

# 0. 前置检查
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "错误：有未提交的改动。先跑 commit-task.sh。" >&2
  exit 1
fi
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" == "main" ]]; then
  echo "错误：不能在 main 上 ship。" >&2
  exit 1
fi

# 1. push
git push -u origin "$BRANCH"

# 2. 开 PR（从 commits 自动生成 body）
PR_URL=$(gh pr create --fill --base main --head "$BRANCH" 2>&1 | tail -1)
echo "PR opened: $PR_URL"

# 3. 等 CI
echo "等待 CI..."
if gh pr checks "$PR_URL" --watch --fail-fast; then
  echo "✅ CI 全绿。"
  echo "下一步：到 GitHub web 上点 Merge（或开启 auto-merge）。"
  echo "PR: $PR_URL"
else
  echo "❌ CI 红。"
  echo "拉失败日志：gh run view --log-failed"
  echo "回 Claude Code 修复后重新提交，PR 会自动重跑。"
  exit 1
fi
```

`chmod +x scripts/ship.sh` 后即可用。

### Step 6️⃣ — `/done` slash command（解决"经常忘记 commit/PR"问题，1 小时）

**这是核心新增**——你完成一个 task 时打一行命令，后面全自动。

```bash
mkdir -p .claude/skills/done
cat > .claude/skills/done/SKILL.md <<'MD'
---
name: done
description: Use when a task implementation is complete. Runs verification, quality gates, commits, and opens PR if this is the last task in the SPEC.
user-invocable: true
argument-hint: "<task_id> \"<imperative subject>\""
---

## Goal
Single-command "finish this task" trigger. Replaces the easy-to-forget manual chain of verify → commit → PR.

## Steps

1. **Parse arguments**: `$ARGUMENTS` should be `SPEC-X-NNN "subject"`. If missing, ask once.

2. **Locate task card**: Read `tasks/SPEC-X/<NNN>-*.md`. Extract `verification_commands` and `allowed_files`.

3. **Run verification** (sequential, halt on first failure):
   ```bash
   for cmd in <verification_commands>; do
     bash -c "$cmd" || { echo "FAILED: $cmd"; exit 1; }
   done
   ```
   On failure → output the failing command + last 30 lines of output → STOP. Do NOT commit.

4. **Run quality gates** (additional to pre-commit, in case of bypass):
   ```bash
   madge --circular src/backend src/frontend
   pytest --cov=src/backend --cov-fail-under=80 -q
   ```
   On failure → STOP.

5. **Verify staged files match `allowed_files`**:
   - `git diff --cached --name-only` ⊆ task card's `allowed_files`?
   - If extra files staged → STOP, ask user to confirm scope.

6. **Commit**: `bash commit-task.sh "<task_id>" "<subject>"`

7. **Check completion of SPEC**:
   - Read `tasks/SPEC-X/` task cards, count remaining `status: pending|in_progress`.
   - If > 0 → output "Remaining tasks in SPEC-X: N. Run /done again when next task completes." → STOP.
   - If = 0 → proceed to step 8.

8. **Auto-ship**: `bash scripts/ship.sh`
   - Pushes branch, opens PR, watches CI.
   - On CI green → outputs PR URL with merge instruction.
   - On CI red → outputs failed log + suggests next debugging step (do NOT auto-fix on main path).

## Constraints
- NEVER commit if verification fails.
- NEVER open PR if there are uncommitted changes after step 6.
- NEVER merge automatically (red light per AGENTS.md decision matrix).
- If `loop_count >= 3` from PostToolUse hook → STOP step 3, advise human review.

## Reset on success
After successful commit, reset `.claude/loop_count` to 0.
MD
```

**使用**：
```
你 → Claude Code:
  /done SPEC-C-012 "implement ProjectService.create()"
  
我 → 自动跑 verify → 质量门禁 → commit → 检查 SPEC 是否完成 → 必要时开 PR
```

**为什么这是核心**：你说会忘记 commit + PR——`/done` 把易忘的多步操作压成一行。

---

### Step 7️⃣ — GitHub Branch Protection（5 分钟，web 操作）

GitHub 仓库 → Settings → Branches → Add branch protection rule:

- **Branch name pattern**: `main`
- ☑ Require a pull request before merging
- ☑ Require status checks to pass before merging
  - 选 `fast` 和 `slow`（Step 4 拆出来的两个 job）
- ☑ Require branches to be up to date before merging
- ☑ Allow auto-merge

**之后**：开了 PR → 点一次 "Enable auto-merge (squash)" → CI 绿后 GitHub 自动合。

---

## 4. 每天最常用的 2 条命令

```
1. 在 Claude Code 里启动新功能（你主动）
   /speckit-specify "<需求>"
   ... /speckit-plan / /speckit-tasks / /speckit-analyze ...

2. 完成一个 task card（你主动，AI 接管后续全部）
   /done SPEC-X-NNN "<imperative subject>"
```

**就这两条**。其他全部自动：
- `commit-task.sh` 由 `/done` 自动调
- `ship.sh` 由 `/done` 在最后一个 task 完成时自动调
- pre-commit 在 `git commit` 时自动跑（被 commit-task.sh 触发）
- PostToolUse hook 在每次 Edit/Write 时自动跑测试
- CI 在 `git push` / 开 PR 时自动跑
- auto-merge 在 CI 全绿时由 GitHub 自动合（如开了 Branch Protection）

---

## 5. 故障排查

| 症状 | 可能原因 | 处理 |
|---|---|---|
| `pre-commit` 跑得慢 | mypy / pytest 把全量跑了 | 检查 `files:` 正则是否正确锁定到改动文件 |
| Claude Code Stop hook 不触发 | settings.json 路径错 | 全局放 `~/.claude/settings.json`，项目级放 `<repo>/.claude/settings.json` |
| `commit-task.sh` 报 "no PROGRESS entry" | task_id 拼错 / PROGRESS 段还没建 | 先在 PROGRESS.md 加 `## [SPEC-X-NNN]` 段（含 `- **Commit**: pending`） |
| `ship.sh` 卡在 `gh pr checks --watch` | CI 在跑 | 正常，等就行；如果想后台跑用 `&` |
| CI fast 层过了 slow 层失败 | integration / docker 问题 | `gh run view --log-failed` 看具体错；本地 `docker compose up -d` 复现 |
| `/speckit-implement` 没跑测试 | tasks.md 里没列 test 任务 | 先 `/speckit-tasks` 时声明 "TDD approach"；或手动在 tasks.md 加 test 任务 |
| auto-merge 没合 | branch protection 没开 / PR 有 conflict | Settings → Branches 检查；本地 rebase main 解 conflict |

---

## 6. 与既有规则的关系

- **HARNESS.md** 是宪法（目录权限、TDD 强制、PROGRESS 格式等）。本流程**遵守它**，不替代它。
- **CLAUDE.md** 是地图（去哪找文件、SPEC 依赖顺序）。本流程**用它导航**。
- **AGENTS.md §决策权限矩阵** 决定我什么时候自己做、什么时候停下问。本流程**符合矩阵**：
  - 🟢 PostToolUse hook 跑测试 / pre-commit / commit-task.sh / madge / coverage → AI 自动
  - 🟡 `/done` 触发的 ship.sh 开 PR → AI 自动（PR 可逆，不动 main）
  - 🟡 PostToolUse 检测到测试红，AI 自动 TDD 修复（最多 3 轮）→ AI 自动，超阈值停下问你
  - 🔴 在 GitHub web 上点 Merge → 永远人工，绝不自动
  - 🔴 修改 HARNESS.md / CLAUDE.md / AGENTS.md → 永远人工

---

## 7. 落地优先级（按你的核心诉求重排）

你的核心诉求：**(a) 完成时不忘 commit/PR  (b) 自动测试-修复循环  (c) 质量门禁**

| 优先级 | Step | 解决的诉求 | 成本 |
|---|---|---|---|
| 🔴 必做 | **Step 6 (`/done` skill)** | (a) 一行触发完整收尾链 | 1h |
| 🔴 必做 | **Step 2 (PostToolUse hook)** | (b) AI 自动测试-修复循环 + 失控保护 | 30min |
| 🔴 必做 | **Step 1 (pre-commit + madge + coverage)** | (c) 本地强制门禁 | 45min |
| 🔴 必做 | **Step 5 (ship.sh)** | `/done` 依赖它 | 2h |
| 🟡 强烈建议 | Step 4 (分层 CI + flaky 检测) | (c) 远程门禁 + 反馈提速 | 1h |
| 🟡 强烈建议 | Step 3 (bug-fix 4 skill) | 覆盖 50%+ 真实工作（bug 修复） | 半天 |
| 🟢 锦上添花 | Step 7 (Branch Protection) | 单人项目防御性，团队必须 | 5min |

**核心组合（必做 4 项）**：Step 1 + 2 + 5 + 6，**约 4.5 小时**，落地后就实现了你的全部 3 个核心诉求。
**完整体验**：全部 7 步，**约 1.5 个工作日**。

---

## 8. 触发我做下一步

读完后告诉我你想从哪一步开始：

- 想立刻见效 → "做 Step 1 + Step 4"
- 想要完整 bug 流程 → "做 Step 3"
- 想要全自动 → "全部按优先级落地"
- 想看某一步先看代码 → "把 Step N 的草稿写出来给我看"

我会按 AGENTS.md 自动驾驶模式执行（绿灯直接做、黄灯做完汇报、红灯停下问）。
