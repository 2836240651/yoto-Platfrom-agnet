# Spec（WIP）：跨境业务场景 · LLM vs Tool 边界

> 状态：**WIP** · 版本 v0.1 · 2026-07-23  
> 用途：给编码 Agent 的**可执行边界**；对照实盘项目校准，非空谈。  
> 权威产品 / 工程定义仍以 `docs/spec-product.md`、`docs/spec-engineering.md` 为准。  
> 定稿后可升为 `docs/spec-business-scenarios-llm-tool.md` 并更新 `docs/README.md`。

---

## 0. 核心原则（强制）

| 类型 | 归类 | 示例 |
|------|------|------|
| 创意、理解、联想、生成、差异化改写、语义拆解 | **LLM**（Completion / 多模态） | 文案、提示词、长尾词联想、竞品改写 |
| 固定流程、读写文件、接口、浏览器自动化、存储、统计渲染 | **Tool / MCP** | Excel 解析、店小秘 API、采集、OSS、HTML 报表 |
| **已落地外部流水线（内部自带模型）** | **整段视为 Tool/MCP** | Temu Commander `product_issue`（内含 Lyncr 分析/生图） |

**边界补充：** 若外部系统已经把「分析 + 生图 + 上架」收成可调 job，agent-platform **不得**再拆成 LLM 步重复调用模型；本仓最多做意图路由、缺参确认、job 状态人话。

**Token 禁令**

- Excel 全表、图片二进制、采集原始大 JSON：**禁止**进模型上下文。  
- LLM 只吃：抽样行、字段摘要、校验错误列表、需改写的文本片段。

**Skill 与 Tool 粒度**

- Skill = 剧本（何时问什么、调哪个 tool、成功长什么样）。  
- 固化的是**步骤类型与工具名**，不是把全部业务重写进 `SKILL_PLANS` 硬编码、也不是用系统提示词「渐进写完上架」。  
- 对用户可表现为「一次 MCP / 一个任务」；MCP **背后**可以是已有系统的多步 job（读表→可选 LLM→生图→发布）。进度用轮询/事件，**禁止**让 LLM loop 逐步代跑平台 API。

**接入姿势（统一）**

```
Workspace 用户意图（含附件）
  → Skill（渐进披露：metadata → SKILL.md → 按需 prompts）
  → LLM 步（仅语义/生成） 和/或 MCP Tool（固定动作）
  → MCP 调用外部已有系统（Commander / OSS / social-auto-upload / 采集服务）
```

禁止在本仓 `src/agent` 重复实现已落地的上架/发布/OSS 引擎。

---

## 1. 场景一：Temu 智能产品上架

### 1.1 业务目标

商户提供产品 Excel + 原图 → **一次调用已落地 Commander 上架任务** → 店小秘完成 Temu 上架。

### 1.2 边界校准（相对「逐步拆 LLM」文档的修正）

Commander **已是完整闭环**。链路内模型调用归 **Commander Server（Lyncr）**，**不属于** agent-platform Runtime 的 LLM 步。

| 阶段 | 发生在哪 | agent-platform 要不要再跑 LLM |
|------|----------|-------------------------------|
| 解析 Excel、笛卡尔积校验 | Commander API（`AgentProductIssue`） | **否** — Tool 背后 |
| 缺标题/缺 5 图时：视觉分析、多语标题、五场景提示词 | Commander `RunProductIssue` → `runProductIssueLyncrLLM` / `analyzeProductVision` | **否** — 已有 Lyncr |
| 五张轮播图生图 | Commander `runLyncrProductCarousel` | **否** — 已有 Lyncr |
| 店小秘 `add` 上架 | Commander Agent `DxmFactory.ProductIssue` | **否** — Tool 背后 |
| 用户说「Temu 批量上架」+ 传表；确认店铺；解释 job 失败 | 本仓 Skill / 薄对话 | **仅意图路由与人话**（可选极薄 LLM）；**禁止**重做分析/生图 |

**对 Workspace 的正确抽象：整条 Temu 上架 = 一个（或「提交 + 查状态」两个）MCP Tool。**

```
用户 Excel +「Temu 批量上架」
  → Skill 确认 file_id / 店铺等缺参
  → MCP temu_batch_list_from_excel(...)
  → COMMANDER_API product_issue（内部自带 Lyncr + DXM）
  → 轮询 job → 人话总结
```

### 1.3 实盘调用链（代码事实）

1. HTTP：`AgentProductIssue` 收 Excel → 建任务  
2. `RunProductIssue`：若标题或 5 图不齐 → Lyncr vision + 标题/场景 LLM → Lyncr 生图；已齐则跳过  
3. WebSocket 下发 Agent（去掉内嵌大图）  
4. `DxmFactory.ProductIssue` → 店小秘 API 上架  

### 1.4 MCP 包装

| 项 | 约定 |
|----|------|
| 外部系统 | `commander-server` + `commander-agent`（DXM / Temu） |
| 建议 MCP | `temu_batch_list_from_excel`（`file_id`、店铺上下文 → `job_id`）；可选 `temu_listing_job_status` |
| 环境变量键名 | `COMMANDER_API_BASE`、`COMMANDER_API_TOKEN` |
| Skill | 只做意图匹配、缺参确认、失败人话；**不**调用本仓 Completion 做商品分析/生图 |

**禁止**：在本仓重写 Excel→Lyncr→店小秘；禁止把 Commander 内部步骤拆成 agent-platform 的多步 LLM Skill 计划。

### 1.5 本机对照（仅供人读，勿写入代码）

- `dev/workspace/commander-server-t260220`：`internal/tasks/proto_product_issue.go`、`product_issue_llm_lyncr.go`、`lyncr_product_carousel.go`  
- `dev/workspace/commander-agent-*-main/.../factory/dxm/ProductIssue.go`

## 2. 场景二：1688 铺货上架

### 2.1 业务目标

采竞品 Listing → AI 差异化改写与图翻新 → 自动化上架。

### 2.2 步骤边界

| 步骤 | 边界 | 说明 |
|------|------|------|
| 竞品 Listing 采集 | **Tool** | CDP/CLI/HTTP 采集桌面或 Onebound 等 |
| 标题/详情差异化改写 | **LLM** | 保留核心参数，去同质化 |
| 图生图翻新 | **LLM/生图 API** | grsai / Lyncr 类 |
| 后台/ERP 上架 | **Tool** | 妙手导入或商家后台 Playwright |

### 2.3 实盘与缺口

| 能力 | 状态 | MCP 建议 |
|------|------|----------|
| 竞品采集桌面 | 已有 sibling `1688-`（本地 HTTP/CLI） | 可先包 `1688_offer_collect` |
| Commander 1688 v1（妙手路径） | 产品内 API，非本仓 | 可选 MCP 适配，勿复制业务 |
| 商家后台 Playwright 发品（wizard v2） | 多为 Spec，**未完整可调** | **未完成前禁止在本仓假装已有发品 MCP** |

**注意**：采集与发品是两截；文档不得写成「一条已闭环」误导实现。

### 2.4 本机对照（仅供人读）

- 采集：`reverselab/1688-`  
- Wizard 规格：`dev/workspace/docs/.../1688-listing-wizard-v2`（若存在）

---

## 3. 场景三：抖音关键词挖掘与可视化（本仓最高优先）

### 3.1 业务目标

种子词 → 拓展/分层 → 行业数据采集 → 可视化或结构化报告，支撑选品与内容。

### 3.2 步骤边界

| 步骤 | 边界 | 说明 |
|------|------|------|
| 种子词语义与拓展方向 | **LLM（轻量）** | 勿一次加载全量 Spec |
| 行业数据批量采集 | **Tool/MCP** | **蝉妈妈个人版**：Cookie/登录态 + **浏览器自动化**拉数（站点自身 `api-service.chanmama.com` 等请求随登录态发出，**≠**开放平台官方 API 套餐）；受个人版权益/次数限制。当前本仓多为 stub |
| 长尾联想与分层 | **LLM** | 可结合采集结果摘要再归纳 |
| 数据整理与前端/报告渲染 | **Tool / FE** | 本仓报告 `kind=douyin_keyword`；词卡 HTML 流水线在 open-reverselab（另一条产品形态） |

### 3.3 实盘与禁令

| 项 | 约定 |
|----|------|
| 本仓 Skill | `douyin-keyword-research`（采集 tool 多为 `mcp_tool: null`） |
| 外部参考 | open-reverselab：蝉妈妈登录态自动化观测/笔记；词卡流水线（slug→HTML）；抖音渔具采集包 |
| **采集真相** | 产品意图 = 蝉妈妈**个人版 Cookie + 浏览器自动化**，不是官方 OpenAPI Key 对接 |
| **禁止** | 把词卡流水线整包接到本仓业务 Skill；禁止把个人版 Cookie 明文写进仓库 |

### 3.4 本机对照（仅供人读）

- 词卡流水线：`open-reverselab/scripts/keyword-cards`；HTML：`exports/keyword-cards/<stamp>/html/`、`dev/workspace/docs/keyword-cards/`  
- 个人版约束文档例：`dev/workspace/docs/chanmama-fishing-intercept-v2.html`  
- 本仓：`skills/douyin-keyword-research`、`config/tool_registry.json`  
- 优先工程：真实采集 MCP（个人版 Cookie 自动化）+ Skill `schema/`

---

## 4. 场景四：企业 OSS 多媒体托管

| 项 | 约定 |
|----|------|
| 边界 | **100% Tool**，无 LLM |
| 能力 | 上传、存储、分类、预览、下载、权限 |
| 外部系统 | `media.yoto.work`（源码仓常称 OSS / media-ybb-oss） |
| 建议 MCP | `oss_upload`、`oss_list`（或等价） |
| 环境变量键名 | `OSS_API_BASE`、`OSS_API_TOKEN` |

为上架生图、社媒发布提供统一素材源；不进 agent 主路径硬编码。

### 本机对照（仅供人读）

- 常见根：`OSS`（部署域名 media.yoto.work）

---

## 5. 场景五：多社交媒体批量发布

| 步骤 | 边界 |
|------|------|
| 文案/标题/配文创作（可选前置） | **LLM** |
| 账号登录、上传、发布、状态回传 | **Tool**（已有自动化后端） |

| 项 | 约定 |
|----|------|
| 外部系统 | `social-auto-upload`（多平台 Playwright/API） |
| 建议 MCP | `social_publish_video` / `social_list_accounts` |
| 环境变量键名 | `SOCIAL_UPLOAD_API_BASE` |
| Skill | 编排确认平台与账号；**不**把 Playwright 搬进 LangGraph 节点 |

### 本机对照（仅供人读）

- 常见根：`multiPlaformUpLoad/social-auto-upload`

---

## 6. MCP 包装通用约定

1. **一工具一事**：对 Workspace 暴露稳定 JSON Schema（建议同步落在 `skills/<id>/schema/`）。  
2. **异步 job**：长任务返回 `job_id`；用 status tool 或任务 API 轮询；禁止 LLM 空转等待。  
3. **失败语义**：与 `docs/spec-engineering.md` §4 一致（stub warn / 真失败 failed / 禁止假成功）。  
4. **凭证**：店铺 token、Cookie 只进加密存储或环境侧；**禁止**进 prompt / Skill 正文。  
5. **限流**：QPS/熔断做在 MCP→上游适配层，不散落在各 Skill。

---

## 7. 接入优先级（以架构契约为准）

强制顺序见 **`docs/spec-architecture-contract.md`**：

1. P0：Skill Schema + 抖音真实采集 MCP  
2. P1：Runtime 动态加载 + Temu Commander **整段** MCP（本仓不做分析/生图）  
3. P2：OSS / 社媒等（延后）

---

## 8. 编码 Agent 检查清单

- [ ] 该步是语义/生成？→ LLM；固定 IO/接口/自动化？→ Tool  
- [ ] 是否已有外部系统可 MCP 包装？→ 禁止重写  
- [ ] 大表/大 JSON/图片是否被错误塞进模型上下文？  
- [ ] 是否误接 `keyword_cards_pipeline_tool` 到抖音四栏 Skill？  
- [ ] 1688 发品 MCP 是否在未就绪时假装可用？  
