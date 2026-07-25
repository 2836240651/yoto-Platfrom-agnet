# 抖音采集 · 肉机 Worker（服务器下发 · 本机执行）

> 状态：现行 · 2026-07-25  
> **作废**旧方案「客户端直连肉机 MCP HTTP」。对齐 Temu：`platform_mcp` 在服务器，执行器在肉机出站。

## 架构锁定：双肉机手（复用角色，不复用 Commander Agent）

Temu 上架与抖音采集是**同一角色**（服务器入队 → 肉机出站领取 → 本地执行 → complete），**不是同一个进程 / 协议**。

| 手 | 进程 | 控制面 | 浏览器 |
| -- | ---- | ------ | ------ |
| Temu / 1688… | `commander-agent`（Wails/Go） | Commander `yoto/api/v1` → **WebSocket** `platform+protocol` | go-rod 自有 profile |
| 抖音蝉妈妈 | 本仓 `scripts/douyin_meat_worker.py` | `platform_mcp` **HTTP** `/worker/*` | Playwright + `DOUYIN_CHROME_USER_DATA_DIR` |

**明确不做：**

- 在 `commander-agent` 增加 `douyin_*` protocol / 把蝉妈妈塞进 Dispatcher
- 把蝉妈妈 Cookie 迁入 rod 默认 profile（抢登录 / 互相踢）
- 客户端直连肉机开 MCP 端口
- 用 Commander `product_issue` 冒充采集任务

同机运维入口：`scripts/start-meat-hands.bat`（双启）+ `scripts/meat_hands_status.py`（双路探测）。运营说明见 [`douyin-meat-ops-runbook.md`](./douyin-meat-ops-runbook.md)。交接：[`docs/handoffs/2026-07-25-douyin-dual-meat-hands.md`](../handoffs/2026-07-25-douyin-dual-meat-hands.md)。

## 数据流

```
用户 Web → 服务器 Agent/API → platform_mcp（douyin_collect_hot_keywords）
  → Job 队列（DOUYIN_JOB_DIR）
← 肉机 Worker 出站 claim / complete
  → 本机 Playwright 蝉妈妈（DOUYIN_CHROME_USER_DATA_DIR）
→ 真实 keywords；报告 data_source.source=mcp
```


| 角色       | 行为                                                             |
| -------- | -------------------------------------------------------------- |
| 用户 / 智能体 | 只连服务器（`https://www.yoto.work/agent-platform` + `platform-mcp`） |
| 本机肉机     | 只**出站**领任务；**不**对外开 MCP 端口                                     |
| 登录态      | 仅留在肉机 Chrome profile；禁止回传 Cookie                               |


不复用 Commander `product_issue`；独立轻量队列（同角色、不同协议）。

## 环境变量怎么填（对照那几行 `$env:`）

以前示例里的占位符含义如下；**推荐全部写进本机 `.env`（已 gitignore）**，部署/启动脚本会自动读，不必每次手敲 `$env:`。


| 旧写法                                                             | `.env` 键                    | 是什么                                      | 怎么填                                                                                              |
| --------------------------------------------------------------- | --------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `$env:P = '<ssh>'`                                              | `DEPLOY_PASS`（或临时 `$env:P`） | 部署机 **SSH 密码**（`root@124.223.27.98`）     | 从 `D:\dev\workspace\scripts\_ssh-probe\` 同步到本仓 `.env`（**勿提交 git**）                               |
| `$env:DOUYIN_WORKER_TOKEN = '<强随机>'`                            | `DOUYIN_WORKER_TOKEN`       | 肉机 Worker ↔ 服务器队列的。 **共享密钥**（Bearer）     | 本机已用 `python scripts/_fill_douyin_worker_env.py` **生成并写入 `.env`**；部署脚本会原样写到服务器 `platform-mcp` 容器 |
| `$env:COMMANDER_ACCESS_TOKEN = '<已有则可>'`                        | `COMMANDER_ACCESS_TOKEN`    | Temu/Commander API Token（与抖音队列无关，但同网关共用） | **沿用本机 `.env` 已有值**即可；空则 Temu 工具不可用，抖音队列仍可工作                                                     |
| `$env:DOUYIN_WORKER_URL = 'https://www.yoto.work/platform-mcp'` | `DOUYIN_WORKER_URL`         | Worker 出站基址（**不要**加 `/mcp`）              | 固定填 `https://www.yoto.work/platform-mcp`（已写入 `.env`）                                             |
| （bat 里）`DOUYIN_WORKER_ID`                                       | `DOUYIN_WORKER_ID`          | Worker 名称                                | 默认 `肉机`（已写入）                                                                                     |


其它常用键：


| 键                             | 说明                 | 默认                              |
| ----------------------------- | ------------------ | ------------------------------- |
| `DEPLOY_HOST` / `DEPLOY_USER` | SSH 目标             | `124.223.27.98` / `root`        |
| `DOUYIN_CHROME_USER_DATA_DIR` | 蝉妈妈 Chrome profile | 空 → 仓库 `.local/chanmama-chrome` |
| `DOUYIN_JOB_DIR`（仅服务器容器）      | 任务落盘目录             | `/data/douyin-jobs`             |


**禁止**把 `DEPLOY_PASS` / `DOUYIN_WORKER_TOKEN` / `COMMANDER_ACCESS_TOKEN` 写进 git、Spec 正文或聊天记录长久粘贴。

### 本机一次填好

```powershell
cd D:\reverselab\agent-platform
python scripts\_fill_douyin_worker_env.py
# 然后用编辑器打开 .env，只补这一项：
# DEPLOY_PASS=你的SSH密码
```

核对（不打印密钥）：

```powershell
python scripts\load_env_keys.py DEPLOY_PASS DOUYIN_WORKER_TOKEN DOUYIN_WORKER_URL COMMANDER_ACCESS_TOKEN
# 应看到 DEPLOY_PASS=...（非空）、DOUYIN_WORKER_TOKEN=...（非空）
```

## 一键部署 + 启动肉机

1. `.env` 里 `DEPLOY_PASS` 已填非空
2. **就地升级**已有网关容器 `platform-mcp`（Temu/社媒仍在同一进程；抖音队列工具挂上去）。**不**另开第二套 MCP。URL 不变：`https://www.yoto.work/platform-mcp/mcp`

```powershell
scripts\deploy-platform-mcp.bat
# 或：node scripts\deploy-platform-mcp.js
```

1. 本机蝉妈妈登录（若尚未登录）：

```powershell
python scripts\chanmama_login.py
```

1. 常驻 Worker（自动读 `.env` 里的 Token/URL）：

```powershell
scripts\start-douyin-meat-worker.bat
# 或同机双启（抖音 Worker + 可选 Commander Agent）：
scripts\start-meat-hands.bat
python scripts\meat_hands_status.py
```

看到日志含 `login logged_in=True` / 心跳成功后，他人只需打开服务器 Web 建抖音任务即可。

## MCP 工具（platform_mcp）


| Tool                          | 行为                                           |
| ----------------------------- | -------------------------------------------- |
| `douyin_chanmama_auth_status` | 肉机心跳 / 登录摘要                                  |
| `douyin_collect_hot_keywords` | 入队并在 tool 内轮询至完成/超时；失败返回 `{ok:false}`，禁止伪装成功 |


Worker HTTP（同端口，经 nginx `/platform-mcp/`）：

- `POST /worker/heartbeat`
- `POST /worker/claim`
- `POST /worker/complete`
- `GET  /worker/status`

鉴权：`Authorization: Bearer $DOUYIN_WORKER_TOKEN`（与对外 MCP 分离）。

客户端 MCP URL 仍为：`https://www.yoto.work/platform-mcp/mcp`  
`config/mcp.json` / `tool_registry.json`：`douyin_collect_*` → `platform_mcp`，`requires_mcp: true`；采集无 stub。

## 产品行为

- 任意渔具细分词；未收录时桥接父词 + 平台侧 LLM 分析（`action: analyze`）
- Worker 离线 / 未登录 → MCP `ok:false`（`need_login` / `need_worker`），图上失败，不落 stub 词卡

## 验收

1. Worker 心跳在线；未登录时 `douyin_chanmama_auth_status` / collect 返回失败
2. 服务器 Web 建「渔具」任务 → 肉机 claim 日志 → 报告四栏非空且 `source=mcp`、无 stub 标签
3. 关掉 Worker 再跑 → 明确失败，无 stub 词卡

