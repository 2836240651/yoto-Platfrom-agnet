# Handoff：抖音双肉机手（不合并 Commander Agent）

> 2026-07-25 · 架构定稿

## 结论

**不**二次开发 `commander-agent`（`D:\dev\workspace\commander-agent-t260220-main`）做抖音手。  
**保留**本仓 Python `douyin_meat_worker` ↔ `platform_mcp` `/worker/*`。  
与 Temu Agent **同机双进程并存**；复用的是「出站手」角色，不是 Wails 二进制。

## 证据摘要

| | Temu | 抖音 |
|--|------|------|
| 控制面 | Commander WS + `product_issue` 等 | `platform_mcp` HTTP claim/complete |
| 入队 | `commander_temu_client` → `yoto/api/v1` | `douyin_job_queue` 磁盘队列 |
| 浏览器 | go-rod | Playwright 蝉妈妈 profile |

把抖音塞进 Agent = 改 Commander 云协议 + Go 重写/嵌 Playwright，跨仓高风险，且违反「MCP 包装、禁止重写引擎」。

## 本仓落地

- Spec：[`docs/wip/douyin-meat-machine-mcp.md`](../wip/douyin-meat-machine-mcp.md)「架构锁定」
- 运维一页：[`docs/wip/douyin-meat-ops-runbook.md`](../wip/douyin-meat-ops-runbook.md)
- 双启：`scripts/start-meat-hands.bat`；**EXE**：`scripts/build-meat-worker.bat` → `dist/meat-worker/`（见 [`docs/wip/meat-worker-exe.md`](../wip/meat-worker-exe.md)）
- 双路状态：`scripts/meat_hands_status.py`；API `GET /api/tools/status` 含 `commander_agent` + `douyin_meat_worker`（总体 `ok` 以 MCP + 抖音手为准，Temu 仅展示）
- 部署：`scripts/deploy-platform-mcp.bat`；API 热补丁 `scripts/deploy-agent-api-hotpatch.js`

## 线上对齐（2026-07-25）

- `platform-mcp` 已部署（含 `/worker/*` + 抖音队列）
- `agent-platform-api` 热补丁后 Skill 计划为 `collect → analyze → report`（禁 stub 回退）
- `GET /api/tools/status`：`douyin_meat_worker` 在线已登录；`commander_agent` 若 401 为 Commander Token 问题，不影响抖音采集判定
- 真采任务走 MCP；空结果会失败（如蝉妈妈无相关词），**不会**落 stub 词卡

## 明确不做

- commander-agent 增加 `douyin_*` protocol  
- 蝉妈妈 Cookie 并入 rod profile  
- 客户端直连肉机开端口  
