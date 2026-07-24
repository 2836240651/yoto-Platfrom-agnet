# Handoff：开发文档大清洗 + 权威产品定义

- 日期：2026-07-23
- 状态：done

## 做了什么

1. 新增权威产品 Spec：`docs/spec-product.md`（跨境 Agent Workspace、多角色）。  
2. 新增工程 Spec：`docs/spec-engineering.md`（硬编码现状、MCP 态度、渐进披露未实现）。  
3. 新增 `docs/README.md` 索引；旧 baseline/PRD/phase Spec 迁入 `docs/archive/`。  
4. 重写 `AGENTS.md`、`README.md` 定位，去掉「仅运营任务模板」表述。

## 编码 Agent 边界

实现前读：`docs/spec-product.md` → `docs/spec-engineering.md`。  
`docs/archive/*` 不参与日常决策。

## 未做

- 未改 Runtime / 未接 Skills 渐进披露加载器。  
- 未改前端行为（Composer 仍可能落到单 Skill 表单）。
