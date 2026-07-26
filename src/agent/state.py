"""Agent graph state definitions."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class StepPlan(TypedDict, total=False):
    id: str
    name: str
    label: str
    tool: str | None
    action: str | None
    status: Literal["pending", "running", "done", "failed"]


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]

    task_id: str
    skill: str
    user_id: str
    status: Literal["planning", "executing", "reviewing", "done", "failed"]

    seed: str
    slugs: list[str]
    deploy: bool
    collect: bool
    include_video: bool
    include_product: bool
    date_range_days: int
    query_plan: list[dict[str, str]]
    kb_context: list[dict[str, Any]]

    excel_path: str
    shop_id: str
    agent_id: str
    platform: str
    media_path: str
    platform_type: int
    account_list: list[str]
    title: str
    tags: list[str]
    # Explicit session pin; null/absent → catalog light|heavy. Black-box skills ignore.
    model_id: str | None

    plan: list[StepPlan]
    current_step: int

    progress_step_name: str
    progress_percent: int
    micro_attempt: int
    replan_used: int

    micro_budget_default: int
    micro_budget_current: int
    micro_budget_max: int
    micro_budget_used: int
    replan_budget_default: int
    replan_budget_max: int
    replan_budget_used: int
    global_loop_budget: int
    global_loop_used: int
    run_timeout_s: int
    run_started_at: float
    run_token_budget: int
    run_token_used: int

    quality_score: float | None
    quality_threshold: float
    min_gain_delta: float
    max_consecutive_no_gain: int
    consecutive_no_gain: int
    last_gain_delta: float | None
    last_step_quality: float | None

    current_action: str | None
    last_tool_error: str | None
    failure_class: str | None
    user_error_message: str | None

    collected_data: dict[str, Any]
    report: dict[str, Any] | None
    final_answer: str
    errors: list[str]
    dead_ends: list[dict[str, Any]]
    events: list[dict[str, Any]]

    generate_retry_count: int
    generate_retry_max: int
    micro_route: str | None
    validate_route: str | None
