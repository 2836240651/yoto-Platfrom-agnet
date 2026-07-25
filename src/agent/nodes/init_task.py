"""Initialize task from API parameters — plan-driven first step."""

from __future__ import annotations

import time

from langchain_core.messages import HumanMessage

from agent.budget import init_budget_fields
from agent.constants import SKILL_PLANS
from agent.nodes.helpers import append_event
from agent.state import AgentState

SKILL_INIT: dict[str, dict] = {
    "douyin-keyword-research": {
        "message_fn": lambda state: (
            f"分析抖音种子词【{state.get('seed') or '渔具'}】的热搜词与潜力词"
        ),
        "run_timeout_s": 600,
        "quality_threshold": 0.7,
    },
    "temu-product-listing": {
        "message_fn": lambda state: (
            f"Temu 上架：店铺 {state.get('shop_id') or '?'}，文件 {state.get('excel_path') or '?'}"
        ),
        "run_timeout_s": 900,
        "quality_threshold": 0.5,
        "progress_label": "提交上架",
    },
    "social-media-publish": {
        "message_fn": lambda state: (
            f"社媒发布：type={state.get('platform_type') or '?'} "
            f"标题={state.get('title') or '?'} "
            f"文件={state.get('media_path') or '?'}"
        ),
        "run_timeout_s": 900,
        "quality_threshold": 0.5,
        "progress_label": "提交发布",
    },
}


def init_task(state: AgentState) -> dict:
    skill = state.get("skill") or "douyin-keyword-research"
    seed = state.get("seed") or "渔具"
    plan = SKILL_PLANS.get(skill)
    if not plan:
        plan = SKILL_PLANS["douyin-keyword-research"]
        if skill != "douyin-keyword-research":
            skill = "douyin-keyword-research"
    first_name = plan[0]["name"] if plan else "collect"

    overrides = SKILL_INIT.get(skill, {})
    msg_fn = overrides.get("message_fn")
    msg = msg_fn(state) if callable(msg_fn) else f"运行 Skill【{skill}】"

    budget = init_budget_fields(first_name)
    if "run_timeout_s" in overrides:
        budget["run_timeout_s"] = overrides["run_timeout_s"]
    if "quality_threshold" in overrides:
        budget["quality_threshold"] = overrides["quality_threshold"]
    if "progress_label" in overrides:
        budget["progress_step_name"] = overrides["progress_label"]

    return {
        **budget,
        "skill": skill,
        "seed": seed,
        "excel_path": state.get("excel_path") or "",
        "shop_id": state.get("shop_id") or "",
        "agent_id": state.get("agent_id") or "",
        "platform": state.get("platform") or "temu",
        "media_path": state.get("media_path") or "",
        "platform_type": int(state.get("platform_type") or 0) or 3,
        "account_list": list(state.get("account_list") or []),
        "title": state.get("title") or "",
        "tags": list(state.get("tags") or []),
        "model_id": state.get("model_id"),
        "status": "planning",
        "current_step": 0,
        "collected_data": {},
        "errors": [],
        "dead_ends": [],
        "events": append_event(state, "init_task", "任务已初始化"),
        "messages": [HumanMessage(content=msg)],
        "run_started_at": time.time(),
        "micro_route": None,
    }
