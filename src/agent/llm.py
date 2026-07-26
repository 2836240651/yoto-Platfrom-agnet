"""Shared chat model factory — NewAPI OpenAI-compatible, tiered + session pin.

Black-box MCP Skills must not call this for success/fail judgment.
Routing: explicit model_id pin > catalog tier/task > default light.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from agent.config.settings import settings
from agent.constants import ALLOWED_MODEL_IDS

LlmTier = Literal["light", "heavy"]

LIGHT_TASKS = frozenset(
    {
        "summary",
        "fact_extract",
        "intent_classify",
        "memory_compress",
        "format",
        "slot_fill_check",
        "error_paraphrase",
    }
)
HEAVY_TASKS = frozenset(
    {
        "ops_analysis",
        "plan_write",
        "strategy",
        "long_form",
        "complex_reasoning",
    }
)


def resolve_tier(task: str | None = None, *, tier: LlmTier | None = None) -> LlmTier:
    """Map a task label to light/heavy. Explicit ``tier`` wins."""
    if tier in ("light", "heavy"):
        return tier
    if not task:
        return "light"
    key = task.strip().lower()
    if key in HEAVY_TASKS or key.startswith("heavy"):
        return "heavy"
    if key in LIGHT_TASKS or key.startswith("light"):
        return "light"
    return "heavy" if "analy" in key or "plan" in key or "strateg" in key else "light"


def _tier_endpoint(tier: LlmTier) -> tuple[str, str, str]:
    if tier == "heavy":
        key = settings.llm_heavy_api_key or settings.openai_api_key
        model = settings.llm_heavy_model or settings.llm_model
        base = settings.llm_heavy_api_base or settings.openai_api_base
    else:
        key = settings.llm_light_api_key or settings.openai_api_key
        model = settings.llm_light_model or settings.llm_model
        base = settings.llm_light_api_base or settings.openai_api_base
    return (key or "missing"), model, base


def model_id_channel(model_id: str) -> LlmTier:
    """Which API key channel a pinned model_id uses."""
    if model_id.startswith("gpt-5.6"):
        return "heavy"
    return "light"


def _uses_responses_api(model: str) -> bool:
    """Route OpenAI/Codex-family models to the provider's Responses endpoint."""
    return model.startswith("gpt-5.6")


def resolve_chat_endpoint(
    *,
    model_id: str | None = None,
    tier: LlmTier | None = None,
    task: str | None = None,
) -> tuple[str, str, str, LlmTier | None]:
    """Return (api_key, model, base_url, effective_tier_or_None_if_pinned).

    Explicit non-empty ``model_id`` pins model string; key still by channel.
    """
    pinned = (model_id or "").strip() or None
    if pinned:
        if pinned not in ALLOWED_MODEL_IDS:
            raise ValueError(f"model_id not in allowlist: {pinned}")
        channel = model_id_channel(pinned)
        key, _catalog_model, base = _tier_endpoint(channel)
        return key, pinned, base, None
    resolved = resolve_tier(task, tier=tier)
    key, model, base = _tier_endpoint(resolved)
    return key, model, base, resolved


@lru_cache(maxsize=8)
def _cached_chat(model: str, base: str, key: str):
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        api_key=key,
        base_url=base,
        temperature=0,
        use_responses_api=_uses_responses_api(model),
    )


def get_chat_model(
    *,
    model_id: str | None = None,
    tier: LlmTier | None = None,
    task: str | None = None,
    **overrides: Any,
):
    """Return ChatOpenAI.

    Prefer session ``model_id`` (explicit pin). Else ``tier`` / ``task`` catalog.

    Runtime nodes should call ``get_chat_model_for_state`` instead of this,
    so ``state["model_id"]`` is never dropped.
    """
    key, model, base, _ = resolve_chat_endpoint(
        model_id=model_id, tier=tier, task=task
    )
    if overrides:
        from langchain_openai import ChatOpenAI

        kwargs: dict[str, Any] = {
            "model": model,
            "api_key": key,
            "base_url": base,
            "temperature": 0,
            "use_responses_api": _uses_responses_api(model),
        }
        kwargs.update(overrides)
        return ChatOpenAI(**kwargs)
    return _cached_chat(model, base, key)


def resolve_chat_endpoint_for_state(
    state: dict[str, Any],
    *,
    tier: LlmTier | None = None,
    task: str | None = None,
) -> tuple[str, str, str, LlmTier | None]:
    """Resolve endpoint from AgentState (session pin + black-box guard)."""
    from agent.constants import is_blackbox_skill

    if is_blackbox_skill(state.get("skill")):
        raise RuntimeError(
            "black-box skill must not resolve a chat model "
            f"(skill={state.get('skill')!r})"
        )
    return resolve_chat_endpoint(
        model_id=state.get("model_id"),
        tier=tier,
        task=task,
    )


def get_chat_model_for_state(
    state: dict[str, Any],
    *,
    tier: LlmTier | None = None,
    task: str | None = None,
    **overrides: Any,
):
    """Mandatory entry for graph/Skill LLM calls.

    Always forwards ``state["model_id"]``. Raises if skill is black-box.
    """
    key, model, base, _ = resolve_chat_endpoint_for_state(
        state, tier=tier, task=task
    )
    if overrides:
        from langchain_openai import ChatOpenAI

        kwargs: dict[str, Any] = {
            "model": model,
            "api_key": key,
            "base_url": base,
            "temperature": 0,
            "use_responses_api": _uses_responses_api(model),
        }
        kwargs.update(overrides)
        return ChatOpenAI(**kwargs)
    return _cached_chat(model, base, key)
