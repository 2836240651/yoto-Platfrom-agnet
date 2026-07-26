# BOSS 平台数据接入审查报告（抖音首批）

> 状态：审查完成，尚未进入实现计划。  
> 日期：2026-07-26  
> 范围：BOSS 抖音运营数据展示、Agent/Tool 边界、后续平台扩展和肉机定时采集。

## 1. 结论

1. `douyin_reports` 已可作为 BOSS 首批抖音运营数据源；BOSS 页面应通过本仓 API 读取，前端不得直连 MySQL。
2. BOSS 数字查询不是 LLM 任务，也不是当前抖音关键词 Skill 的一部分；首期不新增 Skill，不让模型判断结构化成功/失败。
3. 如后续需要在对话中回答“抖音运营日报”，再新增一个只读 `douyin_report_query` Tool/MCP；它只返回小型聚合结果，LLM 仅在用户请求经营分析/方案时解释结果。
4. 肉机不应直接访问 MySQL 或决定调度；推荐服务器发出同步 Job，肉机通过现有 `/worker/*` 队列领取、浏览器/官方接口采集，再将结构化数据或源文件回传服务器，由服务器完成校验和幂等写库。
5. Temu、Amazon、1688 必须分别确认合法数据源、认证、字段和增量语义后再接入；禁止用当前 Temu 上架 MCP 或抖音关键词 MCP 伪装成运营数据来源。

## 2. 已核验事实

### 2.1 远程数据库（只读查询）

数据库 `douyin_reports` 恰有 5 张表：

| 表 | 精确行数 | 主要用途 |
| --- | ---: | --- |
| `store_daily` | 31 | 店铺日报 |
| `store_weekly` | 13 | 店铺周报 |
| `store_monthly` | 25 | 店铺月报 |
| `product_transaction_daily` | 15,007 | 商品成交日报 |
| `video_daily` | 186 | 视频日报 |

总行数为 **15,262**。没有发现其他业务表。

- `video_daily.completion_rate` 存在，类型为 `decimal(18,10)`，可为空。
- `video_daily` 有唯一索引 `uq_video_daily_source_row(source_file, source_row_number)`；因此相同 `video_id` 的不同原始行可保留，重复导入相同源文件行不会新增数据。
- `product_transaction_daily` 有唯一索引 `(report_date, product_id)`；三个店铺汇总表均有唯一索引 `(report_date, store_name)`。
- 店铺相关 4 张表各只有 1 个 `store_name`；当前 BOSS UI 不应预设为多店汇总产品。
- 数据最新日期为 2026-07-22：店铺/商品日报到 2026-07-22，视频 `published_at` 最晚为 2026-07-22 18:34。BOSS 必须显示“数据截至 2026-07-22”，不能展示为实时或今日数据。
- 视频表 186 行对应 184 个不同的 `video_id`，与“保留两组相同视频 ID 原始行”的说明一致。

### 2.2 本仓现状

| 分类 | 结论 |
| --- | --- |
| 已满足 | BOSS 路由 `/boss`、`/boss/douyin` 与四平台侧栏已经存在；平台 MCP 有肉机 `/worker/heartbeat`、`/worker/claim`、`/worker/complete` 队列接口。 |
| Stub | BOSS 页面全部为“暂未接入数据”空态；抖音关键词采集与 Temu 上架工具存在，但都不是运营报表读取能力。 |
| 规范有、仓库无 | BOSS 报表 API、MySQL 只读连接、报表输出 schema、数据新鲜度展示、报表同步 Job、Temu/Amazon/1688 的运营数据源契约均未实现。 |

## 3. 推荐目标架构

```text
BOSS Web
  -> Agent Platform API（Pydantic 输出 + 参数化 SQL）
  -> douyin_reports（只读 DB 用户）

用户在对话中要求经营分析（后续）
  -> 1 个 douyin_report_query Tool/MCP（小型聚合数据）
  -> 可选 heavy LLM 解释指标；不参与 SQL / 成败判断

服务器计划任务
  -> platform-mcp /worker 队列提交 report_sync Job
  -> 肉机领取 Job，执行平台允许的浏览器自动化或官方接口
  -> 回传结构化批次/源文件清单
  -> 服务器 schema 校验 + 幂等 upsert -> douyin_reports
```

### 3.1 BOSS 读取路径（P0）

建议新增 API，而不是 BOSS 前端直接访问数据库，也不是先做 Agent Skill：

- `GET /api/boss/platforms`：平台可用状态、最新数据日期、数据源说明。
- `GET /api/boss/douyin/overview?period=daily|weekly|monthly&end_date=YYYYMMDD`：支付金额、订单数、支付用户数、件数、曝光、点击、曝光点击率、点击转化率、退款金额/订单数、数据截至日期。
- `GET /api/boss/douyin/products?report_date=YYYYMMDD&limit=20`：按支付金额排序的商品榜。
- `GET /api/boss/douyin/videos?period=...&limit=20`：视频成交/播放/完播/互动榜，并保留源行语义，不以 `video_id` 去重。

所有默认值取源表最新可用周期；接口返回 `data_as_of`、`source`、`row_count`。前端缺数时显示“暂无数据”，不生成模拟指标。

### 3.2 数据库安全与部署边界

- 创建独立的 `boss_report_reader`，只授予 `douyin_reports` 的 `SELECT`；API 不得使用容器 MySQL root。
- 创建独立的 `report_ingester`，只授予 5 张表的 `INSERT` / `UPDATE` / 必要 `SELECT`；肉机不持有该凭据。
- API 与 platform-mcp 以部署环境变量获得连接信息；不把密码、主机地址、端口写入源代码、Skill、文档或前端。
- 首期不改现有 5 表、不创建 raw/临时表；写入使用现有唯一键 `INSERT ... ON DUPLICATE KEY UPDATE`。视频按 `(source_file, source_row_number)`，店铺/商品按现有业务唯一键。
- 当前 `report_date` / `published_at` 是字符串且格式不同；P0 查询仅对等匹配已有索引，时间范围解析在 API adapter 完成。未来新增采集写入必须固定标准格式，任何列类型迁移单独立项。

## 4. 肉机定时采集建议

### 不建议

- 不让肉机直连 MySQL。
- 不让 LLM 读取 Excel 全表、控制浏览器或决定重试。
- 不以 Windows 无限循环替代服务端调度。
- 不复用 open-reverselab 词卡流水线。

### 推荐流程

1. **服务器调度**：cron/systemd 定时创建 `report_sync` Job（平台、报表种类、统计周期、目标日期、幂等键）。
2. **肉机执行**：沿用现有 worker 认证与 claim/complete 协议；单个 Job 内部完成登录检查、下载、有限等待和重试。
3. **非 LLM 解析**：肉机或服务器 Python 解析 Excel/CSV，按 schema 映射、数值校验、行数统计；禁止把完整文件交给模型。
4. **服务器写入**：只由服务器 ingest handler 使用 `report_ingester` 将有效批次 upsert 到 5 张表，并返回 `inserted` / `updated` / `skipped` / `failed` 计数。
5. **BOSS 新鲜度**：BOSS API 按 `imported_at` 和报表周期显示最近同步时间、数据截至日期、失败状态。

默认调度建议：日报在业务数据稳定后的次日清晨执行；周报/月报在对应周期结束且平台数据稳定后执行。具体时刻必须由数据源刷新规律确认，不能先硬编码。

## 5. 多平台扩展原则

| 平台 | 当前可复用能力 | 首要阻塞 | 推荐接入形态 |
| --- | --- | --- | --- |
| 抖音 | 肉机浏览器自动化 + worker 队列；现有 `douyin_reports` | 报表导出入口/认证流程、API↔MySQL 网络和只读账号 | 先完成 API BOSS 只读闭环，再接 `report_sync` Job |
| Temu | Commander MCP 用于上架 | 上架任务不是经营报表；尚未确认可用报表/数据源 | 独立 Temu analytics MCP/adapter，不能复用上架工具 |
| Amazon | 无本仓经营数据实现 | SP-API/Reports 认证、店铺授权、限流、字段契约 | 优先官方 Reports API 的服务器 Job；通常不需要肉机浏览器 |
| 1688 | 规范提到外部采集优先 MCP 包装 | 是否有可调外部采集入口、Cookie/授权和报表字段 | 外部采集 Job MCP 化；确认后再安排肉机 |

跨平台统一的是 API 输出 DTO（概览、趋势、榜单、新鲜度、错误），不是强行先建一张大而全的原始表。每个平台保留自己的数据模型和 adapter。

## 6. 实施前阻塞与需要确认的决定

1. 抖音当前 5 个 Excel 分别由哪个后台/账号导出？是否允许肉机自动下载，还是 Hermes 监听脚本是唯一合法入口？
2. 是否接受 API 使用独立只读 MySQL 用户，以及 platform-mcp 使用独立写入用户？需要确认容器网络路径而不是暴露数据库公网端口。
3. BOSS 首期展示哪些指标和榜单？是否只展示 1 个店铺，还是需预留店铺筛选。
4. `report_date` 的字符串口径（日报、周报、月报）及“今日/截至日期”的业务规则由谁确认？
5. Temu、Amazon、1688 各自的账号授权、允许的数据源、采集周期和负责人是什么？
6. 是否先只落地“抖音 BOSS 只读查询 + 手动刷新”，通过验收后再接肉机定时同步？

## 7. 推荐优先级

- **P0-A**：确认 6.1～6.4，创建最小权限 DB 账号与连通性 spike。
- **P0-B**：实现抖音 BOSS 只读 API + 前端真实数据展示 + 数据新鲜度；不新增 Skill/MCP。
- **P0-C**：完成一次手动 `report_sync` 全链路（肉机 -> platform-mcp -> ingest -> MySQL -> BOSS）。
- **P0-D**：确认稳定后再启用服务器调度；调度失败必须在 BOSS 显示明确状态。
- **P1**：为对话经营分析新增 1 个 `douyin_report_query` Tool/MCP；仅聚合数据后再按需用 heavy LLM 给建议。
- **P2**：按独立数据源契约接入 Temu、Amazon、1688。
