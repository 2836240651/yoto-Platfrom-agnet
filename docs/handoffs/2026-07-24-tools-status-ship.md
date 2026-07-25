# Handoff：工具状态收口与上线

> 2026-07-24 · `feat/tools-status-probe`

## 完成

- `GET /api/tools/status`：MCP + 肉机探测；`COMMANDER_*` 仅从 Settings（`.env` / 进程 env）读取，无 `os.environ` 副作用
- FE：侧栏「工具状态」→ `/tools`；单测 mock 不打真网
- Git：`feat/tools-status-probe` @ `6d15730`
- 生产：compose `.env` 已含 `COMMANDER_*`；`docker compose build` 卡在 pip（磁盘 87%）后改为 **现有镜像 + docker cp 热补丁** 上线

## 验收（已通过 · 2026-07-24）

```text
curl -s https://www.yoto.work/agent-platform/api/tools/status
# ok=true；commander_agent.online=true；detail=在线
```

## 未做 / 后续

- 正式 `docker compose build` 镜像层尚未完成（磁盘紧张 / pip 慢）；热补丁重启丢，需择机重建镜像
- Web 前端静态资源未单独部署（`/tools` UI 依赖本机 Vite 或后续 FE 发布）
- P0 抖音真实采集 MCP 仍待启动
