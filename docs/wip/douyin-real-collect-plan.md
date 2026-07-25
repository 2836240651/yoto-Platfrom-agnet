# 抖音真实采集 · 两日冲刺计划

> 状态：执行中 · 2026-07-24  
> 目标：种子词 → 蝉妈妈个人版真实采集 → 视频/商品 热词+潜力词报告

## 工作流（强制分工）

1. **采集 MCP only** — `douyin_collect_hot_keywords`
2. **分析 LLM tool** — `douyin_analyze_keywords`（analyze → optimize）
3. **报告** — `kind=douyin_keyword`

详见 Skill / `src/agent/tools/douyin_analyze.py`。


## 采集源（已关闭）

蝉妈妈**个人版 Cookie + Playwright 持久化 profile**（非官方 OpenAPI）。

## 环境

| 键 | 含义 |
|----|------|
| `DOUYIN_CHROME_USER_DATA_DIR` | Chrome/Chromium user data（默认 `.local/chanmama-chrome`） |
| `CHANMAMA_STORAGE_STATE` | 可选 storage_state.json（与 profile 二选一优先 profile） |

Cookie **禁止**入库 / 进 git。

## MCP

- Server：`douyin_data`（本地 stdio；**生产/肉机改 streamable-http**）
- Tool：`douyin_collect_hot_keywords(seed, …)`
- 未登录：`ok=false, need_login=true`
- 未收录细分词：`seed_mode=bridge` + 父词采集
- 肉机部署：`docs/wip/douyin-meat-machine-mcp.md`

## 阻塞

| ID | 状态 |
|----|------|
| B5 登录态 | 本地已登录；生产改肉机 profile |
| B2 Schema | 已补 `skills/douyin-keyword-research/schema/` |
| B3 | collect 真 + 桥接父词；score LLM 精炼细分词 |
