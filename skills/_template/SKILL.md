---
name: skill-template
description: Skill 模板 — 复制此目录创建新垂直能力
---

# Skill 模板

契约见 `docs/spec-architecture-contract.md`：Skill + 最多 1～2 个 MCP；必备 `schema/input.json`、`schema/output.json`。

## 工作流

1. 步骤一
2. 步骤二
3. 输出

- 分步提示：`prompts/<step>.md`（按需加载）  
- Schema：`schema/input.json` · `schema/output.json`  
- 迁移期步骤名可与 `SKILL_PLANS[].name` 对齐，直至 P1 动态加载落地

## MCP 工具映射（≤2）

| 步骤 | MCP Tool | 说明 |
|------|----------|------|
| 1 | example_tool | 描述 |

## 运营 / Workspace 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| param1 | string | 说明 |
