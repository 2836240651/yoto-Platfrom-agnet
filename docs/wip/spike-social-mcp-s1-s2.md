# Spike 结论：社媒 MCP · S1/S2（及 S3–S5）

> 2026-07-24 · 只读核对 + 现网探针 · **未改业务代码**

## 探针

| 调用 | 结果 |
|------|------|
| `GET /login-agent/status` 无 token | `401` 未登录 |
| `GET /getAccounts` 无 token | `401` |
| `POST /auth/login` 错密 | `401` 用户名或密码错误（端点可用） |
| `POST /postVideo` 无 token + 假文件 | `500` 视频不存在（**未鉴权仍当 owner_id=1 执行**） |

源码：`postVideo` **无** `@login_required`；`resolve_current_user_id(required=False) or 1`。

---

## S2 鉴权 → **关闭**

| 项 | 定论 |
|----|------|
| 形态 | `Authorization: Bearer <JWT>`（`utils/app_auth.create_access_token`，默认 7 天） |
| 获取 | `POST /auth/login` `{username,password}` → `data.token` |
| MCP 环境变量 | `SOCIAL_UPLOAD_API_BASE=https://automedia.yoto.work`（或内网等价）<br>`SOCIAL_UPLOAD_TOKEN=<长期 JWT>`（运维登录后写入；过期再换） |
| 规则 | MCP **一律带 token**；缺 token → tool 失败，禁止匿名走 user 1 |
| 上游建议（非本仓阻塞） | `postVideo` / `postVideoBatch` 加 `@login_required`（安全债） |

不采用每次 MCP 调用户名密码（密钥面更大）；不把密码写进 Skill。

---

## S1 终态 → **关闭（带上游前置）**

| 项 | 定论 |
|----|------|
| 现状 | `postVideo` 成功体仅 `data.publish_runtime`（如 `local_queued`）；**无 job_id** |
| Hub | `dispatch_agent_job` / `get_job` 存在，但是内存队列；**无**面向运营的 `GET` 状态 API |
| 本仓不可独自「真终态」 | 无 id 可轮询 |

**决议（两刀）：**

1. **上游必改（social-auto-upload，Task 0）**  
   - `publish_with_runtime` / `postVideo` 在 `local_queued` 时返回可追踪 `job_id`(s)  
   - 新增 `GET`（`@login_required`）：按 `job_id` 查 `pending|running|success|failed` + 错误信息  
2. **agent-platform MCP**  
   - `social_publish_submit` 透传 `job_id` / `publish_runtime`  
   - `social_publish_status` 调上述 GET；上游未上线前 **禁止** 把 `local_queued` 当成业务 success  

TikTok `runtime=agent_required` → MCP/`Skill` **failed**（已有现网语义，无需等终态 API）。

---

## S3 平台范围 → **关闭**

首批仅 type **1–5**（小红书/视频号/抖音/快手/TikTok）。B站/百家号/YouTube → P2-B。

## S4 素材 → **关闭**

只走 automedia `POST /upload`（或已有 `file_records` 路径）；**不**打通本仓 `UPLOAD_ROOT`。

## S5 同机 Chrome → **关闭（文档级）**

login-agent 与 Commander Agent **分进程**；尽量错峰跑浏览器重任务；账号 profile 各自绑定。冲突时优先查肉机任务队列，不改本仓 Runtime。

---

## 对实现计划的含义

- 可写完整计划；**强验收（可观测 success/failed）依赖上游 Task 0**。  
- 本仓可与上游并行：先接线 list/submit（含 TK 离线失败）+ status 客户端；上游未就绪时 status 返回 `upstream_status_unavailable`，任务保持非成功终态。  
- **未批准「开工」前不编码。**
