# Handoff：社媒黑盒 MCP 实现开工

> 2026-07-24  
> **PARKED（2026-07-24 晚）**：不做收口；恢复指引见 `docs/handoffs/2026-07-24-social-mcp-parked.md`。当前迭代回到 **P0 抖音**。

## 已完成（本仓）

- MCP：`social_automedia_client.py` + `platform_mcp` tools（list/submit/status）
- Skill：`skills/social-media-publish/` + registry + `SKILL_PLANS` + finalize 轮询
- API：`POST /tasks/social-publish`、`/tasks/upload-media`；报告 `kind=social_publish`
- FE：`/tasks/social` · 侧栏「社媒发布」· 报告视图
- Env：`.env.example` → `SOCIAL_UPLOAD_API_BASE` / `SOCIAL_UPLOAD_TOKEN`

## 上游（social-auto-upload，须部署）

- `publish_jobs` + `job_id` 回传 + `GET /publish/jobs/<id>`
- `postVideo` / `postVideoBatch` `@login_required`
- 见 `docs/RELEASE-publish-job-status.md`（automedia 仓）

## 上线前

1. 部署 automedia（含 Task 0）
2. MCP 容器注入 `SOCIAL_UPLOAD_TOKEN`（`/auth/login` 取 JWT）
3. 肉机 login-agent 在线并绑定账号
4. E2E：非 TK 一条 + TK 离线失败

## 未做

- 生产 E2E / 热补丁部署（待运维）
- B站等 P2-B
