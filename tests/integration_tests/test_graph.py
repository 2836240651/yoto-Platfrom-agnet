import pytest
from langchain_core.messages import HumanMessage

from agent.graph import build_graph

pytestmark = pytest.mark.anyio


async def test_agent_douyin_keyword_flow() -> None:
    graph = build_graph(with_checkpointer=False)
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="分析抖音渔具热搜词")],
            "seed": "渔具",
            "skill": "douyin-keyword-research",
            "include_video": True,
            "include_product": True,
            "date_range_days": 30,
            "skip_transient_sim": True,
        },
    )
    assert result is not None
    assert result.get("skill") == "douyin-keyword-research"
    assert result.get("status") == "done"
    assert result.get("report") is not None
    assert result["report"].get("kind") == "douyin_keyword"
    assert result["report"]["summary"]["keyword_count"] > 0
    alerts = result["report"].get("alerts") or []
    assert any(
        any(k in (a.get("text") or "") for k in ("stub", "原子 MCP", "蝉妈妈", "模拟"))
        for a in alerts
    ) or (result["report"].get("data_source") or {}).get("source") in (
        "stub",
        "stub_fallback",
        "mcp",
    )
    assert "final_answer" in result


async def test_micro_budget_fields_initialized() -> None:
    graph = build_graph(with_checkpointer=False)
    result = await graph.ainvoke(
        {
            "seed": "渔具",
            "skill": "douyin-keyword-research",
            "skip_transient_sim": True,
        },
    )
    # collect micro max is 1 (black-box MCP); later steps keep higher caps in budget table
    assert result.get("micro_budget_max", 0) >= 1
    assert result.get("global_loop_used", 0) > 0
