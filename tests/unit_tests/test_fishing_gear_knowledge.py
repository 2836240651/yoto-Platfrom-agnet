"""Tests for deterministic fishing-gear knowledge retrieval."""

import pytest

from agent.knowledge.fishing_gear import plan_fishing_gear_queries
from agent.nodes.init_task import init_task
from agent.tools.arg_builders import build_tool_args


def test_niche_method_uses_only_narrow_expansions():
    result = plan_fishing_gear_queries("反底钓")

    assert result["canonical"] == "反底钓"
    assert [item["term"] for item in result["query_plan"]] == ["反底钓法", "反底钓线组"]
    assert all(item["source"] == "fishing_gear_kb" for item in result["query_plan"])
    assert all(item["term"] not in {"钓鱼", "渔具", "鱼竿"} for item in result["query_plan"])


def test_hook_alias_resolves_to_canonical_product_without_broad_bridge():
    result = plan_fishing_gear_queries("海夕8号")

    assert result["canonical"] == "海夕鱼钩"
    assert [item["term"] for item in result["query_plan"]] == ["海夕鱼钩", "海夕钩"]
    assert result["category"] == "鱼钩与钓组"


@pytest.mark.parametrize(
    ("seed", "canonical", "terms"),
    [
        ("反底钓", "反底钓", ["反底钓法", "反底钓线组"]),
        ("海夕8号", "海夕鱼钩", ["海夕鱼钩", "海夕钩"]),
        ("筏轮微铅", "筏钓轮", ["筏钓轮", "筏钓轮微铅"]),
        ("钨坠", "钨钢坠", ["钨钢坠", "钨钢坠路亚"]),
        ("波爬", "波爬", ["波爬拟饵"]),
    ],
)
def test_five_niche_fishing_terms_have_auditable_narrow_query_plans(seed, canonical, terms):
    result = plan_fishing_gear_queries(seed)

    assert result["matched"] is True
    assert result["canonical"] == canonical
    assert [item["term"] for item in result["query_plan"]] == terms
    assert len(result["query_plan"]) <= 2
    assert all(item["source"] == "fishing_gear_kb" for item in result["query_plan"])
    assert all(item["term"] not in {"钓鱼", "渔具", "鱼竿"} for item in result["query_plan"])


def test_broad_or_unknown_input_does_not_create_hidden_expansion():
    assert plan_fishing_gear_queries("渔具")["query_plan"] == []
    assert plan_fishing_gear_queries("自定义未收录配件")["query_plan"] == []


def test_collect_builder_forwards_explicit_kb_query_plan():
    planned = plan_fishing_gear_queries("海夕8号")["query_plan"]

    args = build_tool_args(
        "douyin_collect_hot_keywords",
        {
            "seed": "海夕8号",
            "query_plan": planned,
            "include_video": True,
            "include_product": True,
            "date_range_days": 30,
        },
    )

    assert args["seed"] == "海夕8号"
    assert args["query_plan"] == planned


def test_init_task_uses_kb_plan_when_operator_did_not_supply_one():
    initialized = init_task(
        {
            "skill": "douyin-keyword-research",
            "seed": "海夕8号",
            "include_video": True,
            "include_product": True,
            "date_range_days": 30,
        }
    )

    assert [item["term"] for item in initialized["query_plan"]] == ["海夕鱼钩", "海夕钩"]
    assert initialized["kb_context"][0]["canonical"] == "海夕鱼钩"
