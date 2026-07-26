"""Unit tests for LLM tier + session model_id pin (no network)."""

import pytest

from agent.constants import ALLOWED_MODEL_IDS
from agent.llm import (
    HEAVY_TASKS,
    LIGHT_TASKS,
    resolve_chat_endpoint,
    resolve_tier,
)


def test_resolve_tier_explicit():
    assert resolve_tier(tier="heavy") == "heavy"
    assert resolve_tier(tier="light") == "light"
    assert resolve_tier("ops_analysis", tier="light") == "light"


def test_resolve_tier_by_task():
    for t in LIGHT_TASKS:
        assert resolve_tier(t) == "light", t
    for t in HEAVY_TASKS:
        assert resolve_tier(t) == "heavy", t


def test_resolve_tier_default_light():
    assert resolve_tier(None) == "light"
    assert resolve_tier("") == "light"
    assert resolve_tier("intent_classify") == "light"
    assert resolve_tier("ops_analysis") == "heavy"


def test_catalog_ops_analysis_uses_service_default_model_when_unpinned():
    _key, model, _base, tier = resolve_chat_endpoint(task="ops_analysis")
    assert tier == "heavy"
    assert model == "gpt-5.6"


def test_pin_luna_overrides_intent_task():
    _key, model, _base, tier = resolve_chat_endpoint(
        model_id="gpt-5.6-luna", task="intent_classify"
    )
    assert model == "gpt-5.6-luna"
    assert tier is None  # pinned


def test_pin_agnes_overrides_ops_analysis():
    _key, model, _base, tier = resolve_chat_endpoint(
        model_id="agnes-2.0-flash", task="ops_analysis"
    )
    assert model == "agnes-2.0-flash"
    assert tier is None


def test_pin_illegal_raises():
    with pytest.raises(ValueError, match="allowlist"):
        resolve_chat_endpoint(model_id="gpt-4-nope")


def test_allowlist_covers_picker():
    assert "agnes-2.0-flash" in ALLOWED_MODEL_IDS
    assert "gpt-5.6-luna" in ALLOWED_MODEL_IDS
    assert "gpt-5.6-sol" in ALLOWED_MODEL_IDS
    assert "gpt-5.6-terra" in ALLOWED_MODEL_IDS


def test_for_state_forwards_model_id():
    from agent.llm import resolve_chat_endpoint_for_state

    _k, model, _b, tier = resolve_chat_endpoint_for_state(
        {"skill": "douyin-keyword-research", "model_id": "gpt-5.6-luna"},
        task="intent_classify",
    )
    assert model == "gpt-5.6-luna"
    assert tier is None


def test_for_state_catalog_when_unpinned():
    from agent.llm import resolve_chat_endpoint_for_state

    _k, _model, _b, tier = resolve_chat_endpoint_for_state(
        {"skill": "douyin-keyword-research", "model_id": None},
        task="ops_analysis",
    )
    assert tier == "heavy"


def test_for_state_blackbox_raises():
    from agent.llm import resolve_chat_endpoint_for_state

    with pytest.raises(RuntimeError, match="black-box"):
        resolve_chat_endpoint_for_state(
            {"skill": "temu-product-listing", "model_id": "gpt-5.6-luna"},
            task="intent_classify",
        )
