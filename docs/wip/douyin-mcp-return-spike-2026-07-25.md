# 抖音 MCP 返回字段核对 Spike

> 日期：2026-07-25
> 状态：已完成，只读核对；未修改业务代码
> 目的：确定“作战图”实施前可依赖的真实 MCP 字段，区分源码声明与线上成功验证。

## 结论

1. 线上 `platform_mcp` 可协商，版本为 `1.28.1`；`douyin_collect_hot_keywords` 已注册。
2. 一台肉机在线且蝉妈妈登录态有效；本次没有读取或记录 Cookie、Token、昵称等敏感信息。
3. 对 `大物竿` 与 `渔具` 各执行一次 7 天、视频与商品双侧的真实采集。两次任务均已到达肉机，但均返回“无相关关联词”，没有成功载荷。
4. 因没有线上成功样本，成功返回字段只能标为“源码声明”，不能标为“线上已验证”。
5. 源码表明采集端可识别 `compete_index`，但当前对外 `keywords` 与四栏数组会丢弃该字段；分析层也只保留 `word/hot_level/side/bucket`。这是下一阶段必须修复的数据损失点。

## 线上只读证据

| 项目 | 结果 |
|---|---|
| `GET /platform-mcp/mcp` | `406`，符合 MCP 协商端点预期。 |
| MCP `initialize` | `200`，返回 SSE 与有效 `Mcp-Session-Id`。 |
| MCP `tools/list` | 存在 `douyin_collect_hot_keywords` 与 `douyin_chanmama_auth_status`。 |
| `douyin_chanmama_auth_status` | 至少一台肉机 `online=true`、`logged_in=true`。 |
| 真采 1 | 种子词 `大物竿`；`ok=false`、`need_login=false`、错误为 relationWord 无相关关联词。 |
| 真采 2 | 种子词 `渔具`；`ok=false`、`need_login=false`、错误为 relationWord 无相关关联词。 |

两次失败证明当前问题不是登录态缺失，也不应伪装为成功报告；它们不证明任何热度、排名或趋势字段可用。

## 工具公开入参：线上已验证

```json
{
  "seed": "string, required",
  "date_range_days": "integer, default 30",
  "include_video": "boolean, default true",
  "include_product": "boolean, default true"
}
```

`store_context` 不属于 MCP 采集入参；它应留在本仓的 Skill/API/任务输入层，仅供 LLM 归类、挂车边界和报告策略使用。

## 成功返回字段：源码声明

`mcp/servers/douyin_chanmama_client.py` 的抽取行可得到：

```json
{
  "word": "string",
  "hot_level": "integer",
  "compete_index": "number|null",
  "side": "video|product",
  "bucket": "hot|potential"
}
```

当前返回结构包括 `seed`、`seed_mode`、`bridges_used`、`date_range_days`、`keywords`、`count`、四栏数组、`auth`、`traces`、`errors`、`data_source` 与 `error`。

但 `keywords` 目前仅透传 `word/hot_level/side/bucket/bridge`；四栏数组仅透传 `word/hot_level`。因此：

- `compete_index` 已在采集端抽取，但未进入分析输入；
- 排名、排名变化、趋势、逐词来源引用未在当前源码契约中产生；
- `bucket` 在采集端由热度与竞争度的启发式规则生成，只能视为采集特征，不是作战图最终分栏结论。

## 后续实施约束

1. 在 `douyin_chanmama_client.py` 中让成功 `keywords` 保留 `compete_index`，并保留原始字段/来源的可选引用；不能凭空新增 rank 或 trend。
2. 在 `douyin_analyze.py` 中将 `compete_index` 和 `bridge` 保留到紧凑分析行；最终热搜/潜力分栏必须由词性、种子关系、侧别、证据和商品目录共同决定。
3. 线上成功样本取得前，报告只能展示热度和竞争度（若存在）；趋势、排名及“上涨/红海”结论必须输出“需补数”。
4. 下次真采应先检查 relationWord 页面/接口的请求参数与返回原文，定位为什么宽种子词仍无关联词；不得以 LLM 词表补充为“真实 MCP 数据”。
