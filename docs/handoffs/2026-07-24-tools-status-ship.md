# Handoff：工具状态收口与上线

> 2026-07-24 · `feat/tools-status-probe`

## 完成

- `GET /api/tools/status`：MCP + 肉机探测；`COMMANDER_*` 仅从 Settings（`.env` / 进程 env）读取，无 `os.environ` 副作用
- FE：侧栏「工具状态」→ `/tools`；单测 mock 不打真网
- 生产：经 `scripts/deploy-shared-uploads.js` 重建 `agent-platform-api`；compose `.env` 写入 `COMMANDER_*`

## 验收

```text
curl -s https://www.yoto.work/agent-platform/api/tools/status
# commander_agent.online === true
```

## 未做

- Web 前端静态资源未单独部署（生产页依赖本机 Vite 或后续 FE 发布）
- P0 抖音真实采集 MCP 仍待启动
