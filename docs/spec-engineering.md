# Spec：工程现状与约束（Runtime / MCP / Skills）

> 状态：**Canonical（工程）** · 版本 v1.2 · 2026-07-23  
> 产品定义见 `docs/spec-product.md`。架构契约与迭代优先级见 **`docs/spec-architecture-contract.md`（强制）**。  
> 本文只写实现边界与**真话现状**，避免把目标写成已交付。

---

## 1. 架构入口（路径）

| 层 | 路径 |
|----|------|
| Runtime | `src/agent/` |
| Skills | `skills/<id>/SKILL.md` |
| Skill Schema（契约强制） | `skills/<id>/schema/input.json` · `output.json` |
| 分步提示（约定） | `skills/<id>/prompts/<step>.md` |
| 执行计划（现状） | `src/agent/constants.py` → `SKILL_PLANS` |
| Tool 映射 | `config/tool_registry.json` |
| MCP 注册 | `config/mcp.json` |
| MCP 实现 | `mcp/servers/` |
| API | `apps/api/` |
| Web Shell | `apps/web/` |
| 平台薄系统提示（约定） | `src/agent/prompts/platform_system.md` |

## 2. 现状（必须当事实）

| 项 | 事实 |
|----|------|
| 执行模型 | LangGraph 固定图 + **硬编码** `SKILL_PLANS` 四步流水线 |
| Skills 渐进披露 | **未实现**：无 Discovery→Activation→Execution 加载器；`SKILL.md` 几乎不进模型上下文 |
| Composer | UI 可自由输入；创建任务仍常落到单一 Skill / 表单参数 |
| MCP 业务工具 | 抖音采集类多为 `mcp_tool: null`（intentional stub） |
| 报告 | `kind` 区分；当前业务 kind 以 `douyin_keyword` 为主 |

编码时：**不要假设** Runtime 已按 Agent Skills 标准做渐进披露。

## 3. 目标 Runtime（未完成 · 见契约 P1）

对齐 Agent Skills + 架构契约「Skill + 1～2 MCP」：

1. Discovery：Skill metadata 索引  
2. Activation：读入匹配的 `SKILL.md`  
3. Execution：按需读 `prompts/`、`schema/`、`references/`；MCP/脚本按需调用  

**P1-1** 起拆除业务对静态 `SKILL_PLANS` 的硬依赖；迁移期允许过渡。  
是否迁 Deep Agents 等 harness：契约允许预留，未立项前不在业务 PR 偷偷换底座。

## 3.1 迭代指针

强制顺序与验收：`docs/spec-architecture-contract.md`（P0 Schema+抖音 MCP → P1 Runtime+Temu MCP → P2 延后）。

## 4. MCP 产品态度（仍有效）

| 场景 | 允许结果 |
|------|----------|
| intentional stub（`mcp_tool: null`） | 可完成 + **warn** |
| MCP 失败且不允许 fallback | **failed**，禁止成功报告 |
| fallback 仅限显式 dev 配置 | 完成须带 **stub_fallback** 类标识 |

禁止把 open-reverselab **词卡流水线**接到本仓业务 Skill。

## 5. Web 双视图（工程）

| 视图 | 路由前缀 | 暴露 |
|------|----------|------|
| 业务（默认） | `/`、`/tasks/*` | 进度、报告、人话错误；少工程术语 |
| 开发 | `/dev/*` | 另加 loop 事件、预算、MCP 页等 |

壳的信息架构以 `apps/web` 为准；与归档中「不做聊天框」的旧 baseline **冲突时以产品 Spec + 前端为准**。

## 6. 业务场景 LLM vs Tool（指针）

步骤级边界、实盘映射、MCP 包装约定、接入优先级：

→ **`docs/wip/spec-business-scenarios-llm-tool.md`**

编码强制摘要：

- 语义/生成 → LLM；文件/接口/自动化/渲染 → Tool/MCP。  
- 已有 Commander / OSS / social-auto-upload / 1688 采集：**MCP 包装，禁止在 `src/agent` 重写引擎**。  
- 大表/大 JSON/图片二进制禁止进模型上下文。  
- 对用户「一次 tool」允许背后是外部多步 job；禁止 LLM loop 逐步代跑平台 API。

## 7. 改动同步清单

- 新 Skill：`skills/` →（现状仍要）`SKILL_PLANS` → registry → API Literal → FE  
- 提示词文件变更：步骤名与 `SKILL_PLANS[].name` 对齐  
- 新业务场景步骤：先对照 `docs/wip/spec-business-scenarios-llm-tool.md` 标 LLM/Tool  
- 跨会话大改：`docs/handoffs/YYYY-MM-DD-<slug>.md`

## 8. 历史文档

MCP phase1/2/3、dual-ui、旧抖音产品 Spec 等已迁入 `docs/archive/`。  
其中 phase3 的失败语义已摘要进本文 §4；细节争议时可读归档，**不得**再把归档当默认权威。
