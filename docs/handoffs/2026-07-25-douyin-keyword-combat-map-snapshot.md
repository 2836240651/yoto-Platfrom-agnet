# 抖音关键词作战图 · 会话快照

> 日期：2026-07-25
> 用途：跨会话继续设计/实施时的事实基线；不是新的权威产品 Spec。
> 关联 Spec：[`docs/wip/douyin-keyword-combat-map-spec.md`](../wip/douyin-keyword-combat-map-spec.md)
> 关联 Spike：[`docs/wip/douyin-mcp-return-spike-2026-07-25.md`](../wip/douyin-mcp-return-spike-2026-07-25.md)

## 已确认的目标

工具定位为“抖音渔具选词与打法参谋”：运营输入一个种子词，工具利用真实平台数据回答赛道位置、视频和商品应分别押什么词、本周先测什么、应避开什么坑。

报告应是作战图，而不是词表：核心打法、市场现状、视频/商品四栏词卡、本周优先测试和风险。店铺背靠渔具工厂只是广供给和测试能力，不得替代具体 SKU、授权、库存、材质或合规事实。

## 已确认的工程现状

- 代码基线提交：`fe5b9ba`。
- 主链路已存在：Skill `collect → analyze → report`；采集经 `platform_mcp`，分析在本仓 `src/agent/tools/douyin_analyze.py`，报告组装在 `src/agent/tools/step_handlers.py`。
- MCP 工具 `douyin_collect_hot_keywords` 已线上注册，公开入参为 `seed`、`date_range_days`、`include_video`、`include_product`。
- `douyin_chanmama_auth_status` 显示至少一台肉机在线且登录；未读取或记录 Cookie、Token 等敏感信息。
- 当前分析和报告仍是最小四栏词卡契约；`store_context`、策略摘要、测试清单、排除项等尚未进入 API、任务、报告和前端的端到端契约。

## MCP Spike 事实

- 线上 MCP 初始化与 `tools/list` 已成功。
- 使用 `大物竿` 和 `渔具` 各做一次 7 天、视频/商品双侧真实采集。
- 两次任务均到达已登录肉机，但都以“relationWord 无相关关联词”结束，`need_login=false`；未得到成功载荷。
- 因此，不能把“当前 relationWord 为空”解释为“抖音不存在相关视频/商品需求”；它只证明该采集入口当前没有返回词。
- 源码声明采集内部可抽取 `word`、`hot_level`、`compete_index`、`side`、`bucket`；但目前 `keywords` 与四栏数组会丢失 `compete_index`，分析层也只保留 `word/hot_level/side/bucket`。
- rank、rank_change、trend、逐词来源引用没有成功线上样本，也未在当前源码契约中稳定产生；禁止在报告中伪造这些结论。

## 本轮最重要的架构结论

问题不只是 LLM 幻觉，而是**上游数据语义污染**：若种子词没有数据，MCP 不能自动回退到“渔具”等父类目并把结果伪装成种子词相关数据。即使 LLM 完全不编造，也会在错误数据上得到错误策略。

正确链路应调整为：

```text
种子词
  → 轻量 LLM 生成受控查询计划
  → 单个 MCP Job 按计划采集并保留查询血缘
  → 本仓校验结果边界
  → LLM 输出四栏作战图
```

受控查询顺序：精确词 → 写法变体 → 同结构规格 → 同需求场景 → 同结构相邻词。父类目只能作为 `market_context`，不得自动替代种子词或混入四栏主池。

## 应加入 MCP 结果契约的字段

```json
{
  "coverage_state": "exact_hit|expanded_hit|coverage_gap|market_weak|parent_only",
  "attempts": [
    {
      "term": "大物竿",
      "level": "exact|variant|spec|scene|parent_context",
      "route": "relation_word|video_search|product_search|topic",
      "result_count": 0
    }
  ],
  "validated_candidates": [],
  "market_context": [],
  "fallback_used": false
}
```

规则：精确词和强相关扩词均无结果时返回 `coverage_gap`；只有父类目命中时返回 `parent_only`，只可写大盘背景。海竿、路亚竿等结构冲突词必须作为 `diversion_risk`，不得混链。

## 后续顺序

1. 先修订作战图 Spec，纳入“受控扩词、查询血缘、coverage_state、父类目隔离”这一 MCP 契约。
2. 对 relationWord 的页面/请求参数/原始返回做针对性采集诊断，取得一个成功样本；不要用 LLM 词表伪装成真实 MCP 数据。
3. 以成功样本确认哪些字段可用后，实施 MCP 证据保留、`douyin_analyze.py` 重新分栏、报告/API/前端契约和测试。
4. 文档改动目前尚未提交；凭证临时脚本和桌面端解包产物必须继续保持不提交。
