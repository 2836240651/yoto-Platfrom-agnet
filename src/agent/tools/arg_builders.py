"""Build MCP/stub tool arguments from agent state + registry defaults."""

from __future__ import annotations

from typing import Any, Callable

from agent.state import AgentState

ArgBuilder = Callable[[AgentState], dict[str, Any]]


def _seed_window(state: AgentState) -> dict[str, Any]:
    return {
        "seed": state.get("seed") or "渔具",
        "date_range_days": state.get("date_range_days", 30),
        "include_video": bool(state.get("include_video", True)),
        "include_product": bool(state.get("include_product", True)),
    }


def _seed_depth(state: AgentState) -> dict[str, Any]:
    return {"seed": state.get("seed") or "渔具", "depth": 2}


def _ping(_state: AgentState) -> dict[str, Any]:
    return {"message": "health"}


def _temu_submit(state: AgentState) -> dict[str, Any]:
    return {
        "file_path": state.get("excel_path") or "",
        "shop_id": state.get("shop_id") or "",
        "agent_id": state.get("agent_id") or "",
        "platform": state.get("platform") or "temu",
        "precheck": True,
    }


def _temu_status(state: AgentState) -> dict[str, Any]:
    collected = state.get("collected_data") or {}
    submit = collected.get("submit") or {}
    task_ids = submit.get("candidate_task_ids") or []
    task_id = ""
    if isinstance(task_ids, list) and task_ids:
        task_id = str(task_ids[0] or "")
    return {
        "agent_id": state.get("agent_id") or submit.get("agent_id") or "",
        "platform": state.get("platform") or "temu",
        "task_id": task_id,
        "list_scope": "all",
    }


def _social_submit(state: AgentState) -> dict[str, Any]:
    import json

    accounts = state.get("account_list") or []
    tags = state.get("tags") or []
    return {
        "file_path": state.get("media_path") or "",
        "account_list_json": json.dumps(list(accounts), ensure_ascii=False),
        "platform_type": int(state.get("platform_type") or 3),
        "title": state.get("title") or "",
        "tags_json": json.dumps(list(tags), ensure_ascii=False),
        "agent_id": state.get("agent_id") or "",
        "file_list_json": "[]",
    }


def _social_status(state: AgentState) -> dict[str, Any]:
    collected = state.get("collected_data") or {}
    submit = collected.get("submit") or {}
    return {"job_id": str(submit.get("job_id") or "")}


ARG_BUILDERS: dict[str, ArgBuilder] = {
    "douyin_collect_hot_keywords": _seed_window,
    "douyin_expand_suggest_words": _seed_depth,
    "ping": _ping,
    "temu_product_issue_submit": _temu_submit,
    "temu_product_issue_status": _temu_status,
    "social_publish_submit": _social_submit,
    "social_publish_status": _social_status,
}


def build_tool_args(logical_name: str, state: AgentState) -> dict[str, Any]:
    builder = ARG_BUILDERS.get(logical_name)
    return builder(state) if builder else {}


def register_arg_builder(logical_name: str, builder: ArgBuilder) -> None:
    ARG_BUILDERS[logical_name] = builder
