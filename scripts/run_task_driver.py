#!/usr/bin/env python3
"""Mode B task driver: pick → dispatch `claude -p` → verify → fix → repeat.

Each iteration starts a fresh `claude -p` subprocess with AVS_CURRENT_TASK set,
so context never grows across tasks. Pairs with scripts/pick_next_task.py:
when that picker exits with an empty stdout, the loop ends.

Dev-test loop (enabled by default):
  1. dispatch — "developer" agent implements the task (TDD RED→GREEN).
  2. verify   — independent read-only "auditor" agent re-runs
                verification_commands, writes .verify/<task_id>.json.
  3. fix      — if verify fails, "fixer" agent reads the report and patches;
                loop back to step 2 up to --max-fix-rounds times.

Typical use:

    python3 scripts/run_task_driver.py --max-tasks 5

Disable the audit/fix loop (single-agent mode):

    python3 scripts/run_task_driver.py --max-tasks 5 --no-verify

Tests inject fake `pick_next` / `dispatch` / `verify` / `fix` callables via
`run_loop` so the core loop logic is unit-testable without invoking real
`claude` binaries.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Tuple, cast

DEFAULT_PROMPT_TEMPLATE = (
    "按 HARNESS 走 TDD 完成 {task_id}:\n"
    "- 读 tasks/SPEC-*/{task_id}*.md（task card），遵守 allowed_files / forbidden_files\n"
    "- 写 RED test，确认失败原因\n"
    "- GREEN 最小实现到测试通过\n"
    "- 跑 task card 中的 verification_commands\n"
    "- Append PROGRESS.md 一条 DONE（HARNESS §9.2 全部字段：\n"
    "  Status / Started / Completed / Files Changed / Verification /\n"
    "  Artifacts / Commit / Decisions / Notes；\n"
    "  **Decisions** 字段必填：一到三条 bullet，记录关键取舍与原因，\n"
    "  例如 \"选 Pydantic v2 而非 v1 因为 SPEC-B 已锁定\"）\n"
    "- 完成即结束，不要继续下一 task"
)

VERIFIER_PROMPT_TEMPLATE = (
    "独立审计 {task_id}（只读审查，你不是开发者而是审计者）：\n"
    "- 禁止修改除 .verify/{task_id}.json 之外的任何文件\n"
    "- 读 tasks/SPEC-*/{task_id}*.md 提取 verification_commands\n"
    "- 逐一执行每条命令，捕获 exit code 与关键输出尾部（最多 20 行）\n"
    "{bdd_block}"
    "- 读 PROGRESS.md 中 {task_id} 最新条目，检查 HARNESS §9.2 字段是否齐全\n"
    "  (Status / Started / Completed / Files Changed / Verification / Artifacts)\n"
    "- 写报告到 .verify/{task_id}.json，schema:\n"
    '  {"task_id": "{task_id}", "status": "pass" | "fail",\n'
    '    "verification_results": [\n'
    '      {"command": "...", "exit_code": N, "tail": "..."}],\n'
    '    "bdd_results": [\n'
    '      {"tag_expr": "...", "exit_code": N, "passed": N, "failed": N, "tail": "..."}],\n'
    '    "progress_check": "pass" | "fail",\n'
    '    "reasons": ["..."] }\n'
    "- 判定：所有 verification_command exit=0 且 BDD（如有） exit=0 且 progress_check=pass → status=pass\n"
    "- 任何一项不满足 → status=fail，reasons 写清具体原因（命令名 + 失败摘要）\n"
    "- 不要 append PROGRESS.md；不要 git commit；完成即结束"
)


def _build_bdd_block(bdd_tag_expr: str) -> str:
    """Return the BDD verification instruction lines, or empty string."""
    if not bdd_tag_expr:
        return ""
    return (
        f'- 额外执行 BDD：`pytest tests/integration/bdd/ -m "{bdd_tag_expr}" -v`\n'
        f'  捕获 exit code、通过/失败数、输出尾部 20 行；写入 bdd_results[0]\n'
    )

FIXER_PROMPT_TEMPLATE = (
    "修复 {task_id}：\n"
    "- 读 $AVS_FIX_REPORT（环境变量指向 .verify/{task_id}.json 或\n"
    "  .verify/{task_id}.review.json）获取失败详情\n"
    "- verify 报告含 reasons + verification_results；review 报告含 findings\n"
    "  （severity=P0 表示必须修复的代码质量问题）\n"
    "- 根据失败详情定位问题\n"
    "- TDD：若现有测试缺失/错误，先改测试到 RED（因正确原因失败），再改实现到 GREEN\n"
    "- 遵守 task card 的 allowed_files / forbidden_files\n"
    "- 重跑 verification_commands 本地确认通过\n"
    "- 如需更新 PROGRESS.md，append 新条目（不改旧条目）按 HARNESS §9.2，\n"
    "  必须含 Decisions 字段说明为何这样修\n"
    "- 完成即结束，不要继续下一 task"
)

REVIEWER_PROMPT_TEMPLATE = (
    "独立代码审查 {task_id}（只读审查，聚焦代码质量而非功能正确性）：\n"
    "- 禁止修改除 .verify/{task_id}.review.json 之外的任何文件\n"
    "- 读该 task 最新改动（git diff）+ PROGRESS.md 最新条目\n"
    "- 按 HARNESS 检查以下维度，给每条 finding 打 severity：\n"
    "  * P0（阻塞）：违反 HARNESS §2 依赖方向、§5 schema 边界、§11 安全；\n"
    "                函数/文件严重超出 §6 上限；无 TDD 迹象（没有测试）；\n"
    "                commit 缺 [SPEC-X-NNN] 前缀；使用 §7.2 禁用模式。\n"
    "  * P1（强烈建议）：文件>§6 上限 20%；单函数>50 行；测试覆盖薄弱；\n"
    "                    命名违反 §3；missing Decisions 字段。\n"
    "  * P2（可选）：注释、微小命名、格式细节。\n"
    "- 写报告到 .verify/{task_id}.review.json，schema:\n"
    '  {{"task_id": "{task_id}", "status": "pass" | "fail",\n'
    '    "findings": [{{"severity": "P0"|"P1"|"P2",\n'
    '                   "file": "path", "line": N, "message": "..."}}]}}\n'
    "- 判定：只要有一条 P0 → status=fail；否则 status=pass（P1/P2 仅记录）\n"
    "- 不要 append PROGRESS.md；不要 git commit；完成即结束"
)


def _now() -> str:
    return dt.datetime.now().strftime("%H:%M:%S")


def render_prompt(template: str, **kwargs: object) -> str:
    """Safe placeholder substitution: no .format() so literal braces survive."""
    out = template
    for key, value in kwargs.items():
        out = out.replace("{" + key + "}", str(value))
    return out


def run_loop(
    pick_next: Callable[[], Optional[str]],
    dispatch: Callable[[str], int],
    max_tasks: int,
    stop_on_error: bool,
    log: Callable[[str], None] = print,
    *,
    verify: Optional[Callable[[str], Tuple[str, str]]] = None,
    fix: Optional[Callable[[str, str], int]] = None,
    review: Optional[Callable[[str], Tuple[str, str]]] = None,
    max_fix_rounds: int = 3,
    max_review_rounds: int = 3,
) -> dict[str, Any]:
    """Drive the pick → dispatch → (verify → fix)* → (review → fix)* loop.

    Returns a summary dict with one of these shapes:
      {"reason": "no_tasks_ready", "iterations": N}
      {"reason": "max_tasks_reached", "iterations": N}
      {"reason": "task_failed", "iterations": N, "task_id": "...", "exit_code": K}
      {"reason": "fix_failed", "iterations": N, "task_id": "...",
         "exit_code": K, "fix_round": R}
      {"reason": "verify_exhausted", "iterations": N, "task_id": "...",
         "fix_rounds_used": R}
      {"reason": "review_exhausted", "iterations": N, "task_id": "...",
         "review_rounds_used": R}
    """
    iteration = 0
    while iteration < max_tasks:
        task_id = pick_next()
        if task_id is None:
            return {"reason": "no_tasks_ready", "iterations": iteration}
        iteration += 1
        log(
            f">>> [{_now()}] dispatching {task_id} "
            f"(iter {iteration}/{max_tasks})"
        )
        exit_code = dispatch(task_id)
        log(f"<<< [{_now()}] {task_id} dispatch exit={exit_code}")
        if exit_code != 0:
            if stop_on_error:
                return {
                    "reason": "task_failed",
                    "iterations": iteration,
                    "task_id": task_id,
                    "exit_code": exit_code,
                }
            continue

        if verify is None:
            continue

        status, report = verify(task_id)
        log(f"... verify({task_id}) -> {status}")
        fix_round = 0
        while status != "pass" and fix_round < max_fix_rounds:
            if fix is None:
                break
            fix_round += 1
            log(
                f">>> [{_now()}] fixing {task_id} "
                f"(round {fix_round}/{max_fix_rounds})"
            )
            fix_rc = fix(task_id, report)
            log(f"<<< [{_now()}] {task_id} fix exit={fix_rc}")
            if fix_rc != 0:
                if stop_on_error:
                    return {
                        "reason": "fix_failed",
                        "iterations": iteration,
                        "task_id": task_id,
                        "exit_code": fix_rc,
                        "fix_round": fix_round,
                    }
                break
            status, report = verify(task_id)
            log(f"... verify({task_id}) -> {status}")

        if status != "pass":
            if stop_on_error:
                return {
                    "reason": "verify_exhausted",
                    "iterations": iteration,
                    "task_id": task_id,
                    "fix_rounds_used": fix_round,
                }
            continue

        if review is None:
            continue

        r_status, r_report = review(task_id)
        log(f"... review({task_id}) -> {r_status}")
        review_round = 0
        while r_status != "pass" and review_round < max_review_rounds:
            if fix is None:
                break
            review_round += 1
            log(
                f">>> [{_now()}] review-fix {task_id} "
                f"(round {review_round}/{max_review_rounds})"
            )
            fix_rc = fix(task_id, r_report)
            log(f"<<< [{_now()}] {task_id} review-fix exit={fix_rc}")
            if fix_rc != 0:
                if stop_on_error:
                    return {
                        "reason": "fix_failed",
                        "iterations": iteration,
                        "task_id": task_id,
                        "exit_code": fix_rc,
                        "fix_round": review_round,
                    }
                break
            r_status, r_report = review(task_id)
            log(f"... review({task_id}) -> {r_status}")

        if r_status != "pass" and stop_on_error:
            return {
                "reason": "review_exhausted",
                "iterations": iteration,
                "task_id": task_id,
                "review_rounds_used": review_round,
            }
    return {"reason": "max_tasks_reached", "iterations": iteration}


def run_parallel_loop(
    pick_batch: Callable[[int], list[str]],
    dispatch: Callable[[str], int],
    verify: Optional[Callable[[str], Tuple[str, str]]],
    fix: Optional[Callable[[str, str], int]],
    review: Optional[Callable[[str], Tuple[str, str]]],
    max_tasks: int,
    parallel: int,
    stop_on_error: bool,
    log: Callable[[str], None] = print,
    *,
    max_fix_rounds: int = 3,
    max_review_rounds: int = 3,
) -> dict[str, Any]:
    """Run up to `parallel` task pipelines concurrently via thread pool.

    Each task pipeline = dispatch → verify → (fix→verify)* → review →
    (fix→review)*. Tasks in the same batch are picked to have disjoint
    allowed_files (enforced by `pick_batch`), so the only shared mutable
    state at risk is PROGRESS.md (agents append — OS-level append is
    atomic for single small writes; agents that rewrite the file are a
    known hazard documented in the summary doc).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    iteration = 0
    while iteration < max_tasks:
        remaining = max_tasks - iteration
        limit = min(parallel, remaining)
        batch = pick_batch(limit)
        if not batch:
            return {"reason": "no_tasks_ready", "iterations": iteration}
        batch = list(batch)[:limit]

        def _single_task_pipeline(task_id: str) -> dict[str, Any]:
            pick_once = [task_id]

            def _pick() -> str | None:
                return pick_once.pop(0) if pick_once else None

            return run_loop(
                pick_next=_pick,
                dispatch=dispatch,
                max_tasks=1,
                stop_on_error=stop_on_error,
                log=log,
                verify=verify,
                fix=fix,
                review=review,
                max_fix_rounds=max_fix_rounds,
                max_review_rounds=max_review_rounds,
            )

        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = {
                pool.submit(_single_task_pipeline, tid): tid for tid in batch
            }
            results: list[dict[str, Any]] = []
            for fut in as_completed(futures):
                results.append(fut.result())

        iteration += len(batch)

        if stop_on_error:
            for r in results:
                if r["reason"] in (
                    "task_failed",
                    "fix_failed",
                    "verify_exhausted",
                    "review_exhausted",
                ):
                    r["iterations"] = iteration
                    return r

    return {"reason": "max_tasks_reached", "iterations": iteration}


def build_dispatch_command(
    program: str,
    task_id: str,
    max_turns: int,
    prompt_template: str,
) -> list[str]:
    """Return argv for the developer `claude -p` invocation."""
    prompt = render_prompt(prompt_template, task_id=task_id)
    return [program, "-p", prompt, "--max-turns", str(max_turns)]


def _render_verifier_prompt(template: str, task_id: str, bdd_tag_expr: str) -> str:
    """Render verifier prompt: substitute {task_id} and {bdd_block}."""
    out = template.replace("{task_id}", str(task_id))
    out = out.replace("{bdd_block}", _build_bdd_block(bdd_tag_expr))
    return out


def build_verifier_command(
    program: str,
    task_id: str,
    max_turns: int,
    prompt_template: str,
    bdd_tag_expr: str = "",
) -> list[str]:
    """Return argv for the independent verifier `claude -p` invocation.

    bdd_tag_expr is a pytest marker expression (no '@' prefix, space-free);
    when non-empty, the prompt instructs the verifier to also run
    `pytest tests/integration/bdd/ -m "<expr>"`.
    """
    prompt = _render_verifier_prompt(prompt_template, task_id, bdd_tag_expr)
    return [program, "-p", prompt, "--max-turns", str(max_turns)]


def build_fixer_command(
    program: str,
    task_id: str,
    max_turns: int,
    prompt_template: str,
) -> list[str]:
    """Return argv for the fixer `claude -p` invocation."""
    prompt = render_prompt(prompt_template, task_id=task_id)
    return [program, "-p", prompt, "--max-turns", str(max_turns)]


def build_reviewer_command(
    program: str,
    task_id: str,
    max_turns: int,
    prompt_template: str,
) -> list[str]:
    """Return argv for the code-reviewer `claude -p` invocation."""
    prompt = render_prompt(prompt_template, task_id=task_id)
    return [program, "-p", prompt, "--max-turns", str(max_turns)]


def make_dispatch(
    build_command: Callable[[str], list[str]],
) -> Callable[[str], int]:
    """Wrap a command-builder into a dispatch callable.

    dispatch(task_id) spawns the built command with AVS_CURRENT_TASK=task_id
    and returns the subprocess's exit code.
    """
    def dispatch(task_id: str) -> int:
        cmd = build_command(task_id)
        env = dict(os.environ)
        env["AVS_CURRENT_TASK"] = task_id
        res = subprocess.run(cmd, env=env, check=False)
        return res.returncode

    return dispatch


def make_verify(
    build_command: Callable[[str], list[str]],
    verify_dir: Path,
) -> Callable[[str], Tuple[str, str]]:
    """Wrap a verifier command-builder into a verify callable.

    verify(task_id) spawns the verifier, reads .verify/<task_id>.json, and
    returns (status, report_path). status ∈ {"pass", "fail", "error"};
    "error" means the report was missing or malformed (treated as failure).
    A stale report from a previous run is deleted before dispatch so a
    missing fresh report cannot be mistaken for a pass.
    """
    verify_dir = Path(verify_dir)

    def verify(task_id: str) -> Tuple[str, str]:
        verify_dir.mkdir(parents=True, exist_ok=True)
        report_path = verify_dir / f"{task_id}.json"
        if report_path.exists():
            report_path.unlink()
        cmd = build_command(task_id)
        env = dict(os.environ)
        env["AVS_CURRENT_TASK"] = task_id
        env["AVS_VERIFY_MODE"] = "1"
        subprocess.run(cmd, env=env, check=False)
        if not report_path.exists():
            return ("error", str(report_path))
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return ("error", str(report_path))
        status = data.get("status")
        if status not in ("pass", "fail"):
            return ("error", str(report_path))
        return (status, str(report_path))

    return verify


def make_review(
    build_command: Callable[[str], list[str]],
    verify_dir: Path,
) -> Callable[[str], Tuple[str, str]]:
    """Wrap a reviewer command-builder into a review callable.

    review(task_id) spawns the reviewer, reads .verify/<task_id>.review.json,
    and returns (status, report_path). status is forced to "fail" if any
    finding has severity "P0" regardless of what the reviewer wrote; P1/P2
    findings alone keep the status as reported (pass). Missing or malformed
    reports surface as "error". A stale report from the previous run is
    deleted before dispatch.
    """
    verify_dir = Path(verify_dir)

    def review(task_id: str) -> Tuple[str, str]:
        verify_dir.mkdir(parents=True, exist_ok=True)
        report_path = verify_dir / f"{task_id}.review.json"
        if report_path.exists():
            report_path.unlink()
        cmd = build_command(task_id)
        env = dict(os.environ)
        env["AVS_CURRENT_TASK"] = task_id
        env["AVS_REVIEW_MODE"] = "1"
        subprocess.run(cmd, env=env, check=False)
        if not report_path.exists():
            return ("error", str(report_path))
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return ("error", str(report_path))
        status = data.get("status")
        if status not in ("pass", "fail"):
            return ("error", str(report_path))
        findings = data.get("findings") or []
        if any(
            isinstance(f, dict) and f.get("severity") == "P0"
            for f in findings
        ):
            return ("fail", str(report_path))
        return (status, str(report_path))

    return review


def make_fix(
    build_command: Callable[[str], list[str]],
) -> Callable[[str, str], int]:
    """Wrap a fixer command-builder into a fix callable.

    fix(task_id, report_path) spawns the fixer with AVS_CURRENT_TASK and
    AVS_FIX_REPORT in the environment and returns the subprocess exit code.
    """
    def fix(task_id: str, report_path: str) -> int:
        cmd = build_command(task_id)
        env = dict(os.environ)
        env["AVS_CURRENT_TASK"] = task_id
        env["AVS_FIX_REPORT"] = report_path
        res = subprocess.run(cmd, env=env, check=False)
        return res.returncode

    return fix


def _lookup_bdd_tag_expr(root: Path, task_id: str) -> str:
    """Return pytest marker expression derived from the task card's bdd_tags.

    @router / @phase0 → 'router' / 'phase0'; multi-tag → ' or '-joined.
    Empty string if card missing or no bdd_tags.
    """
    try:
        # pytest / repo-root-on-sys.path mode
        from scripts.pick_next_task import load_task_cards
    except ModuleNotFoundError:
        # `python3 scripts/run_task_driver.py` mode — scripts/ is sys.path[0]
        from pick_next_task import load_task_cards  # type: ignore
    cards = load_task_cards(root)
    card = cards.get(task_id)
    if not card or not card.bdd_tags:
        return ""
    # Strip '@' prefix; pytest markers don't include it.
    names = [t.lstrip("@") for t in card.bdd_tags]
    return " or ".join(names)


def pick_next_from_script(
    script_path: Path, root: Path, task_id_override: Optional[str] = None
) -> Callable[[], Optional[str]]:
    """Wrap scripts/pick_next_task.py as a callable returning task_id or None.

    When task_id_override is set, the first call returns that id (validated by
    the picker's --task-id flag) and subsequent calls return None — so the
    driver runs the target task exactly once, regardless of --max-tasks.
    """
    consumed = [False]

    def picker() -> Optional[str]:
        if task_id_override is not None:
            if consumed[0]:
                return None
            consumed[0] = True
            cmd = [
                sys.executable,
                str(script_path),
                "--root",
                str(root),
                "--task-id",
                task_id_override,
            ]
        else:
            cmd = [sys.executable, str(script_path), "--root", str(root)]
        res = subprocess.run(
            cmd, capture_output=True, text=True, check=False,
        )
        if res.returncode != 0:
            return None
        out = res.stdout.strip()
        return out or None

    return picker


def _parse_args(argv: Optional[list[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pick → dispatch developer `claude -p` → verify → fix → "
            "repeat until no tasks ready."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root (defaults to cwd).",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=999,
        help="Cap on tasks dispatched this session (default: 999).",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=120,
        help="--max-turns forwarded to developer `claude -p` (default: 120).",
    )
    parser.add_argument(
        "--verifier-max-turns",
        type=int,
        default=40,
        help="--max-turns for verifier `claude -p` (default: 40).",
    )
    parser.add_argument(
        "--fixer-max-turns",
        type=int,
        default=60,
        help="--max-turns for fixer `claude -p` (default: 60).",
    )
    parser.add_argument(
        "--max-fix-rounds",
        type=int,
        default=3,
        help="Maximum fix attempts per task before giving up (default: 3).",
    )
    parser.add_argument(
        "--verify-dir",
        type=Path,
        default=Path(".verify"),
        help="Directory (relative to --root) for verifier JSON reports.",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verifier/fixer loop (single-agent legacy mode).",
    )
    parser.add_argument(
        "--reviewer-max-turns",
        type=int,
        default=40,
        help="--max-turns for reviewer `claude -p` (default: 40).",
    )
    parser.add_argument(
        "--max-review-rounds",
        type=int,
        default=3,
        help=(
            "Maximum P0-finding-driven review-fix cycles per task (default: 3)."
        ),
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Skip code-reviewer stage (verify-only).",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help=(
            "Run up to N tasks concurrently (default: 1 = sequential). "
            "Tasks in the same batch must have disjoint allowed_files."
        ),
    )
    parser.add_argument(
        "--program",
        default="claude",
        help="Dispatch program (default: claude).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print next task and command without invoking dispatch.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep dispatching even after a task exits non-zero.",
    )
    parser.add_argument(
        "--task-id",
        default=None,
        help=(
            "Target a specific task id (bypass picker ordering). Runs "
            "exactly once, then ends. Used for driver smoke tests and "
            "for live BDD-loop runs against a specific feature/card."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    script = args.root / "scripts" / "pick_next_task.py"
    if not script.exists():
        print(f"ERROR: missing {script}", file=sys.stderr)
        return 3
    picker = pick_next_from_script(script, args.root, args.task_id)

    if args.dry_run:
        task_id = picker()
        if task_id is None:
            print("[DRY-RUN] no tasks ready")
            return 0
        cmd = build_dispatch_command(
            args.program, task_id, args.max_turns, DEFAULT_PROMPT_TEMPLATE
        )
        print(f"[DRY-RUN] next task: {task_id}")
        print(
            f"[DRY-RUN] would invoke: {cmd[0]} -p <prompt> "
            f"--max-turns {args.max_turns}"
        )
        print(f"[DRY-RUN] with env AVS_CURRENT_TASK={task_id}")
        if not args.no_verify:
            print(
                f"[DRY-RUN] then verifier: {args.program} -p <prompt> "
                f"--max-turns {args.verifier_max_turns} "
                f"(report → {args.verify_dir}/{task_id}.json)"
            )
            print(
                f"[DRY-RUN] max_fix_rounds={args.max_fix_rounds}, "
                f"fixer --max-turns {args.fixer_max_turns}"
            )
            if not args.no_review:
                print(
                    f"[DRY-RUN] then reviewer: {args.program} -p <prompt> "
                    f"--max-turns {args.reviewer_max_turns} "
                    f"(report → {args.verify_dir}/{task_id}.review.json)"
                )
                print(
                    f"[DRY-RUN] max_review_rounds={args.max_review_rounds}"
                )
        if args.parallel > 1:
            print(
                f"[DRY-RUN] parallel={args.parallel} — batches via "
                f"pick_next_batch(disjoint allowed_files)"
            )
        return 0

    dispatch = make_dispatch(
        lambda tid: build_dispatch_command(
            args.program, tid, args.max_turns, DEFAULT_PROMPT_TEMPLATE
        )
    )
    verify_cb: Optional[Callable[[str], Tuple[str, str]]] = None
    fix_cb: Optional[Callable[[str, str], int]] = None
    review_cb: Optional[Callable[[str], Tuple[str, str]]] = None
    if not args.no_verify:
        verify_cb = make_verify(
            lambda tid: build_verifier_command(
                args.program,
                tid,
                args.verifier_max_turns,
                VERIFIER_PROMPT_TEMPLATE,
                _lookup_bdd_tag_expr(args.root, tid),
            ),
            args.root / args.verify_dir,
        )
        fix_cb = make_fix(
            lambda tid: build_fixer_command(
                args.program,
                tid,
                args.fixer_max_turns,
                FIXER_PROMPT_TEMPLATE,
            )
        )
        if not args.no_review:
            review_cb = make_review(
                lambda tid: build_reviewer_command(
                    args.program,
                    tid,
                    args.reviewer_max_turns,
                    REVIEWER_PROMPT_TEMPLATE,
                ),
                args.root / args.verify_dir,
            )
    if args.parallel > 1:
        _batch_script = args.root / "scripts" / "pick_next_task.py"  # noqa: F841
        import pick_next_task as _pnt

        def _pick_batch(limit: int) -> list[str]:
            return cast(list[str], _pnt.pick_next_batch(args.root, limit))

        result = run_parallel_loop(
            pick_batch=_pick_batch,
            dispatch=dispatch,
            verify=verify_cb,
            fix=fix_cb,
            review=review_cb,
            max_tasks=args.max_tasks,
            parallel=args.parallel,
            stop_on_error=not args.continue_on_error,
            max_fix_rounds=args.max_fix_rounds,
            max_review_rounds=args.max_review_rounds,
        )
    else:
        result = run_loop(
            pick_next=picker,
            dispatch=dispatch,
            max_tasks=args.max_tasks,
            stop_on_error=not args.continue_on_error,
            verify=verify_cb,
            fix=fix_cb,
            review=review_cb,
            max_fix_rounds=args.max_fix_rounds,
            max_review_rounds=args.max_review_rounds,
        )
    print(f"=== Driver done: {result} ===")
    if result["reason"] in (
        "task_failed",
        "fix_failed",
        "verify_exhausted",
        "review_exhausted",
    ):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
