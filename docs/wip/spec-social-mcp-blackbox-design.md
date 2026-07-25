# 设计定稿：社媒发布黑盒 MCP（social-auto-upload）

> 状态：**已定稿（2026-07-24）** · 用户确认「按此定稿」  
> 对照：`docs/spec-architecture-contract.md`（P2 社媒）；`docs/wip/spec-business-scenarios-llm-tool.md` §5  
> 外部仓：`D:\multiPlaformUpLoad\social-auto-upload`（现网 `automedia.yoto.work`）  
> **优先级例外**：用户批准在 Temu 黑盒已验后**提前做 P2 社媒**（须交接写明，避免后续 Agent 误判违规）。

---

## 1. 目标

agent-platform 将 **social-auto-upload 整段**封为黑盒 Job：

```text
运营确认平台/账号/素材
  → Skill（编排，可选 LLM 只做文案前置）
  → MCP（≤2 主 tool + 可选 list）
  → automedia.yoto.work
  → 肉机同机 login-agent（Playwright）
```

| 允许 | 禁止 |
|------|------|
| MCP HTTP 调 automedia；Skill 缺参确认/人话 | 本仓重写 Playwright / uploader |
| 浏览器跑在公司肉机（与 Temu Commander Agent **同机不同进程**） | 在 Linux automedia 容器内对 TikTok 静默回退 |
| Cookie/账号留在 automedia | Cookie 进 prompt / Skill 正文 |

---

## 2. 拓扑（已拍板）

| 组件 | 位置 | 职责 |
|------|------|------|
| Skill + MCP | agent-platform | Schema、编排、失败人话 |
| automedia API | `automedia.yoto.work`（`:5409` / 反代） | 账号库、上传、`postVideo`、派发 |
| login-agent | **Temu「肉机」同 Windows** | 浏览器发布；账号**已登录**，只需安装助手并连接/绑定 |
| Commander Agent | 同机另一进程 | 仅 Temu/店小秘；与 login-agent 并存 |

账号侧：**不重新扫码**（用户确认）；运维 = 装便携包 → 网页连接 → 账号绑定该助手。

---

## 3. MCP 契约

### 3.1 Tools

| Tool | 作用 | 上游 |
|------|------|------|
| `social_list_accounts`（可选） | 列账号 / 助手是否在线 | `GET /getAccounts`、`/getValidAccounts`、login-agent status |
| `social_publish_submit` | 上传（若需）+ 发布 | `POST /upload`·`/uploadSave` + `POST /postVideo` 或 `/postVideoBatch` |
| `social_publish_status` | 查结果 | 依赖上游返回 `job_id` + GET（见 spike）；未就绪禁止报业务 success |

环境变量：`SOCIAL_UPLOAD_API_BASE` · `SOCIAL_UPLOAD_TOKEN`（Bearer JWT）。

### 3.2 平台枚举（产品「全部」）

Web/`postVideo` 主路径 `type`：

| type | 平台 | 助手 | 服务器回退 |
|------|------|------|------------|
| 1 | 小红书 | 优先 | 允许（现网） |
| 2 | 视频号 | 优先 | 允许 |
| 3 | 抖音 | 优先 | 允许 |
| 4 | 快手 | 优先 | 允许 |
| 5 | TikTok | **必须在线** | **禁止**；离线 → MCP 明确失败 |

另：仓内另有 B 站 / 百家号 / YouTube uploader 与部分 CLI Skill；**是否进同一 `postVideo` HTTP 面待 gap-check**。定稿口径：

- **P2-A（首批接线）**：type 1–5 全开（与 automedia 账号页一致）  
- **P2-B（补齐）**：B 站 / 百家号 / YouTube 若 HTTP 未齐，单列 spike 后再扩枚举，**不**在本仓自研

### 3.3 Skill

- id：`social-media-publish`  
- 黑盒：图上 1～2 步；`micro_budget=1`；等待在 handler/MCP 内  
- 可选 LLM：仅文案/标题前置（**light** 或会话 `model_id`）；发布成败**代码**判定  
- FE：专用页或 Composer 入口；黑盒页灰掉模型选择器（对齐 Temu）

---

## 4. 验收

1. 肉机 login-agent 已连接，账号已绑定  
2. 智能体：素材 + 平台 + 账号 → submit 派发成功  
3. TikTok：助手离线 → 任务 **failed**（非假完成）  
4. 至少 1 个非 TK + 1 次 TK（助手在线）可观测成功/失败回执  
5. `MCP_ALLOW_STUB_FALLBACK=false` 下禁止 stub 伪装成功  

---

## 5. 风险

- 终态：上游未补 job API 前只能 `accepted`，不可伪造成功  
- 同机双 Agent 抢 Chrome → 分进程 + 错峰（S5）  
- 「全部」→ 首批 1–5；B站等 P2-B  

阻塞 S1–S5 已关闭：`docs/wip/spike-social-mcp-s1-s2.md`。

---

## 6. 文档关系

| 文档 | 作用 |
|------|------|
| 本文 | 设计定稿 |
| `docs/wip/spike-social-mcp-s1-s2.md` | S1/S2 spike 结论 |
| `docs/wip/p2-social-mcp-contract-gap-check.md` | 契约核对 |
| `docs/wip/social-mcp-implementation-plan.md` | 实现计划 |
| `docs/handoffs/2026-07-24-social-mcp-design.md` | 交接 / P2 例外 |
| 场景 WIP §5 | LLM/Tool 边界 |
