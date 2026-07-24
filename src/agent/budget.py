"""Loop budget configuration and fuse guards."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from agent.state import AgentState

# Per-macro-step micro budget caps (name -> max).
# Black-box Job steps (submit/finalize): max 1 — wait/retry inside the handler, not the graph.
STEP_MICRO_BUDGET_MAX: dict[str, int] = {
    "collect": 12,
    "expand": 12,
    "score": 4,
    "report": 3,
    "submit": 1,
    "finalize": 1,
}

STEP_MICRO_BUDGET_DEFAULT: dict[str, int] = {
    "collect": 3,
    "expand": 3,
    "score": 2,
    "report": 2,
    "submit": 1,
    "finalize": 1,
}

EXPANDABLE_STEPS = frozenset({"collect", "expand"})


@dataclass
class BudgetDefaults:
    micro_budget_default: int = 3
    micro_budget_max: int = 12
    replan_budget_default: int = 1
    replan_budget_max: int = 3
    global_loop_budget: int = 40
    run_timeout_s: int = 180
    run_token_budget: int = 50_000
    quality_threshold: float = 0.75
    min_gain_delta: float = 0.05
    max_consecutive_no_gain: int = 2
    generate_retry_max: int = 2


DEFAULTS = BudgetDefaults()


def step_micro_default(step_name: str) -> int:
    return STEP_MICRO_BUDGET_DEFAULT.get(step_name, DEFAULTS.micro_budget_default)


def step_micro_max(step_name: str) -> int:
    return STEP_MICRO_BUDGET_MAX.get(step_name, DEFAULTS.micro_budget_max)


def init_budget_fields(step_name: str = "collect") -> dict:
    """Initial budget fields for a new task."""
    return {
        "micro_budget_default": step_micro_default(step_name),
        "micro_budget_current": step_micro_default(step_name),
        "micro_budget_max": step_micro_max(step_name),
        "micro_budget_used": 0,
        "replan_budget_default": DEFAULTS.replan_budget_default,
        "replan_budget_max": DEFAULTS.replan_budget_max,
        "replan_budget_used": 0,
        "global_loop_budget": DEFAULTS.global_loop_budget,
        "global_loop_used": 0,
        "run_timeout_s": DEFAULTS.run_timeout_s,
        "run_started_at": time.time(),
        "run_token_budget": DEFAULTS.run_token_budget,
        "run_token_used": 0,
        "quality_threshold": DEFAULTS.quality_threshold,
        "min_gain_delta": DEFAULTS.min_gain_delta,
        "max_consecutive_no_gain": DEFAULTS.max_consecutive_no_gain,
        "consecutive_no_gain": 0,
        "last_gain_delta": None,
        "quality_score": None,
        "generate_retry_count": 0,
        "generate_retry_max": DEFAULTS.generate_retry_max,
        "failure_class": None,
        "user_error_message": None,
    }


def elapsed_s(state: AgentState) -> float:
    started = state.get("run_started_at") or time.time()
    return time.time() - started


def fuse_tripped(state: AgentState) -> tuple[bool, str | None]:
    """Return (tripped, reason). Code-owned termination only."""
    if state.get("global_loop_used", 0) >= state.get("global_loop_budget", DEFAULTS.global_loop_budget):
        return True, "分析步骤过多已停止，请缩小范围后重试"
    if elapsed_s(state) > state.get("run_timeout_s", DEFAULTS.run_timeout_s):
        return True, "分析超时，请稍后重试"
    if state.get("run_token_used", 0) >= state.get("run_token_budget", DEFAULTS.run_token_budget):
        return True, "本次分析资源预算已用尽，请稍后重试"
    if state.get("consecutive_no_gain", 0) >= state.get(
        "max_consecutive_no_gain", DEFAULTS.max_consecutive_no_gain
    ):
        return True, "连续多轮无有效进展，已自动停止"
    fc = state.get("failure_class")
    if fc in ("policy", "permanent"):
        return True, state.get("user_error_message") or "任务无法继续执行"
    return False, None


def can_extend_micro_budget(state: AgentState, step_name: str) -> bool:
    """Adaptive extension: transient error + expandable step + under hard cap."""
    if step_name not in EXPANDABLE_STEPS:
        return False
    if state.get("failure_class") != "transient":
        return False
    current = state.get("micro_budget_current", 0)
    hard_max = state.get("micro_budget_max", DEFAULTS.micro_budget_max)
    if current >= hard_max:
        return False
    tripped, _ = fuse_tripped(state)
    if tripped:
        return False
    gain = state.get("last_gain_delta")
    min_gain = state.get("min_gain_delta", DEFAULTS.min_gain_delta)
    if gain is not None and gain <= min_gain:
        return False
    return True


def extend_micro_budget(state: AgentState, step_name: str) -> int:
    current = state.get("micro_budget_current", 3)
    hard_max = state.get("micro_budget_max", step_micro_max(step_name))
    if step_name in EXPANDABLE_STEPS:
        new_cap = min(current + 3, hard_max)
    else:
        new_cap = min(current + 1, hard_max)
    return new_cap


def bump_loop(state: AgentState, *, tokens: int = 0) -> dict:
    return {
        "global_loop_used": state.get("global_loop_used", 0) + 1,
        "run_token_used": state.get("run_token_used", 0) + tokens,
    }
