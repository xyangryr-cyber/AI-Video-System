"""SPEC-A-106 (v3.18 D1): ProjectInfo gains category + updated_at."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.shared.schemas.project_state import ProjectInfo


def test_project_info_requires_category():
    with pytest.raises(ValidationError):
        ProjectInfo(
            project_id="proj_x",
            title="t",
            description="d",
            current_phase=0,
            status="active",
            updated_at="2026-04-17T12:00:00Z",
        )


def test_project_info_requires_updated_at():
    with pytest.raises(ValidationError):
        ProjectInfo(
            project_id="proj_x",
            title="t",
            description="d",
            current_phase=0,
            status="active",
            category="行业分析",
        )


def test_project_info_accepts_category_and_updated_at():
    p = ProjectInfo(
        project_id="proj_x",
        title="t",
        description="d",
        current_phase=0,
        status="active",
        category="行业分析",
        updated_at="2026-04-17T12:00:00Z",
    )
    assert p.category == "行业分析"
    assert p.updated_at == "2026-04-17T12:00:00Z"
