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
  - douyin_expand_suggest_words
  - douyin_search_products
---

# 抖音关键词研究

## 工作流

1. **采集** — `douyin_collect_hot_keywords(seed)`
2. **扩展** — `douyin_expand_suggest_words(seed, depth=2)`
3. **打分** — 规则 + LLM 语义过滤
4. **报告** — 固定表格输出

## 分类规则

- **热搜词**: hot_level 高或 Top 20%
- **潜力词**: 标签为新/上升，或周环比增速 > 30%
- **商品词**: 来自电商搜索，带销量字段

## 运营界面参数

| 参数 | 类型 | 说明 |
|------|------|------|
| seed | string | 种子词，如「渔具」 |
| include_video | bool | 分析视频侧词 |
| include_product | bool | 分析商品侧词 |
