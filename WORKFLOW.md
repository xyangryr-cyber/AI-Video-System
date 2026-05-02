# AI-Video-System 开发闭环使用手册

> 目的：把 **开发 → 测试 → 修复 → 本地门禁 → CI → 提交 → PR → 合并** 串成一条可重复执行的流水线。
> 适用对象：你（项目维护者）+ Claude Code 会话。
> 与 HARNESS / CLAUDE.md 的关系：**HARNESS 定纪律，CLAUDE 定地图，本文档定操作**。三者不冲突。

---

## 1. 组件全景（一张表看完）

| # | 组件 | 职责 | 触发方式 | 当前状态 |
|---|---|---|---|---|
| 1 | **SPEC-KIT**（14 个 `/speckit-*` skill） | 新功能流程：specify→plan→tasks→implement | Claude Code 里输入 `/speckit-xxx` | ✅ 已装 |
| 2 | **Bug-fix 4 skill**（自建） | Bug 流程：report→analyze→fix→verify | `/fix-report` 等 | ⏳ 待建 |
| 3 | **Claude Code Stop hook** | 我每次回完话自动跑 unit test | `~/.claude/settings.json` | ⏳ 待配 |
| 4 | **pre-commit framework** | 本地提交门禁（lint/format/type/unit） | `git commit` 时自动 | ⏳ 待装 |
| 5 | **GitHub Actions（分层 CI）** | 远程门禁：fast 层 + slow 层 | `git push` / PR 时 | ⚠️ 已有但未分层 |
| 6 | **commit-task.sh** | 提交 + PROGRESS.md SHA 反填 | 手动调用 | ✅ 已有 |
| 7 | **ship.sh**（自建） | 开 PR + 等 CI + 合并提示 | 手动调用 | ⏳ 待建 |
| 8 | **GitHub Branch Protection + auto-merge** | 强制 CI 全绿才能合 | GitHub web 配置 | ⏳ 待配 |
| 9 | **superpowers:using-git-worktrees** | 多任务并行加速 | 按需 `/superpowers-using-git-worktrees` | ✅ 已装（按需启用） |

> 图例：✅ 可立即用 / ⏳ 待落地 / ⚠️ 部分可用

---

## 2. 日常使用：6 个典型场景

### 场景 A — 开发一个新功能

```
你 → Claude Code 会话:
  "我想做 X 功能，需求是 ..."

Claude → 自动按下面流程走（所有命令在 Claude Code 里输入）:
  /speckit-specify "X 功能..."          ← 生成 specs/<NNN>-<slug>/spec.md（自动建 git 分支）
  /speckit-clarify                      ← 5 个澄清问题，回灌 spec
  /speckit-plan                         ← 生成 plan.md（架构、技术选型）
  /speckit-tasks                        ← 生成 tasks.md（T001/T002...）
  /speckit-analyze                      ← 跨文档一致性扫描（必跑，是免费保险）
  /speckit-implement                    ← 按 tasks.md 顺序执行 TDD

每个任务完成 → 我自动调 commit-task.sh 提交 + 反填 PROGRESS.md。
全部任务完 → 你输入 "ship"，我调 ship.sh 开 PR。
```

**单人项目可以跳过 `/speckit-clarify`**，需求自己写清楚就行。

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

### 场景 F — 我不想守着等测试（Stop hook 落地后）

```
你不需要做什么。Claude Code 每次回完话都会自动跑 pytest tests/unit -x，
失败结果会回灌到下一轮对话里，我看到红了会自动尝试修。

你只要做：观察 → 在我修不动时介入。
```

---

## 3. 首次落地清单（按依赖顺序）

> 全部完成约 **半天工作量**。可以一次做完，也可以按需要分批。
> 每步落地后这份文档对应组件的"状态"列改成 ✅。

### Step 1️⃣ — pre-commit（30 分钟，零风险）

```bash
# 1. 安装
pip install pre-commit

# 2. 在仓库根写 .pre-commit-config.yaml
cat > .pre-commit-config.yaml <<'YAML'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        files: ^src/backend/
        additional_dependencies: [pydantic, fastapi, sqlalchemy]
  - repo: local
    hooks:
      - id: tsc
        name: TypeScript type check
        entry: pnpm --filter frontend exec tsc --noEmit
        language: system
        files: ^src/frontend/.*\.(ts|tsx)$
        pass_filenames: false
      - id: pytest-unit
        name: Pytest unit tests (fast)
        entry: pytest tests/unit -x --tb=short
        language: system
        files: ^(src/backend/|tests/unit/).*\.py$
        pass_filenames: false
YAML

# 3. 启用
pre-commit install

# 4. 验证：故意写个错的 import 试试
echo "import nonexistent_module" >> src/backend/services/foo.py
git add src/backend/services/foo.py
git commit -m "test pre-commit"   # 应该被拦下来
git restore --staged --worktree src/backend/services/foo.py
```

**对应 HARNESS §10.1**——把那一节列的命令落地成自动门禁。

### Step 2️⃣ — Claude Code Stop hook（10 分钟）

```bash
# 编辑 ~/.claude/settings.json（不是项目内的，是全局）
# 或者只对本项目：在项目根 .claude/settings.json
```

写入（如果文件已存在，合并 hooks 段）：

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && pytest tests/unit -x --tb=short 2>&1 | tail -50"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "if [[ \"$CLAUDE_FILE_PATH\" == *.py ]]; then ruff check --fix \"$CLAUDE_FILE_PATH\" 2>&1 | tail -5; fi"
          }
        ]
      }
    ]
  }
}
```

**重启 Claude Code 会话**生效。验证：让我编辑一个 .py 文件，看是否自动 ruff；让我说 "done"，看是否自动跑 pytest。

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

### Step 4️⃣ — 分层 CI（1 小时）

把现有 `.github/workflows/ci.yml` 拆成两个 job：

```yaml
# .github/workflows/ci.yml
name: ci
on:
  pull_request:
  push: { branches: [main] }

jobs:
  fast:                          # 应该 < 2 分钟
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt jsonschema
      - run: ruff check src/backend/
      - run: pytest tests/unit/ tests/contract/ -x

  slow:                          # 5-10 分钟
    needs: fast                  # fast 没过就别跑 slow，省 CI 配额
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f docker-compose.dev.yml up -d
      - run: pytest tests/integration/
      - run: curl -sf http://localhost:3000/api/projects | python3 -c "import json,sys; json.load(sys.stdin)"
      - if: always()
        run: docker compose -f docker-compose.dev.yml down
```

**好处**：lint/unit 错的 PR 在 2 分钟内显红，不用等 10 分钟。`needs: fast` 让快层失败时整个 slow 层不跑，省 CI 时间。

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

### Step 6️⃣ — GitHub Branch Protection（5 分钟，web 操作）

GitHub 仓库 → Settings → Branches → Add branch protection rule:

- **Branch name pattern**: `main`
- ☑ Require a pull request before merging
- ☑ Require status checks to pass before merging
  - 选 `fast` 和 `slow`（Step 4 拆出来的两个 job）
- ☑ Require branches to be up to date before merging
- ☑ Allow auto-merge

**之后**：开了 PR → 点一次 "Enable auto-merge (squash)" → CI 绿后 GitHub 自动合。

---

## 4. 每天最常用的 3 条命令

```bash
# 1. 完成一个 task card 后提交
./commit-task.sh SPEC-X-NNN "<imperative subject>"

# 2. 整个 feature 完成，开 PR
./scripts/ship.sh

# 3. 在 Claude Code 里启动新功能
/speckit-specify "<需求>"
```

其他都是被自动触发的（pre-commit / Stop hook / CI / auto-merge）。

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
  - 🟢 commit-task.sh / pre-commit / Stop hook → AI 自己跑
  - 🟡 ship.sh 开 PR → AI 跑（PR 是可逆的，不动 main）
  - 🔴 在 GitHub 上点 Merge → 永远人工，不自动

---

## 7. 落地优先级（如果只能做一部分）

| 优先级 | Step | 价值 | 成本 |
|---|---|---|---|
| 🔴 必做 | Step 1 (pre-commit) | 防止低级错误污染 git 历史 | 30min |
| 🔴 必做 | Step 4 (分层 CI) | CI 反馈从 10min 缩到 2min | 1h |
| 🟡 强烈建议 | Step 3 (bug-fix skills) | 覆盖 50%+ 真实工作（bug） | 半天 |
| 🟡 强烈建议 | Step 5 (ship.sh) | 省手动开 PR + 守 CI 的时间 | 2h |
| 🟢 锦上添花 | Step 2 (Stop hook) | 全自动测试反馈，体验提升 | 10min |
| 🟢 锦上添花 | Step 6 (Branch Protection) | 防御性，对单人项目意义不大 | 5min |

**最小可用集**：Step 1 + Step 4，**90 分钟搞定**，立刻见效。
**完整体验**：全部 6 步，**约 1 个工作日**。

---

## 8. 触发我做下一步

读完后告诉我你想从哪一步开始：

- 想立刻见效 → "做 Step 1 + Step 4"
- 想要完整 bug 流程 → "做 Step 3"
- 想要全自动 → "全部按优先级落地"
- 想看某一步先看代码 → "把 Step N 的草稿写出来给我看"

我会按 AGENTS.md 自动驾驶模式执行（绿灯直接做、黄灯做完汇报、红灯停下问）。
