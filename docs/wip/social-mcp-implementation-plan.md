# Social Media Publish MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `executing-plans` to implement task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.  
> **Design:** `docs/wip/spec-social-mcp-blackbox-design.md`  
> **Spike:** `docs/wip/spike-social-mcp-s1-s2.md`  
> **Gap:** `docs/wip/p2-social-mcp-contract-gap-check.md`  
> **Status:** 实现中（2026-07-24 开工）· Task 0–3 已落代码；Task 4 待部署/E2E

**Goal:** 将 automedia（social-auto-upload）封为黑盒 Skill+MCP：账号列表 → 上传/发布 → 状态轮询；浏览器在 Temu 肉机 login-agent；首批平台 type 1–5。

**Architecture:** 对齐 Temu：`platform_mcp` 增 HTTP client + ≤3 tools（list 可选）→ `tool_registry` → Skill `social-media-publish`（`SKILL_PLANS` 1～2 步）→ FE 入口；成败代码判定，禁止 stub 假成功。

**Tech Stack:** FastMCP / httpx · FastAPI · React/Vite · pytest · 上游 Flask automedia

## Global Constraints

- Skill + MCP 黑盒；禁止本仓 Playwright / uploader  
- 图步默认 submit→（status）；`micro_budget=1`；等待在 handler/MCP 内  
- TikTok 助手离线 → **failed**（`agent_required`）  
- 鉴权：`SOCIAL_UPLOAD_API_BASE` + `SOCIAL_UPLOAD_TOKEN`（Bearer）；缺 token 失败  
- 素材只走 automedia `/upload`；不接本仓 `UPLOAD_ROOT`  
- 首批 type ∈ {1,2,3,4,5}；`MCP_ALLOW_STUB_FALLBACK=false` 下禁止伪造成功  
- LLM：可选文案前置 light/会话钉扎；**不用** LLM 判发布成败；黑盒页灰掉模型选择器  
- P2 提前为例外（handoff 已记）；勿重开抖音采集/域模型等搁置项

---

## File map

| 路径 | 职责 |
|------|------|
| **上游** `social-auto-upload`：`publish_dispatch.py` / `sau_backend.py` / hub | Task 0：`job_id` + GET status；建议 `postVideo` `@login_required` |
| `mcp/servers/social_automedia_client.py` | HTTP 封装（新建） |
| `mcp/servers/platform_mcp_gateway.py` | 注册 MCP tools |
| `config/tool_registry.json` · `config/mcp.json` · `mcp.docker.json` | 映射 |
| `skills/social-media-publish/` | SKILL + schema |
| `src/agent/constants.py` | `SKILL_PLANS` |
| `src/agent/tools/arg_builders.py` · handlers / report | 参数与报告 `kind` |
| `.env.example` · Settings | 环境变量 |
| `apps/web` 入口页 / Composer | 业务入口 + blackbox |
| `tests/unit_tests/test_social_*` | mock 单测 |

---

## Task 0: 上游 automedia — job_id + status API

**Repo:** `D:\multiPlaformUpLoad\social-auto-upload`（sibling，非本仓）

**Goal:** Workspace 可轮询发布终态。

- [ ] `publish_with_runtime` / agent worker：每个派发任务保留稳定 `job_id`（持久化或 hub 可查询，避免纯火即忘）
- [ ] `POST /postVideo`（及 Batch）成功响应增加：`job_id` 或 `job_ids[]`、`publish_runtime`
- [ ] 新增 `GET /publish/jobs/<job_id>`（或等价）`@login_required` → `{status: pending|running|success|failed, error?, runtime?}`
- [ ] （强烈建议）`postVideo` / `postVideoBatch` 加 `@login_required`
- [ ] 本地/staging：助手在线发一条非 TK → status 到 success/failed；TK 助手离线 → 400 `agent_required`
- [ ] 在 automedia 仓留短 RELEASE/handoff；本仓 spike 文档链过去

**验收：** 持 Bearer 可 submit→poll 到明确终态；无 token → 401。

**并行：** Task 1–2 可先 mock status；接真终态前 Skill **不得** 把 `local_queued` 标为任务成功。

---

## Task 1: MCP client + tools（本仓）

- [ ] 新增 `mcp/servers/social_automedia_client.py`：base URL、Bearer、超时；方法 `list_accounts`、`login_agent_status`、`upload`、`publish_submit`、`publish_status`
- [ ] 缺 `SOCIAL_UPLOAD_TOKEN` → 返回 `{ok:false, error:"…"}`，不打匿名请求
- [ ] `platform_mcp_gateway.py` 注册：
  - `social_list_accounts`
  - `social_publish_submit`（file 路径或已上传名 + type + account_list + title/tags…）
  - `social_publish_status`（`job_id`）
- [ ] `.env.example`：`SOCIAL_UPLOAD_API_BASE`、`SOCIAL_UPLOAD_TOKEN`
- [ ] Settings（若 API tools-status 要展示）：只读探测 login-agent online（可选，仿 Commander）
- [ ] 单测：httpx mock — token 缺失、TK `agent_required`、status success/failed

**验收：** `python -m pytest tests/unit_tests/test_social_automedia_client.py -q` 通过。

---

## Task 2: Skill + registry + Runtime 接线

- [ ] `skills/social-media-publish/SKILL.md` + `schema/input.json` + `output.json`
- [ ] `config/tool_registry.json`：三 tool → `server: platform_mcp`，`allow_in_skills` 含本 Skill
- [ ] `SKILL_PLANS`：submit → finalize（status 轮询在 submit handler **内**完成，或两步 submit+status 且 micro_budget=1）
- [ ] arg_builder / step_handler：代码拼报告 `kind: social_publish`（或既定命名）
- [ ] `BLACKBOX_SKILLS` 纳入；禁止调 LLM 做成败
- [ ] 单测：plan 存在、registry 非 null、validate report

**验收：** `tests/unit_tests/test_social_publish_skill.py` 通过；与 Temu 测试对称。

---

## Task 3: API / FE 入口

- [ ] 创建任务接受 `skill_id=social-media-publish` + 输入 schema 字段
- [ ] FE：专用页或 Composer 入口；`blackbox` 灰掉模型选择器
- [ ] 报告视图：runtime / job_id / 平台 / 账号 / 成功失败（无工程黑话）
- [ ] （可选）工具状态页增加 automedia login-agent 探针

**验收：** 业务视图可提交并看到非 stub 报告结构（联调前可用 mock）。

---

## Task 4: 部署与 E2E

- [ ] 生产 MCP 容器注入 `SOCIAL_UPLOAD_*`（勿提交实值）
- [ ] 肉机：login-agent 已连接；账号绑定；与 Commander 错峰
- [ ] E2E：`MCP_ALLOW_STUB_FALLBACK=false`
  - [ ] 非 TK 一条：submit → status success（依赖 Task 0）
  - [ ] TK 助手离线：任务 **failed**
  - [ ] TK 助手在线（可选）：success 或明确 failed（非假完成）
- [ ] handoff：`docs/handoffs/YYYY-MM-DD-social-mcp-ship.md`

**验收：** 满足设计文档 §4。

---

## Out of scope（本计划不做）

- B站 / 百家号 / YouTube（P2-B）  
- 本仓重写社媒引擎、Cookie 进 prompt、多轮 replan 抬发布质量  
- 打通 agent-platform `UPLOAD_ROOT` 与 automedia 素材库  

---

## 开工门槛

1. 用户明确说「开工」  
2. 已知 `SOCIAL_UPLOAD_TOKEN` 写入本地/生产密钥侧（或开发用 mock）  
3. Task 0 有人认领或明确接受「无终态则任务不标成功」的临时语义  

**推荐开工顺序：** Task 0（上游）∥ Task 1 → Task 2 → Task 3 → Task 4。
