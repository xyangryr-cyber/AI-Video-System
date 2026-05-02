"""[Phase C] ClarificationAgent — context-aware clarification prompts.

Generates clarification questions when IntentRouter returns action: clarify.
Phase-aware: different prompt templates for P0, P1, and later phases.
"""

from __future__ import annotations

from typing import Any

# Phase-aware clarification templates
_P0_PROMPT = (
    "请帮我确认以下几点：\n"
    "1. 你想做的视频主题是什么？（例如：解读某个经济数据、分析某个行业趋势）\n"
    "2. 目标受众是谁？（例如：个人投资者、机构从业者、大众理财人群）\n"
    "3. 预期视频时长大概多久？（例如：3分钟以内、5-10分钟）\n"
    "4. 是否有关键数据或观点需要包含？"
)

_P1_PROMPT = (
    "已了解基本需求。接下来请确认：\n"
    "1. 你希望选题从什么角度切入？（例如：正面解读、风险提示、对比分析）\n"
    "2. 大纲结构有什么特别要求吗？（例如：先讲背景再讲数据、先抛结论再展开）"
)

_GENERIC_PROMPT = "请进一步描述你的需求，我会根据你的反馈给出更精准的建议。"

_INITIAL_PROMPT = "你好！我是你的AI视频制作助手。让我们开始制作视频吧。\n\n" + _P0_PROMPT


class ClarificationAgent:
    """Stateless agent that generates phase-aware clarification questions."""

    def generate(
        self,
        *,
        phase: int = 0,
        project_meta: dict[str, Any] | None = None,
    ) -> str:
        """Return a clarification prompt appropriate for the current phase.

        Args:
            phase: Current project phase number (0=P0, 1=P1, ...).
            project_meta: Optional project metadata for context.

        Returns:
            A clarification question string in Chinese.
        """
        title = ""
        if project_meta:
            title = str(project_meta.get("title", ""))

        if phase == 0:
            return _P0_PROMPT
        elif phase == 1:
            return _P1_PROMPT
        else:
            return _GENERIC_PROMPT

    def initial_prompt(self, *, title: str = "") -> str:
        """Generate the initial Agent greeting when a project is first created.

        Args:
            title: The project title.

        Returns:
            An initial prompt string combining greeting and P0 clarification.
        """
        if title:
            return f"你好！项目「{title}」已创建。我是你的AI视频制作助手。\n\n" + _P0_PROMPT
        return _INITIAL_PROMPT


__all__ = ["ClarificationAgent"]
