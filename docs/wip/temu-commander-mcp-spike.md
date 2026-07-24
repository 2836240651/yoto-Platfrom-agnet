# Spike：Temu → Commander `product_issue`（只读核对）

**日期：** 2026-07-23  
**目的：** 确认 agent-platform 用 **≤2 个 MCP** 包装 Commander Temu 上架黑盒所需的真实 API / 鉴权 / 轮询字段，再写 P1-2 执行计划。  
**范围：** 只读核对 sibling `commander-server` / `commander-web`；**未**对本仓写 MCP、未对 Commander 发真实请求。  
**结论摘要：** 接口可包装；最大缺口是 **`product_issue` 成功响应不返回 `taskId`**，状态只能靠 `task_list` 推断。

---

## 1. 契约对照（相对本仓 Spec）

| 项 | 标记 | 说明 |
|----|------|------|
| Temu 整段黑盒 = Commander Job | **已满足（外部）** | Server `AgentProductIssue` → Worker `product_issue` → Lyncr（缺图/缺标题时）→ Agent 店小秘 |
| 本仓 Temu MCP | **规范有、仓库无** | `config/mcp.json` 仅 `example_tools`；无 Commander 客户端 |
| Skill 只编排不重写引擎 | **规范有、仓库无** | 尚无 Temu Skill / schema |
| Job ≤ 2 MCP | **可设计** | 建议：`submit` + `status`（见 §5） |

---

## 2. HTTP 面（可调入口）

基路径：`/api/v1`（`commander-web` → `commander-server`）。

| 用途 | 方法 | 路径 | Body | 鉴权 |
|------|------|------|------|------|
| 登录拿 token | POST | `/user/login` | JSON `username` + `password` | 否 |
| 续期 | POST | `/user/refresh` | — | Bearer |
| 上架预检 | POST | `/agent/product_issue_precheck` | JSON `agent_id`, `shop_id`, `platform` | Bearer |
| **提交上架** | POST | `/agent/product_issue` | **multipart**：`file` + `shop_id` + `platform` + `agent` | Bearer |
| 任务列表/状态 | POST | `/agent/task_list` | JSON 见下 | Bearer |
| 店铺列表 | POST | `/agent/shop_list` | JSON `agent_id`, `platform` | Bearer |
| Agent 列表 | POST | `/agent/list` | — | Bearer |
| 重试 / 删除 | POST | `/agent/retask` · `/agent/task_delete` | `taskId` / `task_id[]` | Bearer |

前端对照：`commander-web` `src/api/modules/agent.js`（`productIssue` / `getAgentTaskList`）。

### 2.1 提交字段（强制）

`AgentProductIssueRequest`（form）：

- `shop_id` — 店铺 ID  
- `platform` — 如 `temu`  
- `agent` — **Agent 实例 ID**（与 `agent_id` 命名不一致，multipart 字段名是 `agent`）  
- `file` — xlsx（`FormFile("file")`）；父体须嵌主图；状态列区分父体/子体  

成功时 `data` 仅为文案：`"产品发布任务已提交,请稍后查看结果"`。  
**不返回 `taskId`。** 同一 Excel 多「编号」会循环多次 `CreateNewTask`，仍无 ID 列表。

### 2.2 任务列表（状态观测）

`AgentTaskListRequest`：

| 字段 | 含义 |
|------|------|
| `agent_id` | 可选筛选 |
| `platform` | 可选，前端默认 `temu` |
| `page` / `page_size` | 分页（page_size 默认 10，上限 100） |
| `list_scope` | `active`（排除失败上架）\| `failed_listing` \| `all` |

列表项形状（`AgentMessage`，列表侧会去掉 `send.imageRawUrl`）：

| 字段 | 说明 |
|------|------|
| `taskId` | 任务 ID（仅在 list / DB 侧存在） |
| `agentId` / `platform` / `protocol` | `protocol` = `product_issue` |
| `status` | `processing` \| `success` \| `failed` \| `cancelled` |
| `message` | 人话进度/失败原因 |
| `tasksAhead` | 仅 processing：排队位数 |
| `createAt` / `runAt` | 时间戳 |
| `send` / `receive` | 载荷摘要（无大图） |

### 2.3 响应信封

统一 `{ "code": 0, "msg": "success", "data": ... }`。业务成功看 **`code === 0`**。  
登录成功：`data` 为 **token 字符串**（非 `{token: ...}`）。  
续期：`data.token`；响应头可能带 `X-Access-Token`。

### 2.4 鉴权

- 请求头：`Authorization: Bearer <token>`（下载类也可 `?access_token=`）  
- Redis 会话 + JWT；过期文案：`登录已过期，请重新登录`  
- Agent 模块除 `GET /agent/online` 外均需 `Authentication`

---

## 3. 黑盒边界（勿在本仓重做）

一次 `product_issue` 在 Commander 内已包含：Excel 解析与笛卡尔积校验、缺标题/缺五图时的 Lyncr 视觉与文案/轮播生图、WS 下发 Agent、店小秘上架。  
本仓 MCP **只**做 HTTP 客户端 + 可观测状态；Skill **只**做意图/缺参确认/调用/人话总结。

---

## 4. 环境变量建议（未写入 `.env.example`，待阻塞拍板）

| 键 | 用途 |
|----|------|
| `COMMANDER_API_BASE` | 如 `https://<host>/api/v1`（勿硬编码本机路径） |
| `COMMANDER_ACCESS_TOKEN` | 优先：长期/运维注入的 Bearer；或 |
| `COMMANDER_USERNAME` / `COMMANDER_PASSWORD` | MCP 内登录换 token（含密钥风险，需约定） |
| `COMMANDER_DEFAULT_AGENT_ID` | 默认 `agent` 表单值 |
| `COMMANDER_DEFAULT_SHOP_ID` | 可选默认店铺 |
| `COMMANDER_DEFAULT_PLATFORM` | 默认 `temu` |

---

## 5. MCP 形状草案（≤2 tools，未实现）

| Tool | 输入（草案） | 输出（草案） |
|------|--------------|--------------|
| `temu_product_issue_submit` | `file_path` 或 workspace `file_id`；`shop_id`；`agent_id`；`platform`；可选 `precheck: bool` | `submitted: true`；`hint`；**可选**提交后立刻 `task_list` 摘到的候选 `taskId[]` |
| `temu_product_issue_status` | `agent_id`；`platform`；可选 `task_id`；`list_scope` | `status` / `message` / `tasksAhead` / 列表摘要 |

失败必须原样上抛 `msg`，禁止伪装成功。

---

## 6. 阻塞与歧义（写执行计划前须拍板）

| ID | 问题 | 影响 |
|----|------|------|
| **T1** | 运行时 `COMMANDER_API_BASE` 是哪套环境？ | 无基址无法 spike 联调 |
| **T2** | 鉴权用固定 `COMMANDER_ACCESS_TOKEN`，还是 MCP 用账号登录？ | 密钥落盘与会话过期策略 |
| **T3** | 提交不返回 `taskId`：接受「提交后按 agent+platform 取最新 processing」，还是先改 Commander 返回 ID？（改 Commander 超出本仓默认范围） | status 工具可观测性 |
| **T4** | `agent_id` / `shop_id`：环境默认 vs 每次 Skill 向用户确认？ | Skill schema 与 FE |
| **T5** | Excel 从哪来：本地 path、Workspace 上传、还是仅 URL？ | submit 输入契约 |
| **T6** | 是否把 `precheck` 并入 submit（仍算 1 个 tool），还是单独暴露？（合计仍 ≤2） | UX vs 工具数 |

**未做：** 对真实 Commander 发登录 / 上传 / 轮询（需 T1+T2）。

---

## 7. 建议下一步

1. 用户拍板 **T1–T6**（至少 T1/T2/T3）。  
2. 可选：用测试账号对目标环境做一次最小联调（login → shop_list → 小表 precheck；**不上真实店**可停在 precheck）。  
3. 再写执行计划：`docs/wip/` 或 `docs/handoffs/YYYY-MM-DD-temu-commander-mcp.md`，按 P1-2 切 MCP → registry →（薄）Skill/schema → 单测。  
4. **暂不**动抖音 P0-2；与当前「先 Temu MCP」一致。

---

## 8. 源码锚点（sibling，勿 import）

- `commander-server`：`internal/services/agent_product_issue.go`、`agent_task_list.go`、`agent_product_issue_precheck.go`、`internal/manager/WorkerManager.go`（`CreateNewTask`）、`internal/router/register.go`（`AgentModuleRegister`）、`internal/middleware/Authentication.go`  
- `commander-web`：`src/api/modules/agent.js`、`src/api/request.js`（Bearer + `X-Access-Token`）
