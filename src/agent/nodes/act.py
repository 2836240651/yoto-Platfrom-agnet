"""Execute tool or step handlers (registry-driven)."""

from __future__ import annotations

from typing import Any

from agent.budget import bump_loop
from agent.config.settings import settings
from agent.nodes.helpers import append_event, current_step_def
from agent.state import AgentState
from agent.tools.arg_builders import build_tool_args
from agent.tools.mcp_runtime import mcp_runtime
from agent.tools.step_handlers import run_step_action
from agent.tools.stub_dispatch import get_stub
from agent.tools.tool_registry import tool_registry


def act_tool_or_llm(state: AgentState) -> dict:
    step = current_step_def(state)
    if not step:
        return {
            **bump_loop(state),
            "failure_class": "permanent",
            "user_error_message": "执行步骤无效",
            "micro_route": "fail",
        }

    name = step.get("name", "")
    action = state.get("current_action") or ""
    collected = dict(state.get("collected_data") or {})
    skill = state.get("skill") or "douyin-keyword-research"
    attempt = state.get("micro_budget_used", 0) + 1

    simulate_transient = (
        not state.get("skip_transient_sim", True)
        and name == "collect"
        and attempt == 1
        and state.get("replan_budget_used", 0) == 0
    )
    if simulate_transient:
        return {
            **bump_loop(state, tokens=200),
            "micro_budget_used": attempt,
            "failure_class": "transient",
            "last_tool_error": "数据源响应超时（模拟）",
            "quality_score": 0.2,
            "last_gain_delta": 0.0,
            "events": append_event(
                state,
                "act",
                "采集超时，准备重试",
                attempt=attempt,
                failure_class="transient",
            ),
        }

    try:
        hard_fail = False
        quality = 0.5

        if action.startswith("tool:"):
            logical = action[5:]
            result, quality, hard_fail = _run_registered_tool(logical, skill, state)
            collected[name] = result
            fail_msg = (
                (result.get("_meta") or {}).get("mcp_error")
                or result.get("error")
                or f"工具「{logical}」执行失败"
            )
        elif action.startswith("action:"):
            handler_name = action[7:]
            updates, quality, hard_fail = run_step_action(handler_name, state, collected)
            collected.update({k: v for k, v in updates.items() if v is not None})
            fail_msg = "步骤处理失败"
        else:
            collected[name] = {"status": "skipped"}
            fail_msg = "未知动作"

        if hard_fail:
            return {
                **bump_loop(state, tokens=200),
                "collected_data": collected,
                "micro_budget_used": attempt,
                "quality_score": quality,
                "last_gain_delta": 0.0,
                "last_step_quality": quality,
                "failure_class": "permanent",
                "last_tool_error": fail_msg,
                "user_error_message": fail_msg,
                "micro_route": "fail",
                "events": append_event(
                    state,
                    "act",
                    f"步骤 {name} 永久失败",
                    attempt=attempt,
                    failure_class="permanent",
                ),
            }

        prev_q = state.get("quality_score") or 0.0
        gain = max(0.0, quality - prev_q)
        return {
            **bump_loop(state, tokens=500),
            "collected_data": collected,
            "micro_budget_used": attempt,
            "quality_score": quality,
            "last_gain_delta": gain,
            "last_step_quality": quality,
            "failure_class": None,
            "last_tool_error": None,
            "events": append_event(
                state,
                "act",
                f"步骤 {name} 执行完成",
                attempt=attempt,
                quality=quality,
            ),
        }
    except PermissionError as exc:
        return {
            **bump_loop(state, tokens=50),
            "micro_budget_used": attempt,
            "failure_class": "policy",
            "last_tool_error": str(exc),
            "user_error_message": str(exc),
            "micro_route": "fail",
            "events": append_event(state, "act", f"策略拒绝：{exc}", attempt=attempt),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            **bump_loop(state, tokens=100),
            "micro_budget_used": attempt,
            "failure_class": "transient",
            "last_tool_error": str(exc),
            "quality_score": state.get("quality_score"),
            "last_gain_delta": 0.0,
            "events": append_event(state, "act", f"步骤 {name} 异常：{exc}", attempt=attempt),
        }


def _run_registered_tool(
    logical: str, skill: str, state: AgentState
) -> tuple[dict[str, Any], float, bool]:
    resolved = tool_registry.resolve(logical)
    tool_registry.assert_allowed(resolved, skill)
    args = build_tool_args(logical, state)
    stub = get_stub(logical, state)
    requires_mcp = bool(resolved.requires_mcp)

    if requires_mcp and not settings.mcp_runtime_enabled:
        payload = {
            "ok": False,
            "error": f"MCP_RUNTIME_ENABLED=false，无法运行 {logical}",
            "_meta": {"source": "mcp", "tool": logical, "mcp_error": "runtime disabled"},
        }
        return payload, 0.1, True

    if not resolved.use_mcp:
        if stub is None:
            payload = {
                "ok": False,
                "error": f"no stub for intentional-stub tool {logical}",
                "_meta": {"source": "stub", "tool": logical},
            }
            return payload, 0.1, True
        payload = stub()
        payload.setdefault("_meta", {})
        payload["_meta"].update({"source": "stub", "tool": logical})
        return payload, tool_registry.quality_for(resolved, payload), False

    if not settings.mcp_runtime_enabled:
        if settings.allow_stub_fallback and stub is not None:
            payload = stub()
            payload.setdefault("_meta", {})
            payload["_meta"].update(
                {
                    "source": "stub_fallback",
                    "tool": logical,
                    "mcp_error": "mcp runtime disabled",
                }
            )
            return payload, tool_registry.quality_for(resolved, payload), False
        payload = {
            "ok": False,
            "error": "MCP runtime disabled",
            "_meta": {"source": "mcp", "tool": logical, "mcp_error": "runtime disabled"},
        }
        return payload, 0.1, True

    mcp_result = mcp_runtime.invoke_logical(logical, args)
    if mcp_result.ok:
        payload = dict(mcp_result.data or {})
        payload.setdefault("_meta", {})
        payload["_meta"].update(
            {
                "source": "mcp",
                "tool": logical,
                "resolved_tool": mcp_result.resolved_tool,
            }
        )
        hard_fail = payload.get("ok") is False
        return payload, tool_registry.quality_for(resolved, payload), hard_fail

    if settings.allow_stub_fallback and stub is not None and not requires_mcp:
        payload = stub()
        payload.setdefault("_meta", {})
        payload["_meta"].update(
            {
                "source": "stub_fallback",
                "tool": logical,
                "mcp_error": mcp_result.error,
            }
        )
        return payload, tool_registry.quality_for(resolved, payload), False

    payload = {
        "ok": False,
        "error": mcp_result.error or f"MCP call failed for {logical}",
        "_meta": {
            "source": "mcp",
            "tool": logical,
            "mcp_error": mcp_result.error,
        },
    }
    return payload, 0.1, True
