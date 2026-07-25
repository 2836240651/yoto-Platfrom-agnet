# Handoff：社媒 MCP 暂存（暂停收口）

> 2026-07-24 · **PARKED**  
> 决定：先不做社媒收口 / 生产 E2E；工作区改动保留在分支工作树，进度以本文 + 既有设计文档为准。  
> 回到主链路：**P0 抖音 `douyin-keyword-research`（Skill + 蝉妈妈个人版 Cookie 采集 MCP）**。

## 为何暂存

- 架构契约优先级：P0 抖音闭环 > P1 Temu > P2 社媒。  
- 社媒本仓实现已基本齐，但上游 automedia（`job_id` / 鉴权加固）与生产部署未收口；继续磨社媒会挤占主链路。

## 已有文档（勿丢）

| 文档 | 用途 |
|------|------|
| `docs/wip/spec-social-mcp-blackbox-design.md` | 黑盒设计 |
| `docs/wip/spike-social-mcp-s1-s2.md` | spike |
| `docs/wip/p2-social-mcp-contract-gap-check.md` | 契约核对（阻塞已关） |
| `docs/wip/social-mcp-implementation-plan.md` | 实现计划 |
| `docs/handoffs/2026-07-24-social-mcp-design.md` | 设计交接 |
| `docs/handoffs/2026-07-24-social-mcp-ship.md` | 开工清单（上游债） |

## 工作树快照（未提交 · `feat/tools-status-probe`）

### 未跟踪（社媒主件）

- `skills/social-media-publish/`
- `mcp/servers/social_automedia_client.py`
- `apps/web/src/pages/SocialPublishPage.tsx`
- `apps/web/src/components/SocialPublishReportView.tsx`
- `tests/unit_tests/test_social_automedia_client.py`
- `tests/unit_tests/test_social_publish_skill.py`
- `scripts/_tmp_set_social_token.sh` · `scripts/_tmp_social_token_and_e2e.sh`（临时脚本，收口时评估是否删除）
- 上述 `docs/wip/*social*` / `docs/handoffs/*social*`

### 已改动且含社媒接线（与 Temu/工具状态可能交织）

- `config/tool_registry.json`（`social_*` 别名）
- `mcp/servers/platform_mcp_gateway.py`
- `src/agent/constants.py`（`social-media-publish` plan / BLACKBOX）
- `src/agent/tools/step_handlers.py` · `arg_builders.py`
- `src/agent/nodes/{generate,init_task,route,validate}.py` · `state.py`
- `apps/api/app/{routers/tasks,schemas/tasks,services/*,store/task_store}.py`
- `apps/web/src/{App,Layout,api/client,types/task,pages/*Detail*}.tsx` 等
- `.env.example`（`SOCIAL_UPLOAD_*`）

### 分支已提交基线（非社媒）

- `6d15730` · 工具状态 `GET /api/tools/status`（见 `2026-07-24-tools-status-ship.md`）

## 恢复时检查单

1. 确认 automedia 已部署：`job_id` + `GET /publish/jobs/<id>`；`postVideo*` 鉴权。  
2. 注入 `SOCIAL_UPLOAD_API_BASE` / `SOCIAL_UPLOAD_TOKEN`。  
3. 肉机 login-agent 在线。  
4. 对本仓工作树做一次 diff 审阅（避免与后续抖音改动冲突）。  
5. E2E：非 TK 成功一条 + TK 离线失败语义。  
6. 正式提交/热补丁前对照 `2026-07-24-social-mcp-ship.md`。

## 明确不做（本阶段）

- 不 commit / 不 PR 社媒收口  
- 不部署社媒热补丁  
- 不把社媒当当前迭代验收项
