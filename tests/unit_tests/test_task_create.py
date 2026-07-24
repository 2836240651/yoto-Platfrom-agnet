"""TaskCreateRequest validators."""

import pytest
from pydantic import ValidationError

from app.schemas.tasks import TaskCreateRequest


def test_douyin_requires_seed():
    with pytest.raises(ValidationError):
        TaskCreateRequest(skill="douyin-keyword-research", seed=None)


def test_douyin_ok():
    body = TaskCreateRequest(
        skill="douyin-keyword-research",
        seed="渔具",
        date_range_days=30,
    )
    assert body.seed == "渔具"


def test_pipeline_skill_rejected():
    with pytest.raises(ValidationError):
        TaskCreateRequest(skill="keyword-cards-pipeline", slugs=["feide"])  # type: ignore[arg-type]
