"""LangGraph agent runtime v0.2 — Plan-and-Execute hybrid loop."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agent.nodes.act import act_tool_or_llm
from agent.nodes.consolidate import consolidate
from agent.nodes.emit_progress import emit_progress
from agent.nodes.fail_terminal import fail_terminal
from agent.nodes.generate import generate_report
from agent.nodes.init_task import init_task
from agent.nodes.macro_plan import macro_plan
from agent.nodes.macro_reflect import macro_reflect
from agent.nodes.micro_judge import micro_judge
from agent.nodes.observe import observe
from agent.nodes.replan import replan_fragment
from agent.nodes.retrieve import retrieve_memory
from agent.nodes.route import route_skill
from agent.nodes.router import (
    after_emit_progress,
    after_micro_judge,
    after_step_enter,
    after_validate,
)
from agent.nodes.step_enter import step_enter
from agent.nodes.step_exit import step_exit
from agent.nodes.think import think_or_rule
from agent.nodes.validate import validate_report_schema
from agent.state import AgentState

# Shared checkpointer for API thread resume / polling
_CHECKPOINTER = MemorySaver()


def build_graph(*, with_checkpointer: bool = True):
    """Build and compile the v0.2 agent graph."""
    builder = StateGraph(AgentState)

    builder.add_node("init_task", init_task)
    builder.add_node("route", route_skill)
    builder.add_node("macro_plan", macro_plan)
    builder.add_node("retrieve", retrieve_memory)
    builder.add_node("step_enter", step_enter)
    builder.add_node("think", think_or_rule)
    builder.add_node("act", act_tool_or_llm)
    builder.add_node("observe", observe)
    builder.add_node("micro_judge", micro_judge)
    builder.add_node("step_exit", step_exit)
    builder.add_node("emit_progress", emit_progress)
    builder.add_node("replan", replan_fragment)
    builder.add_node("macro_reflect", macro_reflect)
    builder.add_node("generate", generate_report)
    builder.add_node("validate", validate_report_schema)
    builder.add_node("consolidate", consolidate)
    builder.add_node("fail", fail_terminal)

    builder.set_entry_point("init_task")
    builder.add_edge("init_task", "route")
    builder.add_edge("route", "macro_plan")
    builder.add_edge("macro_plan", "retrieve")
    builder.add_edge("retrieve", "step_enter")

    builder.add_conditional_edges(
        "step_enter",
        after_step_enter,
        {"think": "think", "macro_reflect": "macro_reflect", "fail": "fail"},
    )
    builder.add_edge("think", "act")
    builder.add_edge("act", "observe")
    builder.add_edge("observe", "micro_judge")
    builder.add_conditional_edges(
        "micro_judge",
        after_micro_judge,
        {
            "step_exit": "step_exit",
            "think": "think",
            "replan": "replan",
            "macro_reflect": "macro_reflect",
            "fail": "fail",
        },
    )
    builder.add_edge("replan", "step_enter")
    builder.add_edge("step_exit", "emit_progress")
    builder.add_conditional_edges(
        "emit_progress",
        after_emit_progress,
        {"step_enter": "step_enter", "macro_reflect": "macro_reflect"},
    )
    builder.add_edge("macro_reflect", "generate")
    builder.add_edge("generate", "validate")
    builder.add_conditional_edges(
        "validate",
        after_validate,
        {"consolidate": "consolidate", "generate": "generate", "fail": "fail"},
    )
    builder.add_edge("consolidate", END)
    builder.add_edge("fail", END)

    checkpointer = _CHECKPOINTER if with_checkpointer else None
    return builder.compile(checkpointer=checkpointer, name="agent-platform")


def get_checkpointer() -> MemorySaver:
    return _CHECKPOINTER


graph = build_graph()
