"""TDD test: TaskCard dataclass parses bdd_tags from task cards."""

from __future__ import annotations

from scripts.pick_next_task import load_task_cards, TaskCard


def test_task_card_parses_bdd_tags(tmp_path, monkeypatch):
    root = tmp_path
    (root / "tasks" / "SPEC-A").mkdir(parents=True)
    card = root / "tasks" / "SPEC-A" / "A-001-example.md"
    card.write_text(
        "# [SPEC-A-001] Example\n\n"
        "## Metadata\n"
        "- **task_id**: SPEC-A-001\n"
        "- **depends_on**: []\n"
        "- **priority**: P0\n"
        "- **allowed_files**: [src/foo.py]\n"
        "- **bdd_tags**: [@router, @classification]\n",
        encoding="utf-8",
    )
    cards = load_task_cards(root)
    assert "SPEC-A-001" in cards
    c: TaskCard = cards["SPEC-A-001"]
    assert c.bdd_tags == ["@router", "@classification"]


def test_task_card_bdd_tags_defaults_empty(tmp_path):
    root = tmp_path
    (root / "tasks" / "SPEC-A").mkdir(parents=True)
    card = root / "tasks" / "SPEC-A" / "A-002-no-bdd.md"
    card.write_text(
        "# [SPEC-A-002] No BDD\n\n"
        "## Metadata\n"
        "- **task_id**: SPEC-A-002\n"
        "- **depends_on**: []\n"
        "- **priority**: P1\n"
        "- **allowed_files**: [src/bar.py]\n",
        encoding="utf-8",
    )
    cards = load_task_cards(root)
    assert cards["SPEC-A-002"].bdd_tags == []
