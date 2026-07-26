# 抖音词分析作战图 Spec

> 状态：WIP · 2026-07-25
> Skill：`douyin-keyword-research`
> 代码基线：`fe5b9ba`
> 权威约束：`docs/spec-architecture-contract.md`、`docs/wip/spec-business-scenarios-llm-tool.md` §3

## 目标

输入一个抖音渔具种子词，例如“大物竿”。基于蝉妈妈 MCP 的真实视频侧和商品侧数据，输出可执行的选词和打法作战图：赛道现状、视频/带货各自应押的词、本周优先测试和必须避开的风险。

该能力是运营参谋，不是百科、脚本库或选品决策替代品。店铺背靠全品类渔具工厂，只代表可测试供给范围较广；不代表某个 SKU、库存、材质、认证、品牌授权或商品结构已确认。商品目录外的结论不得写成“可直接挂车”。

## 现状基线

| 层级 | 已验证代码现状 | 结论 |
|---|---|---|
| 工作流 | `collect → analyze → report` 已在 Skill 与 `SKILL_PLANS` 中注册 | 无需重建主流程。 |
| 采集 | `douyin_collect_hot_keywords` 经 `platform_mcp`、网关队列和肉机 Playwright 执行 | 外部数据只能经 MCP；本次未实盘验证登录态。 |
| 数据源 | 采集补充 `data_source.source=mcp`、`provider=chanmama` | 真实 MCP 仅说明数据来源，不代表策略正确。 |
| 分析 | `douyin_analyze.py` 压缩为 `word/hot_level/side/bucket` 后再做 LLM 分析 | 现有压缩会丢失排名、趋势、竞争度和逐词来源。 |
| 报告 | `handle_report_douyin` 仅透传 `summary/tags/alerts/categories/data_source` | 策略、测试和风险字段会丢失。 |
| Schema/前端 | 输入只有种子词、侧别、周期、模型；前端只认识四栏词卡 | 需要端到端加法扩展。 |

在真实 MCP 返回结构未核实前，不得承诺排名、环比、竞争度或逐词来源；字段不存在时输出 `null` 或“需补数”。

## 强制判定

模型必须先定性种子词、再判定候选词与种子的关系，最后才允许分入四栏。

种子主类型只能为：`content_scene`、`product_main`、`spec_attribute`、`accessory`、`parent_category`、`brand`、`adjacent_category` 或 `uncertain`。父类目和不确定种子词默认不得作为商品主标题，应要求补充具体商品结构、规格或场景。

候选词关系只能为：

- `direct`：同一商品结构或核心购买意图。
- `content_hook`：证明商品价值的鱼情、痛点、场景或结果。
- `conversion_support`：支撑成交的规格、卖点、材质或配套。
- `cross_sell`：明确关联购，不能替代主商品。
- `category_infrastructure`：集合页、导航、类目基建。
- `diversion_risk`：相邻品类或不同结构，可能分流/混链。
- `brand_risk`：品牌授权不明。
- `weak_or_irrelevant`：弱相关或无效。

只有 `direct`、`content_hook`、`conversion_support` 可进入主四栏；`cross_sell` 只可进商品栏且必须标为关联购。其余词进入风险/降级区。

## 四栏规则

| 栏位 | 准入含义 | 主用途 |
|---|---|---|
| 视频热搜 | 同侧真实数据中已有明显热度、且与种子强相关的内容词 | 视频标题、封面、场景、直播话题。 |
| 视频潜力 | 有同侧证据、强相关、可差异化验证的场景/结果/知识点 | 测完播、互动、进店、商品点击。 |
| 商品热搜 | 同侧真实数据中已有商品搜索/带货意图的主词、规格、卖点或配套 | 商品标题、属性、橱窗、直播讲解。 |
| 商品潜力 | 有同侧证据、强相关、可差异化承接的规格/场景/卖点/配套 | 商品页表达、挂车或关联购。 |

“热搜”是当前正在竞争的流量；“潜力”是相对可挖、强相关、可差异化测试的增量。采集返回的 `bucket` 只是特征，不是最终结论。

父类目词、结构冲突的相邻品类主词、授权未知品牌词、无同侧 MCP 证据的词、无可执行动作的词不得进入潜力主池。

## 输入、证据与输出契约

输入 Schema 保持旧调用兼容，并新增可选 `store_context.catalog`。目录项需要传商品结构、确认规格、已验证卖点、主推/关联购角色、品牌授权状态和合规限制。目录为空时仍可给内容建议，但所有挂车建议必须标记 `catalog_unconfirmed`。

采集压缩行至少保留：`keyword`、`side`、`collected_bucket`、`heat`、`rank`、`rank_change`、`trend`、`competition`、`period`、`mcp_source_ref`；采集端未提供的字段一律为 `null`。当前 API 请求、任务持久化和 Web 创建表单都未接收 `store_context`，必须与 Schema 同步改动。

保持现有 `kind=douyin_keyword`、`summary` 和四栏 `categories`，并加法扩展 `executive_summary`、`seed_diagnosis`、`market_snapshot`、`core_playbook`、`weekly_tests`、`exclusions_or_risks`、`compliance_and_linking_rules`。

四栏卡继续保留 `keyword/priority/reason/metrics/evidence/action`，新增 `term_type`、`relationship_to_seed`、`recommended_use`、`risks` 与 MCP 证据对象。默认一个词只进一个主栏；跨侧复用必须有两个侧别证据和不同用途。

`weekly_tests` 是最多 4 个优先测试；词不足时允许少于 3 个并说明原因。每项必须包含内容动作、挂车动作、目录匹配、观测指标、判定规则与风险边界。

`handle_report_douyin`、报告校验、API 类型与 `ReportTabs.tsx` 必须完整透传并渲染新字段。真实 MCP 徽标仅在 `data_source.source == "mcp"` 时显示。

## 验收

- 旧调用仅传 `seed` 时仍生成兼容的四栏基础报告。
- “渔具”“钓具”不进入潜力池，而在风险区说明其基建用途。
- 对“大物竿”出现“海竿”主词时，输出分流/对比风险，绝不建议共用商品链接。
- 视频场景词不会因热度高而自动成为商品主标题。
- 无同侧 MCP 证据、无趋势字段或目录未确认时，报告必须降级而非编造。
- 测试覆盖证据压缩、最终分栏不等于采集 bucket、风险降级、报告透传、Schema 校验和前端类型。
- 使用真实肉机登录态完成一次非 stub 端到端验证；失败必须显示 MCP/登录态错误，不能伪装成功。

实施顺序：先核实 MCP 返回字段并扩展 Schema/分析提示词；再修改 `douyin_analyze.py` 的证据保留与语义归类；最后同步报告组装、校验、API/任务输入、前端和测试。
