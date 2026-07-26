"""Prompt-contract tests for the Douyin keyword research flow."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_douyin_skill_limits_niche_expansion_to_explicit_narrow_variants():
    skill = (ROOT / "skills" / "douyin-keyword-research" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "query_plan" in skill
    assert "最多允许 2 个窄变体" in skill
    assert "保留种子词的技术限定成分" in skill
    assert "钓鱼、渔具、鱼竿" in skill
    assert "不可把扩词结果表述为原种子词的实测结果" in skill
