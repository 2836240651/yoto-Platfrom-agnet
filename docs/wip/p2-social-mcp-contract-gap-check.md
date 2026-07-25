# P2 社媒 MCP 契约核对（Gap Check）

> 状态：**阻塞已关闭（spike 后）** · 2026-07-24  
> 对照：`docs/wip/spec-social-mcp-blackbox-design.md`；spike：`docs/wip/spike-social-mcp-s1-s2.md`  
> **不是执行计划** → 实现计划见 `docs/wip/social-mcp-implementation-plan.md`

标记：已满足 / stub / 规范有、仓库无 / 已关闭（决议）

---

## 0. 范围

- 全平台黑盒；浏览器在 Temu 肉机同机 login-agent；账号已登  
- **P2 提前**（用户批准）；首批 type **1–5**

---

## 1. 外部系统（social-auto-upload）

| 检查项 | 标记 | 证据 / 决议 |
|--------|------|-------------|
| 现网 HTTP | **已满足** | `automedia.yoto.work` |
| 发布 / 上传 / 账号 | **已满足** | `postVideo`、`upload`、`getAccounts` |
| type 1–5 | **已满足** | Web type 表 |
| B站等 HTTP | **P2-B** | 首批不做 |
| TikTok 禁回退 | **已满足** | `agent_required` → 400 |
| 客户端 publish 终态 API | **规范有、上游待补** | spike：无 job_id；Task 0 补 GET |
| Bearer 鉴权 | **已满足** | `/auth/login`；`getAccounts` 要 token |
| `postVideo` 强制登录 | **上游债** | 现无 `@login_required`；MCP 侧强制带 token |

---

## 2. agent-platform 本仓

| 检查项 | 标记 |
|--------|------|
| Skill / registry / MCP tools / FE / `.env.example` | **规范有、仓库无**（计划内落地） |

---

## 3. 阻塞表

| ID | 状态 | 决议 |
|----|------|------|
| **S1** | **已关闭** | 终态依赖上游返回 `job_id` + GET；未就绪禁止报业务 success |
| **S2** | **已关闭** | `SOCIAL_UPLOAD_API_BASE` + `SOCIAL_UPLOAD_TOKEN`（Bearer） |
| **S3** | **已关闭** | 首批仅 1–5 |
| **S4** | **已关闭** | 素材只走 automedia `/upload` |
| **S5** | **已关闭** | 同机分进程 + 错峰；文档约定 |

---

## 4. 结论

可写实现计划并在批准后开工。强 E2E（可观测 success）与 **social-auto-upload Task 0** 绑定；本仓可先接线 list/submit + TK 硬失败。
