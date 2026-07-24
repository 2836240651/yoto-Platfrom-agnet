# docs/

本目录是 **开发文档** 根。编码 Agent 先读仓库根 `AGENTS.md`，再按下列权威链打开文件。

## 权威（现行）

| 文档 | 用途 |
|------|------|
| [`spec-product.md`](./spec-product.md) | **产品唯一权威定义**（跨境 Agent Workspace、多角色） |
| [`spec-engineering.md`](./spec-engineering.md) | **工程现状与约束**（Runtime/MCP/Skills 真话） |
| [`spec-architecture-contract.md`](./spec-architecture-contract.md) | **架构契约 · 迭代优先级 · 开发红线（强制）** |

## 工作区

| 目录 | 用途 |
|------|------|
| [`wip/`](./wip/) | 未定稿草稿；定稿后升为 `spec-*.md` 或写入权威 Spec |
| [`wip/spec-business-scenarios-llm-tool.md`](./wip/spec-business-scenarios-llm-tool.md) | **场景 LLM vs Tool 边界**（可编码检查清单；定稿前现行） |
| [`wip/p0-contract-gap-check.md`](./wip/p0-contract-gap-check.md) | **P0 契约验收核对**（写执行计划前必读） |
| [`wip/temu-commander-mcp-spike.md`](./wip/temu-commander-mcp-spike.md) | **Temu→Commander MCP spike**（API/鉴权/taskId 缺口；P1-2 计划前） |
| [`wip/p1-temu-mcp-contract-gap-check.md`](./wip/p1-temu-mcp-contract-gap-check.md) | **P1-2 Temu/远程 MCP 契约核对**（执行计划编码前必读） |
| [`handoffs/`](./handoffs/) | 跨会话交接：`YYYY-MM-DD-<slug>.md` |
| [`archive/`](./archive/) | 已废止/被取代的 Spec、baseline、PRD；**不参与日常实现决策** |

## 规则

1. 冲突时：`spec-product.md` > **`spec-architecture-contract.md`（契约/优先级）** > `spec-engineering.md`（现状）> 场景 WIP > `skills/*/SKILL.md` > `archive/*`。  
2. 不要在 `docs/` 根目录再堆平行「第二产品定义」。  
3. 新阶段工程方案先写 `wip/`，评审后再合并进权威 Spec 或独立 `spec-*.md`（并改本索引）。
