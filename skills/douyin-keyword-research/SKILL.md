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
