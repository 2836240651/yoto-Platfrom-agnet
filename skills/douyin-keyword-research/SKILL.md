---
name: douyin-keyword-research
description: 分析抖音种子词下的视频热搜词、潜力词、商品热搜词和潜力词
triggers:
  - 抖音热搜
  - 潜力词
  - 渔具关键词
mcp_servers:
  - douyin_data
tools:
  - douyin_collect_hot_keywords
  - douyin_analyze_keywords
---

# 抖音关键词研究

## 工作流（强制分工）

1. **采集（MCP only）** — `douyin_collect_hot_keywords(seed)`  
   蝉妈妈个人版登录态拉取原始关联/热词。**不做成败以外的业务分析。**
2. **分析（LLM tool）** — action `analyze` → `douyin_analyze_keywords`  
   - 分析：热搜/潜力 × 视频/商品四栏 + 理由/行动建议（heavy）  
   - 优化：去重、删弱相关、强化可执行 action（再一轮 LLM）  
3. **报告** — 组装 `kind=douyin_keyword` 交付页

## 登录

```bat
python scripts\chanmama_login.py
```

Profile：`DOUYIN_CHROME_USER_DATA_DIR` 或默认 `.local/chanmama-chrome`（不入库）。

## 运营界面参数

| 参数 | 类型 | 说明 |
|------|------|------|
| seed | string | 种子词，如「渔具」 |
| include_video | bool | 分析视频侧词 |
| include_product | bool | 分析商品侧词 |
| model_id | string? | 可选会话模型钉扎（分析步生效） |

## Exact-query Diagnostic Policy (mandatory)

- Call `douyin_collect_hot_keywords` with the exact seed first. Do not silently substitute broad terms such as fishing or tackle.
- Read `status` and `diagnostics` before analysis. `no_data` must be reported truthfully with its diagnostic counts; `upstream_error` and `parse_error` require investigation, never generated keywords. An `errCode` such as `55006` is an upstream observation, not proof that a broad seed permanently has no data; retain the HTTP status, raw count, parsed count, and timestamp before concluding.
- Only send expansion terms through an explicit `query_plan`; every item needs `term`, `source`, and `query_dimension`. Preserve `queried_term`, `query_level`, `query_source`, and `query_dimension` in all downstream reasoning, diagnostics, and reports.
- Never present an expansion result as evidence for the original seed.
- Default to the exact seed. For a niche seed that has an explicit upstream expansion decision, `query_plan` may contain at most 2 narrow variants. Each variant must preserve the seed's technical qualifier and add only a use-case or form qualifier (for example, `反底钓` → `反底钓法` / `反底钓线组`).
- Do not remove or generalize the seed's technical qualifier. In particular, do not expand a niche query into broad category terms such as `钓鱼、渔具、鱼竿`, and do not create bridge seeds inside the collection black box.
- Label every expansion-derived card with its `queried_term`, source, and dimension. Do not present expansion results as the original seed's measured result.
- When operations need to verify browser automation, use the meat worker's authorized **有头浏览器** mode for one real collection task and record only page URL/title, HTTP status, errCode, raw count, and parsed count. Never expose Cookie or Token.
