"""TaskCreateRequest model_id validation (scheme A + black-box strip)."""

import pytest
from pydantic import ValidationError

from app.schemas.tasks import TaskCreateRequest


def test_omit_model_id_ok():
    body = TaskCreateRequest(skill="douyin-keyword-research", seed="渔具")
    assert body.model_id is None


def test_pin_luna_ok():
    body = TaskCreateRequest(
        skill="douyin-keyword-research", seed="渔具", model_id="gpt-5.6-luna"
    )
    assert body.model_id == "gpt-5.6-luna"


def test_illegal_model_id_raises():
    with pytest.raises(ValidationError) as ei:
        TaskCreateRequest(
            skill="douyin-keyword-research", seed="渔具", model_id="gpt-4-nope"
        )
    assert "model_id not in allowlist" in str(ei.value)


def test_blackbox_strips_even_illegal():
    body = TaskCreateRequest(
        skill="temu-product-listing",
        shop_id="8381218",
        excel_path="/data/x.xlsx",
        model_id="gpt-4-nope",
    )
    assert body.model_id is None


def test_blackbox_strips_luna():
    body = TaskCreateRequest(
        skill="temu-product-listing",
        shop_id="8381218",
        excel_path="/data/x.xlsx",
        model_id="gpt-5.6-luna",
    )
    assert body.model_id is None
