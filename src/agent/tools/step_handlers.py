"""Configurable step handlers (score / report / temu finalize)."""

from __future__ import annotations

import time
from typing import Any, Callable

from agent.state import AgentState
from agent.tools import douyin_stub
from agent.tools.mcp_runtime import mcp_runtime

Handler = Callable[[AgentState, dict[str, Any]], tuple[dict[str, Any], float, bool]]


def _gather_keywords(collected: dict) -> list[str]:
    words: list[str] = []
    c = collected.get("collect") or {}
    for item in c.get("keywords") or []:
        if isinstance(item, dict) and item.get("word"):
            words.append(item["word"])
    e = collected.get("expand") or {}
    words.extend(e.get("suggest_words") or [])
    seen: set[str] = set()
    out: list[str] = []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def handle_analyze(
    state: AgentState, collected: dict[str, Any]
) -> tuple[dict[str, Any], float, bool]:
    """LLM analysis tool: analyze collect → optimize → score-shaped result."""
    from agent.tools.douyin_analyze import analyze_and_optimize

    collect = collected.get("collect") or {}
    if collect.get("ok") is False:
        msg = collect.get("error") or "采集失败"
        empty = {
            "ok": False,
            "error": msg,
            "categories": {
                "video_hot": [],
                "video_potential": [],
                "product_hot": [],
                "product_potential": [],
            },
            "summary": {
                "keyword_count": 0,
                "video_sample_count": 0,
                "product_sku_count": 0,
                "p0_count": 0,
            },
            "tags": [f"种子词：{state.get('seed') or ''}", "分析：跳过"],
            "alerts": [{"type": "warn", "text": msg}],
            "data_source": {
                "source": (collect.get("_meta") or {}).get("source") or "mcp",
                "tool": "douyin_analyze_keywords",
            },
        }
        return {"analyze": empty, "score": empty}, 0.2, True

    result = analyze_and_optimize(state, collect)
    # Keep `score` alias so generate/report paths stay compatible.
    return {"analyze": result, "score": result}, (0.9 if result.get("ok") else 0.35), False


def handle_score(state: AgentState, collected: dict[str, Any]) -> tuple[dict[str, Any], float, bool]:
    """Deprecated alias — prefer action `analyze`."""
    return handle_analyze(state, collected)


def _llm_refine_for_niche_seed(
    state: AgentState, seed: str, scored: dict[str, Any], collect: dict[str, Any]
) -> dict[str, Any]:
    """Use light LLM to keep words relevant to niche seed (e.g. 欧鲤钓)."""
    try:
        from agent.llm import get_chat_model_for_state
        from langchain_core.messages import HumanMessage, SystemMessage
    except Exception:
        return scored

    cats = scored.get("categories") or {}
    pool: list[str] = []
    for key in ("video_hot", "video_potential", "product_hot", "product_potential"):
        for card in cats.get(key) or []:
            kw = card.get("keyword") if isinstance(card, dict) else None
            if kw:
                pool.append(str(kw))
    pool = list(dict.fromkeys(pool))[:40]
    if len(pool) < 4:
        return scored

    prompt = (
        f"种子词：{seed}\n"
        f"桥接词：{', '.join(collect.get('bridges_used') or [])}\n"
        f"候选词：{', '.join(pool)}\n\n"
        "请从候选词中挑出与种子词运营相关的热搜词与潜力词，输出 JSON（不要 markdown）：\n"
        '{"video_hot":[".."],"video_potential":[".."],"product_hot":[".."],"product_potential":[".."]}\n'
        "规则：内容侧偏话题/玩法；商品侧偏可挂车规格/配件；每栏 3～8 个；不要无关大盘词。"
    )
    try:
        llm = get_chat_model_for_state(state, task="fact_extract")
        resp = llm.invoke(
            [
                SystemMessage(content="你是跨境电商抖音选品运营助手，只输出 JSON。"),
                HumanMessage(content=prompt),
            ]
        )
        text = getattr(resp, "content", None) or str(resp)
        import json
        import re

        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return scored
        data = json.loads(m.group(0))
    except Exception:
        return scored

    hot_lookup: dict[str, dict] = {}
    for key in ("video_hot", "video_potential", "product_hot", "product_potential"):
        for card in cats.get(key) or []:
            if isinstance(card, dict) and card.get("keyword"):
                hot_lookup[str(card["keyword"])] = card

    def build(bucket: str, words: list) -> list[dict]:
        out = []
        for i, w in enumerate(words or []):
            w = str(w).strip()
            if not w:
                continue
            base = hot_lookup.get(w) or _card_from_word(seed, w, priority="P0" if i < 2 else "P1")
            out.append(base)
        return out[:8]

    new_cats = {
        "video_hot": build("video_hot", data.get("video_hot") or []),
        "video_potential": build("video_potential", data.get("video_potential") or []),
        "product_hot": build("product_hot", data.get("product_hot") or []),
        "product_potential": build("product_potential", data.get("product_potential") or []),
    }
    if not any(new_cats.values()):
        return scored
    all_cards = sum(new_cats.values(), [])
    scored = dict(scored)
    scored["categories"] = new_cats
    scored["summary"] = {
        "keyword_count": len(all_cards),
        "video_sample_count": len(new_cats["video_hot"]) + len(new_cats["video_potential"]),
        "product_sku_count": len(new_cats["product_hot"]) + len(new_cats["product_potential"]),
        "p0_count": sum(1 for c in all_cards if c.get("priority") == "P0") or 1,
    }
    return scored


def _card_from_word(
    seed: str, word: str, *, priority: str, hot_level: int = 0, bucket: str = "video_hot"
) -> dict:
    from agent.tools.douyin_analyze import build_card_metrics, format_heat

    side = "product" if bucket.startswith("product") else "video"
    return {
        "keyword": word,
        "priority": priority,
        "trend": "up" if hot_level > 0 else "flat",
        "reason": f"与「{seed}」相关（蝉妈妈采集，{_side_hint(side)}）。",
        "metrics": build_card_metrics(hot=hot_level, side=side, bucket=bucket),
        "evidence": [
            f"采集侧别：{'商品带货' if side == 'product' else '视频内容'}",
            f"蝉妈妈热度：{format_heat(hot_level)}",
        ],
        "action": f"围绕「{word}」做一条可复盘的{'商品' if side == 'product' else '视频'}测试。",
    }


def _side_hint(side: str) -> str:
    return "商品带货" if side == "product" else "视频内容"


def _categories_from_collect(collect: dict[str, Any], seed: str) -> dict[str, Any] | None:
    if not isinstance(collect, dict) or collect.get("ok") is False:
        return None
    keys = ("video_hot", "video_potential", "product_hot", "product_potential")
    if not any(collect.get(k) for k in keys):
        return None
    categories: dict[str, list[dict]] = {k: [] for k in keys}
    for bucket in keys:
        items = collect.get(bucket) or []
        for i, item in enumerate(items[:12]):
            if isinstance(item, str):
                word, hot = item, 0
            else:
                word = str(item.get("word") or item.get("keyword") or "").strip()
                hot = int(item.get("hot_level") or 0)
            if not word:
                continue
            pr = "P0" if i < 2 else "P1" if i < 5 else "P2"
            categories[bucket].append(
                _card_from_word(seed, word, priority=pr, hot_level=hot, bucket=bucket)
            )
    all_cards = sum(categories.values(), [])
    if not all_cards:
        return None
    p0 = sum(1 for c in all_cards if c["priority"] == "P0")
    return {
        "ok": True,
        "categories": categories,
        "summary": {
            "keyword_count": len(all_cards),
            "video_sample_count": len(categories["video_hot"]) + len(categories["video_potential"]),
            "product_sku_count": len(categories["product_hot"]) + len(categories["product_potential"]),
            "p0_count": max(p0, 1),
        },
        "tags": [f"种子词：{seed}", "周期：近30天", "数据源：蝉妈妈"],
        "alerts": [
            {
                "type": "info",
                "text": f"「{seed}」采集完成，请优先看潜力词差异化机会。",
            }
        ],
    }


def handle_report_douyin(
    state: AgentState, collected: dict[str, Any]
) -> tuple[dict[str, Any], float, bool]:
    score = collected.get("score") or collected.get("analyze") or {}
    collect = collected.get("collect") or {}
    meta = (collect.get("_meta") or {}) if isinstance(collect, dict) else {}
    ds = score.get("data_source") if isinstance(score.get("data_source"), dict) else {}
    source = (
        ds.get("source")
        or meta.get("source")
        or (collect.get("data_source") or {}).get("source")
        or "stub"
    )
    draft = {
        "kind": "douyin_keyword",
        "summary": score.get("summary"),
        "tags": score.get("tags"),
        "alerts": score.get("alerts"),
        "categories": score.get("categories"),
        "data_source": {
            "source": source,
            "tool": ds.get("tool") or "douyin_analyze_keywords",
            "provider": ds.get("provider") or ("chanmama" if source == "mcp" else None),
        },
    }
    return {"report_draft": draft}, (0.9 if score.get("ok") else 0.2), False


def handle_finalize_temu_listing(
    state: AgentState, collected: dict[str, Any]
) -> tuple[dict[str, Any], float, bool]:
    """Poll Commander via MCP until terminal status, then build report_draft."""
    submit = collected.get("submit") or {}
    if submit.get("ok") is False:
        msg = submit.get("error") or "提交上架失败"
        draft = {
            "kind": "temu_listing",
            "ok": False,
            "status": "failed",
            "message": msg,
            "shop_id": state.get("shop_id") or submit.get("shop_id"),
            "agent_id": state.get("agent_id") or submit.get("agent_id") or "肉机",
            "task_id": None,
            "data_source": {"source": "mcp", "tool": "temu_product_issue_submit"},
        }
        return {"report_draft": draft, "finalize": draft}, 0.2, True

    agent_id = state.get("agent_id") or submit.get("agent_id") or ""
    platform = state.get("platform") or "temu"
    candidates = submit.get("candidate_task_ids") or []
    task_id = str(candidates[0]) if candidates else ""

    last: dict[str, Any] = {}
    terminal = {"success", "failed", "cancelled"}
    # One graph step: poll inside handler (~10 min). Do not micro-retry at graph level.
    poll_rounds = 40
    poll_interval_s = 15
    for _ in range(poll_rounds):
        result = mcp_runtime.invoke_logical(
            "temu_product_issue_status",
            {
                "agent_id": agent_id,
                "platform": platform,
                "task_id": task_id,
                "list_scope": "all",
            },
        )
        if not result.ok:
            last = {
                "ok": False,
                "status": "failed",
                "message": result.error or "状态查询失败",
                "task_id": task_id or None,
            }
            break
        data = dict(result.data or {})
        if task_id and data.get("tasks"):
            match = next(
                (t for t in data["tasks"] if str(t.get("taskId") or "") == task_id),
                None,
            )
            if match:
                data["status"] = match.get("status")
                data["message"] = match.get("message")
                data["task_id"] = match.get("taskId")
                data["tasks_ahead"] = match.get("tasksAhead")
        last = data
        status = (data.get("status") or "").lower()
        if status in terminal:
            break
        time.sleep(poll_interval_s)

    status = (last.get("status") or "unknown").lower()
    ok = status == "success"
    msg = last.get("message") or last.get("error") or status
    if status == "processing":
        msg = f"仍在处理中（已单步轮询结束）：{msg}"
        ok = False

    draft = {
        "kind": "temu_listing",
        "ok": ok,
        "status": status
        if status in ("processing", "success", "failed", "cancelled")
        else "unknown",
        "message": str(msg),
        "shop_id": state.get("shop_id") or submit.get("shop_id"),
        "agent_id": agent_id or "肉机",
        "task_id": last.get("task_id") or task_id or None,
        "data_source": {"source": "mcp", "tool": "temu_product_issue_status"},
    }
    hard_fail = status in ("failed", "cancelled") or (last.get("ok") is False)
    # processing after in-handler poll: exit graph once (do not micro-retry); quality high enough to pass threshold
    if ok:
        quality = 0.95
    elif status == "processing":
        quality = 0.9
    else:
        quality = 0.25
    return {"report_draft": draft, "finalize": draft}, quality, hard_fail


def handle_finalize_social_publish(
    state: AgentState, collected: dict[str, Any]
) -> tuple[dict[str, Any], float, bool]:
    """Poll automedia publish job until terminal; build social_publish report."""
    submit = collected.get("submit") or {}
    if submit.get("ok") is False:
        msg = submit.get("error") or "提交发布失败"
        draft = {
            "kind": "social_publish",
            "ok": False,
            "status": "failed",
            "message": msg,
            "job_id": submit.get("job_id"),
            "platform_type": state.get("platform_type") or submit.get("platform_type"),
            "publish_runtime": submit.get("publish_runtime"),
            "title": state.get("title") or submit.get("title"),
            "account_list": list(state.get("account_list") or submit.get("account_list") or []),
            "data_source": {"source": "mcp", "tool": "social_publish_submit"},
        }
        return {"report_draft": draft, "finalize": draft}, 0.2, True

    job_id = str(submit.get("job_id") or "")
    if not job_id:
        draft = {
            "kind": "social_publish",
            "ok": False,
            "status": "failed",
            "message": "缺少 job_id，无法确认发布终态",
            "job_id": None,
            "platform_type": state.get("platform_type") or submit.get("platform_type"),
            "publish_runtime": submit.get("publish_runtime"),
            "title": state.get("title"),
            "account_list": list(state.get("account_list") or []),
            "data_source": {"source": "mcp", "tool": "social_publish_submit"},
        }
        return {"report_draft": draft, "finalize": draft}, 0.2, True

    last: dict[str, Any] = {}
    terminal = {"success", "failed"}
    poll_rounds = 40
    poll_interval_s = 15
    for _ in range(poll_rounds):
        result = mcp_runtime.invoke_logical(
            "social_publish_status",
            {"job_id": job_id},
        )
        if not result.ok:
            last = {
                "ok": False,
                "status": "failed",
                "error": result.error or "状态查询失败",
                "job_id": job_id,
            }
            break
        data = dict(result.data or {})
        last = data
        status = (data.get("status") or "").lower()
        if status in terminal:
            break
        time.sleep(poll_interval_s)

    status = (last.get("status") or "unknown").lower()
    ok = status == "success"
    msg = last.get("error") or last.get("message") or status
    if status in ("pending", "running"):
        msg = f"仍在处理中（已单步轮询结束）：{msg}"
        ok = False

    draft = {
        "kind": "social_publish",
        "ok": ok,
        "status": status if status in ("pending", "running", "success", "failed") else "unknown",
        "message": str(msg),
        "job_id": last.get("job_id") or job_id,
        "platform_type": state.get("platform_type")
        or last.get("platform_type")
        or submit.get("platform_type"),
        "publish_runtime": last.get("runtime") or submit.get("publish_runtime"),
        "title": state.get("title") or submit.get("title"),
        "account_list": list(state.get("account_list") or submit.get("account_list") or []),
        "data_source": {"source": "mcp", "tool": "social_publish_status"},
    }
    hard_fail = status == "failed" or (last.get("ok") is False)
    if ok:
        quality = 0.95
    elif status in ("pending", "running"):
        quality = 0.9
    else:
        quality = 0.25
    return {"report_draft": draft, "finalize": draft}, quality, hard_fail


def handle_expand_llm(
    state: AgentState, collected: dict[str, Any]
) -> tuple[dict[str, Any], float, bool]:
    """Light LLM expand from collect keywords (accepts session model_id)."""
    seed = state.get("seed") or "渔具"
    collect = collected.get("collect") or {}
    base = [x.get("word") for x in (collect.get("keywords") or []) if isinstance(x, dict) and x.get("word")]
    base = list(dict.fromkeys(base))[:25]
    suggest: list[str] = []
    try:
        from agent.llm import get_chat_model_for_state
        from langchain_core.messages import HumanMessage, SystemMessage
        import json
        import re

        llm = get_chat_model_for_state(state, task="fact_extract")
        prompt = (
            f"种子词：{seed}\n"
            f"已采集词：{', '.join(base) if base else '（无）'}\n\n"
            "请扩展 8～15 个抖音运营可用的联想词（标题/话题/挂车向），"
            "输出 JSON：{\"suggest_words\":[\"..\"]}，不要 markdown。"
        )
        resp = llm.invoke(
            [
                SystemMessage(content="你是抖音选品运营助手，只输出 JSON。"),
                HumanMessage(content=prompt),
            ]
        )
        text = getattr(resp, "content", None) or str(resp)
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group(0))
            suggest = [str(w).strip() for w in (data.get("suggest_words") or []) if str(w).strip()]
    except Exception:
        suggest = []

    if not suggest:
        # Fallback: rule expand (still real-collect first)
        from agent.tools import douyin_stub

        suggest = list(douyin_stub.expand_suggest_words(seed, depth=2).get("suggest_words") or [])

    suggest = [w for w in suggest if w and w != seed][:15]
    return (
        {
            "expand": {
                "ok": True,
                "seed": seed,
                "suggest_words": suggest,
                "count": len(suggest),
                "source": "llm" if suggest else "fallback",
            }
        },
        0.85 if suggest else 0.4,
        False,
    )


STEP_HANDLERS: dict[str, Handler] = {
    "analyze": handle_analyze,
    "score": handle_score,
    "expand_llm": handle_expand_llm,
    "report_douyin": handle_report_douyin,
    "finalize_temu_listing": handle_finalize_temu_listing,
    "finalize_social_publish": handle_finalize_social_publish,
}


def run_step_action(
    action: str, state: AgentState, collected: dict[str, Any]
) -> tuple[dict[str, Any], float, bool]:
    handler = STEP_HANDLERS.get(action)
    if not handler:
        return {state.get("current_step", "unknown"): {"status": "skipped"}}, 0.5, False
    return handler(state, collected)
