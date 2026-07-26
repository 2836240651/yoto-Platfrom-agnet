"""Douyin keyword analysis tool — LLM-only (MCP does collect only).

Flow: summarize collect → analyze (heavy) → optimize (heavy) → report-shaped score.
Never send full raw MCP payloads; keep a compact keyword table in context.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agent.state import AgentState

_BUCKETS = ("video_hot", "video_potential", "product_hot", "product_potential")

_DOUYIN_ANALYSIS_SYSTEM_PROMPT = (
    "你是跨境电商抖音选品与内容运营专家。只输出合法 JSON。"
    "只可基于输入的采集词生成分析；视频侧与商品侧严格分栏，分析要具体可执行。"
    "不得将 no_data、upstream_error 或 parse_error 转成关键词建议，也不得补造未采集词。"
    "必须尊重 queried_term、query_level、query_source、query_dimension；显式 query_plan 的扩词不得表述为原种子词的实测结果。"
)


def format_heat(n: int | float | None) -> str:
    """Human-readable Chanmama heat index (never a lone dash)."""
    try:
        v = int(n or 0)
    except (TypeError, ValueError):
        v = 0
    if v <= 0:
        return "暂无指数"
    if v < 10_000:
        return str(v)
    if v < 100_000_000:
        s = f"{v / 10_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}万"
    s = f"{v / 100_000_000:.2f}".rstrip("0").rstrip(".")
    return f"{s}亿"


def _compact_collect(collect: dict[str, Any], *, limit: int = 80) -> list[dict[str, Any]]:
    lineage: dict[tuple[str, str], dict[str, str]] = {}
    for item in collect.get("keywords") or []:
        if not isinstance(item, dict):
            continue
        word = str(item.get("word") or item.get("keyword") or "").strip()
        side = str(item.get("side") or "").strip()
        if not word or side not in ("video", "product"):
            continue
        values = {
            key: str(item.get(key) or "").strip()
            for key in ("queried_term", "query_level", "query_source", "query_dimension")
            if str(item.get(key) or "").strip()
        }
        if values:
            lineage[(side, word)] = values

    rows: list[dict[str, Any]] = []
    for side, buckets in (
        ("video", ("video_hot", "video_potential")),
        ("product", ("product_hot", "product_potential")),
    ):
        for bucket_key in buckets:
            layer = "hot" if bucket_key.endswith("_hot") else "potential"
            for item in collect.get(bucket_key) or []:
                if isinstance(item, str):
                    word, hot = item.strip(), 0
                elif isinstance(item, dict):
                    word = str(item.get("word") or item.get("keyword") or "").strip()
                    hot = int(item.get("hot_level") or 0)
                else:
                    continue
                if word:
                    row = {"word": word, "hot_level": hot, "side": side, "bucket": layer}
                    row.update(lineage.get((side, word), {}))
                    rows.append(row)

    if not rows:
        for item in collect.get("keywords") or []:
            if not isinstance(item, dict):
                continue
            word = str(item.get("word") or item.get("keyword") or "").strip()
            if not word:
                continue
            side = str(item.get("side") or "video").strip()
            if side not in ("video", "product"):
                side = "video"
            bucket = str(item.get("bucket") or "hot").strip()
            if bucket not in ("hot", "potential"):
                bucket = "hot"
            row = {
                "word": word,
                "hot_level": int(item.get("hot_level") or 0),
                "side": side,
                "bucket": bucket,
            }
            row.update(lineage.get((side, word), {}))
            rows.append(row)

    best: dict[tuple[str, str], dict[str, Any]] = {}
    for r in rows:
        key = (str(r["side"]), str(r["word"]))
        prev = best.get(key)
        if not prev or int(r.get("hot_level") or 0) > int(prev.get("hot_level") or 0):
            best[key] = r
    out = list(best.values())
    out.sort(key=lambda x: -int(x.get("hot_level") or 0))
    return out[:limit]


def _parse_json_obj(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _response_text(content: Any) -> str:
    """Extract text from LangChain string or Responses API content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return _response_text(content.get("text") or content.get("content"))
    if isinstance(content, list):
        return "\n".join(
            text for item in content if (text := _response_text(item)).strip()
        )
    return ""


def _side_label(side: str) -> str:
    return "商品带货" if side == "product" else "视频内容"


def _layer_label(bucket: str) -> str:
    return "潜力" if "potential" in bucket else "热搜"


def build_card_metrics(*, hot: int, side: str, bucket: str) -> list[dict[str, str]]:
    return [
        {"label": "蝉妈妈热度", "value": format_heat(hot)},
        {"label": "侧别", "value": _side_label(side)},
        {"label": "分层", "value": _layer_label(bucket)},
    ]


def _card(
    seed: str,
    word: str,
    *,
    priority: str,
    reason: str,
    action: str,
    hot: int = 0,
    side: str = "video",
    bucket: str = "video_hot",
    evidence: list[str] | None = None,
    lineage: dict[str, str] | None = None,
) -> dict:
    side_s = "product" if side == "product" or bucket.startswith("product") else "video"
    ev = evidence or [
        f"采集侧别：{_side_label(side_s)}",
        f"蝉妈妈热度：{format_heat(hot)}",
        "LLM 运营分析",
    ]
    card = {
        "keyword": word,
        "priority": priority if priority in ("P0", "P1", "P2") else "P1",
        "trend": "up" if hot > 0 else "flat",
        "reason": reason or f"与「{seed}」相关，适合作为{_side_label(side_s)}测试词。",
        "metrics": build_card_metrics(hot=hot, side=side_s, bucket=bucket),
        "evidence": ev[:4],
        "action": action
        or f"围绕「{word}」做一条可复盘的{_side_label(side_s)}测试（记录完播/点击）。",
    }
    if lineage:
        card.update(lineage)
    return card


def _heat_maps(rows: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, str], dict[str, dict[str, str]]]:
    heat: dict[str, int] = {}
    side_of: dict[str, str] = {}
    lineage: dict[str, dict[str, str]] = {}
    for r in rows:
        w = str(r.get("word") or "")
        if not w:
            continue
        h = int(r.get("hot_level") or 0)
        if h >= heat.get(w, -1):
            heat[w] = h
            side_of[w] = str(r.get("side") or "video")
            lineage[w] = {
                key: str(r.get(key) or "")
                for key in ("queried_term", "query_level", "query_source", "query_dimension")
            }
    return heat, side_of, lineage


def _allowed_words(rows: list[dict[str, Any]], side: str) -> set[str]:
    return {str(r["word"]) for r in rows if r.get("side") == side and r.get("word")}


def _resolve_collected_word(word: str, allowed: set[str]) -> str:
    """Resolve an LLM-shortened title only to a same-side collected title."""
    if word in allowed:
        return word
    compact = "".join(char for char in word if char.isalnum())
    if len(compact) < 4:
        return ""
    matches = [
        candidate
        for candidate in allowed
        if compact in "".join(char for char in candidate if char.isalnum())
    ]
    return min(matches, key=lambda candidate: (len(candidate), candidate)) if matches else ""


def _normalize_categories(
    seed: str,
    raw: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    include_video: bool,
    include_product: bool,
) -> dict[str, list[dict]]:
    heat, side_of, lineage_by_word = _heat_maps(rows)
    video_ok = _allowed_words(rows, "video")
    product_ok = _allowed_words(rows, "product")
    cats: dict[str, list[dict]] = {k: [] for k in _BUCKETS}

    for bucket in _BUCKETS:
        want_side = "video" if bucket.startswith("video") else "product"
        allow = video_ok if want_side == "video" else product_ok
        items = raw.get(bucket) or []
        if not isinstance(items, list):
            continue
        for i, item in enumerate(items[:12]):
            evidence: list[str] | None = None
            if isinstance(item, str):
                word, reason, action = item, "", ""
                pr = "P0" if i < 2 else "P1" if i < 5 else "P2"
            elif isinstance(item, dict):
                word = str(item.get("keyword") or item.get("word") or "").strip()
                reason = str(item.get("reason") or "").strip()
                action = str(item.get("action") or "").strip()
                pr = str(item.get("priority") or ("P0" if i < 2 else "P1" if i < 5 else "P2"))
                ev_raw = item.get("evidence")
                if isinstance(ev_raw, list):
                    evidence = [str(x) for x in ev_raw if str(x).strip()][:3]
            else:
                continue
            if not word:
                continue
            word = _resolve_collected_word(word, allow)
            if not word:
                continue
            known = side_of.get(word)
            if known and known != want_side:
                continue
            if allow and word not in allow:
                continue
            if want_side == "video" and not include_video:
                continue
            if want_side == "product" and not include_product:
                continue
            cats[bucket].append(
                _card(
                    seed,
                    word,
                    priority=pr,
                    reason=reason,
                    action=action,
                    hot=heat.get(word, 0),
                    side=want_side,
                    bucket=bucket,
                    evidence=evidence,
                    lineage=lineage_by_word.get(word),
                )
            )
    return cats


def _llm_json(state: AgentState, *, task: str, system: str, user: str) -> dict[str, Any] | None:
    from agent.llm import get_chat_model_for_state
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_chat_model_for_state(state, task=task)
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    text = _response_text(getattr(resp, "content", None)) or str(resp)
    return _parse_json_obj(text)


def _split_rows(rows: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    return (
        [r for r in rows if r.get("side") == "video"],
        [r for r in rows if r.get("side") == "product"],
    )


def _rule_fallback_categories(
    seed: str,
    rows: list[dict[str, Any]],
    *,
    include_video: bool,
    include_product: bool,
) -> dict[str, list[dict]]:
    """Build deterministic cards from this run's MCP rows without changing side."""
    categories: dict[str, list[dict]] = {key: [] for key in _BUCKETS}
    enabled = {"video": include_video, "product": include_product}
    side_indexes = {"video": 0, "product": 0}

    for row in rows:
        side = str(row.get("side") or "")
        if side not in enabled or not enabled[side]:
            continue
        bucket = str(row.get("bucket") or "hot")
        bucket_key = f"{side}_{bucket}"
        if bucket_key not in categories or len(categories[bucket_key]) >= 12:
            continue

        word = str(row.get("word") or "").strip()
        if not word:
            continue
        index = side_indexes[side]
        priority = "P0" if index == 0 else "P1" if index < 5 else "P2"
        side_indexes[side] = index + 1
        hot = int(row.get("hot_level") or 0)
        categories[bucket_key].append(
            _card(
                seed,
                word,
                priority=priority,
                reason=(
                    f"本次蝉妈妈{_side_label(side)}采集热度 {format_heat(hot)}；"
                    f"与「{seed}」同次查询返回，适合先做验证。"
                ),
                action=(
                    f"围绕「{word}」做一条{_side_label(side)}测试，"
                    "记录曝光、点击和转化后再决定是否放量。"
                ),
                hot=hot,
                side=side,
                bucket=bucket_key,
                evidence=[
                    f"采集侧别：{_side_label(side)}",
                    f"蝉妈妈热度：{format_heat(hot)}",
                    "LLM 深度分析待重试；该词仅作为本次 MCP 原始采集证据保留。",
                ],
            )
        )
    return categories


def analyze_and_optimize(
    state: AgentState,
    collect: dict[str, Any],
) -> dict[str, Any]:
    """Analysis tool entry: LLM analyze then optimize. Returns score-shaped payload."""
    seed = state.get("seed") or collect.get("seed") or "渔具"
    include_video = bool(state.get("include_video", True))
    include_product = bool(state.get("include_product", True))
    rows = _compact_collect(collect)
    source = (
        (collect.get("_meta") or {}).get("source")
        or (collect.get("data_source") or {}).get("source")
        or "stub"
    )
    video_rows, product_rows = _split_rows(rows)
    kb_context = [item for item in (state.get("kb_context") or []) if isinstance(item, dict)]

    if not rows:
        return {
            "ok": False,
            "error": "采集结果为空，无法分析",
            "categories": {k: [] for k in _BUCKETS},
            "summary": {
                "keyword_count": 0,
                "video_sample_count": 0,
                "product_sku_count": 0,
                "p0_count": 0,
            },
            "tags": [f"种子词：{seed}", "数据源：空采集"],
            "alerts": [{"type": "warn", "text": "无采集词，请检查蝉妈妈登录态或换种子词重试。"}],
            "data_source": {"source": source, "tool": "douyin_analyze_keywords"},
        }

    bridge_note = ""
    if collect.get("seed_mode") == "bridge":
        bridges = "、".join(collect.get("bridges_used") or []) or "父词"
        bridge_note = (
            f"采集为桥接模式（桥接词：{bridges}），分析须紧扣种子「{seed}」，删掉无关大盘词。\n"
        )

    analyze_prompt = (
        f"种子词：{seed}\n"
        f"{bridge_note}"
        f"【渔具知识库命中】（仅用于理解别名/品类，不得把它补造成未采集词）：\n"
        f"{json.dumps(kb_context, ensure_ascii=False)}\n\n"
        f"需要视频侧：{include_video}；需要商品侧：{include_product}\n\n"
        f"【视频侧采集词】（只可进入 video_* 栏）：\n"
        f"{json.dumps(video_rows, ensure_ascii=False)}\n\n"
        f"【商品侧采集词】（只可进入 product_* 栏）：\n"
        f"{json.dumps(product_rows, ensure_ascii=False)}\n\n"
        "任务：做抖音「视频内容」与「商品带货」双侧运营深分析。"
        "严禁编造未出现的词；严禁视频词进商品栏、商品词进视频栏。\n"
        "每个输入词携带 queried_term、query_level、query_source、query_dimension 查询血缘；不得丢弃、替换，"
        "也不得把显式扩词的结果写成原种子词的实测结果。\n"
        "输出 JSON（不要 markdown）：\n"
        "{\n"
        '  "video_hot":[{"keyword":"..","priority":"P0|P1|P2","reason":"..","action":"..","evidence":[".."]}],\n'
        '  "video_potential":[...],\n'
        '  "product_hot":[...],\n'
        '  "product_potential":[...],\n'
        '  "strategy":"视频打法 vs 商品打法（各2～4句）",\n'
        '  "p0_focus":"本周优先测的3个词及理由",\n'
        '  "risks":"大盘词/弱相关/桥接偏差等风险",\n'
        '  "insight":"一句话总判断"\n'
        "}\n"
        "词卡写作硬性要求：\n"
        "- reason：2～4 句，必须含「为何热或为何潜力 + 与种子词关系 + 人群/场景」；\n"
        "- action：可执行（标题句式 / 话题标签 / 挂车卖点），禁止空泛「建议测试 #词」；\n"
        "- evidence：1～3 条短证据；\n"
        "- 视频栏偏话题/玩法/内容结构；商品栏偏规格/配件/可挂车卖点；\n"
        "- 每栏 4～8 个；每栏至少 1 个 P0（若该侧有词）。\n"
    )

    analyzed = None
    analyze_err = None
    try:
        analyzed = _llm_json(
            state,
            task="ops_analysis",
            system=_DOUYIN_ANALYSIS_SYSTEM_PROMPT,
            user=analyze_prompt,
        )
    except Exception as exc:  # noqa: BLE001
        analyzed = None
        analyze_err = str(exc)

    if not analyzed:
        categories = _rule_fallback_categories(
            seed,
            rows,
            include_video=include_video,
            include_product=include_product,
        )
        all_cards = sum(categories.values(), [])
        p0_count = sum(1 for card in all_cards if card.get("priority") == "P0")
        return {
            "ok": False,
            "status": "analysis_unavailable",
            "error": f"LLM 深度分析未完成：{analyze_err or 'parse empty'}",
            "categories": categories,
            "summary": {
                "keyword_count": len(all_cards),
                "video_sample_count": len(categories["video_hot"]) + len(categories["video_potential"]),
                "product_sku_count": len(categories["product_hot"]) + len(categories["product_potential"]),
                "p0_count": p0_count,
            },
            "tags": [
                f"种子词：{seed}",
                "分析：待重试",
                "数据源：真实 MCP" if source == "mcp" else f"数据源：{source}",
            ],
            "alerts": [
                {
                    "type": "warn",
                    "text": f"LLM 深度分析未完成，已保留本次 MCP 原始词与侧别，等待模型恢复后重试：{analyze_err or 'parse empty'}",
                }
            ],
            "data_source": {
                "source": source,
                "tool": "douyin_analyze_keywords",
                "provider": "chanmama" if source == "mcp" else None,
                "mode": "analysis_unavailable",
            },
        }

    optimize_prompt = (
        f"种子词：{seed}\n"
        f"视频采集词：{[r['word'] for r in video_rows]}\n"
        f"商品采集词：{[r['word'] for r in product_rows]}\n"
        f"初稿：\n{json.dumps(analyzed, ensure_ascii=False)}\n\n"
        "你是抖音运营主编。请审稿优化并只输出同一 JSON schema：\n"
        "- 纠正侧别串栏；删除与种子弱相关的大盘词；\n"
        "- 拉长并具体化 reason/action；保证四栏（按开关）非空且互不撞车；\n"
        "- 强化 strategy / p0_focus / risks，使其可直接给运营执行。\n"
    )
    optimized = None
    try:
        optimized = _llm_json(
            state,
            task="ops_analysis",
            system="你是抖音运营主编。只输出合法 JSON，侧重可执行与分侧正确。",
            user=optimize_prompt,
        )
    except Exception:
        optimized = None

    final = optimized or analyzed
    categories = _normalize_categories(
        seed,
        final,
        rows,
        include_video=include_video,
        include_product=include_product,
    )
    if not include_video:
        categories["video_hot"] = []
        categories["video_potential"] = []
    if not include_product:
        categories["product_hot"] = []
        categories["product_potential"] = []

    all_cards = sum((categories[k] for k in _BUCKETS), [])
    p0 = sum(1 for c in all_cards if c.get("priority") == "P0")

    clean_alerts: list[dict[str, str]] = []
    for key, typ, prefix in (
        ("strategy", "info", "策略"),
        ("p0_focus", "info", "本周优先"),
        ("risks", "warn", "风险"),
        ("insight", "info", "判断"),
    ):
        text = str(final.get(key) or "").strip()
        if text:
            clean_alerts.append({"type": typ, "text": f"【{prefix}】{text}"})
    for a in final.get("alerts") or []:
        if isinstance(a, dict) and a.get("text"):
            t = str(a["text"])
            if any(t in (x.get("text") or "") for x in clean_alerts):
                continue
            clean_alerts.append(
                {"type": "warn" if a.get("type") == "warn" else "info", "text": t}
            )

    tags = [
        f"种子词：{seed}",
        "分析：LLM",
        "数据源：蝉妈妈" if source == "mcp" else f"数据源：{source}",
    ]
    if collect.get("seed_mode") == "bridge":
        tags.append("模式：桥接父词")
        bridges = "、".join(collect.get("bridges_used") or []) or "父词"
        clean_alerts.insert(
            0,
            {"type": "info", "text": f"采集经桥接词（{bridges}），分析已按「{seed}」相关性优化。"},
        )
    elif source == "mcp":
        clean_alerts.insert(
            0, {"type": "info", "text": "采集来自蝉妈妈；视频/商品分侧与建议由 LLM 生成。"}
        )

    return {
        "ok": bool(all_cards),
        "categories": categories,
        "summary": {
            "keyword_count": len(all_cards),
            "video_sample_count": len(categories["video_hot"]) + len(categories["video_potential"]),
            "product_sku_count": len(categories["product_hot"]) + len(categories["product_potential"]),
            "p0_count": max(p0, 1 if all_cards else 0),
        },
        "tags": tags,
        "alerts": clean_alerts,
        "data_source": {
            "source": source,
            "tool": "douyin_analyze_keywords",
            "provider": "chanmama" if source == "mcp" else None,
            "mode": "llm_optimize" if optimized else "llm_analyze",
        },
    }
