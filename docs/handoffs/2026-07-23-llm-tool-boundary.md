# Handoff：跨境场景 LLM vs Tool 边界文档落地

- 日期：2026-07-23
- 状态：done

## 做了什么

1. 新增 WIP 场景标准：`docs/wip/spec-business-scenarios-llm-tool.md`  
   - 五场景步骤级 LLM/Tool 边界  
   - 实盘映射（仓名/服务名；本机路径仅附录）  
   - MCP 包装约定、Token 禁令、接入优先级  
2. 权威 Spec 增加指针：  
   - `docs/spec-product.md` v1.1 §4.1 垂直场景清单  
   - `docs/spec-engineering.md` v1.1 §6 场景边界摘要  
3. 更新 `docs/README.md`、`AGENTS.md`（禁令与阅读顺序）

## 编码 Agent 怎么用

垂直场景实现前：`spec-product` → `spec-engineering` → **`wip/spec-business-scenarios-llm-tool.md` 检查清单**。

## 未做

- 未实现任何 Temu/1688/OSS/社媒 MCP  
- 未改 Runtime / `SKILL_PLANS`  
- 场景文仍为 WIP，评审通过后再升格为 `docs/spec-*.md`
