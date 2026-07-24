# Agent Instructions — agent-platform（编码 Agent 用）

本文件给 **Cursor / Codex 等编码 Agent** 读，不是跨境智能体的运行时提示词。
产品与工程权威 Spec 只记路径；正文见 `docs/`。

## 仓库定位

- **产品**：跨境电商行业 **Agent Workspace**（多角色：开发 / 运营 / 老板 / 财务等），壳对标 Codex 式工作区。  
- **权威定义**：`docs/spec-product.md`  
- **工程现状与约束**：`docs/spec-engineering.md`  
- **架构契约与迭代优先级（强制）**：`docs/spec-architecture-contract.md`  
- **场景 LLM/Tool 边界**：`docs/wip/spec-business-scenarios-llm-tool.md`  
- **文档索引**：`docs/README.md`  
- 本仓改 Runtime / Skill / MCP / API / Web；垂直能力用 Skill + MCP 挂载（已有外部系统优先 MCP 包装，禁止重写引擎）。

## 每次开发必读流程（强制 · 先于写代码 / 写执行计划）

拿到规范或需求后，**禁止**立刻写长执行计划或开工实现。必须按序：

### 1. 对照现状验契约

读代码 / `config/tool_registry.json` / `config/mcp.json` / `skills/<id>/` / 相关 Spec，标清三类：

| 标记 | 含义 |
|------|------|
| **已满足** | 契约要求已在仓库落地 |
| **stub** | 有名字或接口，但是假数据 / `mcp_tool: null` / 未接通 |
| **规范有、仓库无** | Spec 写了但无可调实现（例：蝉妈妈个人版 Cookie 自动化采集 MCP 是否存在可调入口） |

### 2. 揪阻塞与歧义

把答不清的问题列出来再往下走，例如：

- 采集源：蝉妈妈个人版 Cookie + 浏览器自动化（非官方 OpenAPI），还是其它临时方案？  
- Schema 谁校验：Runtime，还是 API？  
- 验收「跑通」的最小路径是什么？  

**禁止**把未证实假设写进详细计划。答不清 → 先问人，或进入步骤 3。

### 3. 必要时最小 spike

只读核对或短时打通外部依赖；确认能调通再写计划。依赖不通则修订 Spec / 缩小范围，不编造计划细节。

### 4. 然后才写执行计划

任务可测、可验收；按架构契约切分（如 P0-1 → P0-2）。发现 Spec 漏洞须回写 `docs/`（或 `docs/handoffs/`），再实现。

执行计划落盘：`docs/wip/` 或 `docs/handoffs/YYYY-MM-DD-<slug>.md`（本文件只记路径）。

## 明令禁止

- 禁止把归档文档（`docs/archive/`）当作现行产品定义。  
- 禁止把 open-reverselab **词卡流水线**（`keyword_cards_pipeline_tool` / 抖音 Playwright → yoto.work）接进本仓业务 Skill。  
- 禁止 MCP 失败时伪装成成功报告（intentional stub 除外，见 registry `mcp_tool: null`）。  
- 禁止 Skill 直连第三方 API；外部完整 Job 仅允许 **1～2 个 MCP**（见架构契约）。  
- 禁止在 Temu 等**外部已含模型**的 Job 上，于本仓再拆分析/文案/生图 LLM 步。  
- 禁止在抖音+Temu「Skill+MCP」闭环验收前开发域模型 / 完整 OAuth / Celery 等重型基建。  
- 禁止只改 `skills/*/SKILL.md` 不同步 schema / registry / API / FE（及迁移期仍存在的 `SKILL_PLANS`）。  
- 禁止提交密钥或把 `.env` 实值写入代码；模板见 `.env.example`。  
- 禁止硬编码：密钥、本机绝对路径、环境相关 URL/端口散落业务代码。  
- 禁止把 Spec / 交接 / 长提示词正文内嵌进本文件。  
- 禁止在**业务视图**默认暴露 LangGraph / prompt 等工程术语（开发视图除外）。  
- 禁止假设 Skills **渐进披露已实现**（现状为硬编码流程，见工程 Spec）。  
- 禁止跳过「每次开发必读流程」：未验契约 / 未澄清阻塞就写假细计划或直接编码。  
- 禁止用 LLM 执行固定 IO/接口/浏览器自动化；禁止把 Excel 全表/大 JSON/图片二进制塞进模型上下文（见场景边界 WIP）。  
- 禁止在本仓重写 Commander Temu 上架 / OSS / 社媒发布等已落地引擎；应 MCP 包装。  
- 禁止为黑盒 MCP Job 设计「多轮 think / replan / micro 重试」图；等待与重试放进 **单次 Tool/handler 内轮询**，图上尽量 **1～2 步结束**。  
- 禁止用 LLM 评判 MCP 结构化成功/失败（`ok` / `status` / schema）；代码分支即可。  
- 禁止把 LLM Key 写入代码 / Spec / 本文件；经 `.env` 的 NewAPI 兼容端点，见「模型路由」与 `.env.example`。
- 禁止轻量任务默认走 heavy 模型；禁止重型任务默认走 light 模型（见下表）。

## 模型路由（强制）

同一网关可挂多 Key / 多模型；图内优先 get_chat_model_for_state(state, task=...)（src/agent/llm.py）。

| Tier | 用途 | 默认模型 | Env |
|------|------|----------|-----|
| **heavy** | 复杂运营分析、方案撰写、长文推理 | `gpt-5.6-luna` | `LLM_HEAVY_*`（或兼容 `OPENAI_API_KEY` / `LLM_MODEL`） |
| **light** | 摘要抽取、事实提取、意图分类、记忆压缩、简单格式化、缺参/失败人话 | `agnes-2.0-flash` | `LLM_LIGHT_*` |

规则：

- **优先级**：黑盒 Skill 忽略模型 → 请求显式 `model_id`（Composer 钉扎）硬覆盖 → catalog `tier`/`task` → 默认 light。  
- **调用约定**：图节点 / Skill 内 LLM **必须**用 `get_chat_model_for_state(state, task=...)`（自动带 `state["model_id"]`）；禁止裸调 `get_chat_model` 漏传钉扎。黑盒 Skill 调用会抛错。  
- 未钉扎时 **不要** 默认传 `agnes`（否则杀死 heavy catalog）；见 `docs/wip/session-model-picker-design.md`。  
- 黑盒 MCP Job **不**调 LLM 做成败判定（仍用代码）；Temu 上架页挂 `blackbox` 灰掉选择器。  
- 未标明任务类型时：**偏 light**（省成本）；明确分析/方案才用 heavy。  
- 新增 LLM 调用点必须在 PR / 计划里写明 `light` / `heavy` 或接受会话 `model_id`。  
- 模型 ID 以网关 `/v1/models` 为准；换模型只改 env，不改业务代码。

## P0 运行时约定（黑盒 MCP · 少 loop · LLM）

前期垂直能力 = **外部完整项目经 MCP 挂载**，对本仓是黑盒 Job，不是多 Agent 对话。

| 原则 | 要求 |
|------|------|
| 形态 | Skill + **1～2 个 MCP**（如 submit + status）；外部内含模型/流水线的不再拆 LLM 步 |
| 图步数 | 默认 **提交 →（可选）确认**；非必要不加 collect/expand/score 类多轮 |
| Loop | `micro_budget` 对黑盒步默认 **1**；等待/轮询在 handler 或 MCP **一次调用内**完成；禁止靠 graph 空转抬质量分 |
| LLM 何时用 | 仅意图路由、缺参追问、失败人话、分析/方案；**能 Tool 则不用 LLM** |
| LLM 何时不用 | 解析 Excel、调 Commander、轮询任务、根据 `status∈{success,failed,…}` 出报告 |
| 模型 | 见上文「模型路由」；入口 `src/agent/llm.py` |
| 细节 | `docs/wip/spec-business-scenarios-llm-tool.md` · 预算见 `src/agent/budget.py` |

## Sibling 仓库（角色，勿当依赖 import）

| 仓库 | 角色 |
|------|------|
| `open-reverselab` | 逆向实验室；词卡流水线所在仓（只读参考，禁止接入） |
| `agent-platform-starter` | 相关 starter；勿与本仓实现混写 |

用 sibling 仓名定位；勿写本机绝对路径。

## 架构入口

| 层 | 路径 |
|----|------|
| Runtime | `src/agent/` |
| Skills | `skills/<id>/SKILL.md` |
| Skill Schema（强制） | `skills/<id>/schema/input.json` · `output.json` |
| 分步提示（约定） | `skills/<id>/prompts/<step>.md` |
| 执行计划（现状·待 P1 拆除） | `src/agent/constants.py` → `SKILL_PLANS` |
| Tool 映射 | `config/tool_registry.json` |
| MCP 注册 / 实现 | `config/mcp.json` · `mcp/servers/` |
| API / Web | `apps/api/` · `apps/web/` |
| 环境变量模板 | `.env.example` |

## 渐进披露（目标 vs 现状）

| | 说明 |
|--|------|
| **目标** | Agent Skills：Discovery（metadata）→ Activation（`SKILL.md`）→ Execution（按需 `prompts/` / `references/` / MCP） |
| **现状** | 固定 LangGraph 图 + 硬编码 `SKILL_PLANS`；无标准加载器。细节：`docs/spec-engineering.md` |
| **契约** | Skill + 1～2 MCP 黑盒 Job；迭代顺序见 `docs/spec-architecture-contract.md` |
| **落盘约定** | L0 `src/agent/prompts/platform_system.md`；L1 `skills/<id>/SKILL.md`；L2 `skills/<id>/prompts/<step>.md` — 约定路径，**不等于已接线** |

## Commands

| Task | Command |
|------|---------|
| API | `scripts\start-api.bat` → http://127.0.0.1:8000/docs |
| Web | `scripts\start-web.bat` → http://127.0.0.1:5179 |
| 单测 | `python -m pytest tests/unit_tests -q` |
| 安装 | `pip install -e ".[ui]"` |

不在此文件填写部署主机 / 账号 / 内网服务器信息。

## 文档目录约定

| 类型 | 路径 |
|------|------|
| 产品权威 Spec | `docs/spec-product.md` |
| 工程权威 Spec | `docs/spec-engineering.md` |
| 架构契约 / 迭代优先级 | `docs/spec-architecture-contract.md` |
| 文档索引 | `docs/README.md` |
| 草稿 | `docs/wip/` |
| P0 契约核对（计划前） | `docs/wip/p0-contract-gap-check.md` |
| 场景 LLM/Tool 边界 | `docs/wip/spec-business-scenarios-llm-tool.md` |
| 会话模型选择（Composer） | `docs/wip/session-model-picker-design.md` |
| 会话模型选择实现计划 | `docs/wip/session-model-picker-plan.md` |
| 交接 | `docs/handoffs/YYYY-MM-DD-<slug>.md` |
| 历史 | `docs/archive/` |
| Skill 模板 | `skills/_template/SKILL.md` |
| 仓库说明 | `README.md` |

## 编码约定（摘要）

- 实现边界：`spec-product` → `spec-engineering` → **`spec-architecture-contract`** → 场景 WIP（做垂直步骤时）。  
- **开发顺序**：验契约 → 列阻塞 →（可选）spike → 执行计划 → 编码（见上文「每次开发必读流程」）。  
- 新 Skill：`skills/` + `schema/` +（迁移期）`SKILL_PLANS` → registry → API → FE。  
- 新垂直能力优先 **黑盒 MCP**；先问「能否 1～2 个 tool 跑完」，再考虑 LLM 步。  
- 工具：`mcp_tool: null` = intentional stub；真实工具写清 `server` + `allow_in_skills`。  
- 报告用 `kind`；黑盒 Job 用代码拼报告（如 `temu_listing`），勿为汇总再调模型。  
- LLM 客户端：优先 get_chat_model_for_state(state, task=...)；黑盒 Skill 禁止调模型；勿裸调漏传 model_id。
- 默认中文回复用户；保留 API / Skill / 工具英文标识符。  
- `CLAUDE.md` symlink → 本文件；勿维护 divergent 副本。
