---
name: temu-product-listing
description: 内部共用店 Temu 上架 — Excel + 店铺 → Commander 黑盒 → 肉机 Agent
---

# Temu 产品上架（内部共用店）

契约：Skill 只做意图/缺参确认/调 MCP/人话总结。  
**禁止**本仓做文案、生图、店小秘自动化（均在 Commander / 肉机内）。

## 工作流

1. 确认 Excel 路径（须网关可读，通常为 API 上传到 `uploads/`）与 `shop_id`
2. `temu_product_issue_submit`（内含 precheck）
3. `temu_product_issue_status` 轮询至 success/failed
4. 向用户回报结果

## MCP（≤2）

| 步骤 | MCP Tool | 说明 |
|------|----------|------|
| 提交 | temu_product_issue_submit | Commander `product_issue` |
| 状态 | temu_product_issue_status | Commander `task_list` |

默认 Agent：`肉机`（环境变量 `COMMANDER_DEFAULT_AGENT_ID`）。

## 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| excel_path | string | 服务器/网关可读的 xlsx 路径 |
| shop_id | string | Temu 店铺 ID（店小秘侧） |
| platform | string | 固定 `temu` |
