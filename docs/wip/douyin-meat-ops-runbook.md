# 抖音肉机 · 运营 / 运维一页

> 现行 · 2026-07-25 · 配合 [`douyin-meat-machine-mcp.md`](./douyin-meat-machine-mcp.md)

运营只打开服务器 Web；肉机侧由运维保证「两只手」在线。

## 肉机每日开机（同机双进程 / 空闲机 EXE）

**推荐（空闲机）：** 拷贝 `dist\meat-worker\` 整夹，见 [`meat-worker-exe.md`](./meat-worker-exe.md)。

```text
1. 编辑 D:\meat-worker\config.json 填入 worker_token
2. 运行 MeatWorker.exe → 托盘「登录蝉妈妈」→ 图标变绿
3. 服务器工具状态应显示抖音肉机在线
```

**开发机脚本（备选）：**

```text
1. 蝉妈妈登录（首次或 Cookie 失效时）
   cd D:\reverselab\agent-platform
   python scripts\chanmama_login.py

2. 一键双启（抖音 Worker + 可选 Commander Agent）
   scripts\start-meat-hands.bat

3. 看双路状态
   python scripts\meat_hands_status.py
```

只启抖音脚本手：`scripts\start-douyin-meat-worker.bat`。
构建 EXE：`scripts\build-meat-worker.bat`。

Commander Agent 路径（可选，写入本仓 `.env`）：

```text
COMMANDER_AGENT_EXE=D:\dev\workspace\commander-agent-t260220-main\commander-agent-t260220-main\build\bin\Agent.exe
```

## 运营怎么用

1. 打开 `https://www.yoto.work/agent-platform`（或本机 Vite 且代理到已对齐真采的 API）
2. Composer 选「抖音词分析」，输入种子词（如「渔具」「反底钓」）
3. 等报告：`data_source.source=mcp`，标签**没有**「数据源：stub」
4. 报告分区：视频热搜 / 视频潜力 / 商品热搜 / 商品潜力

## 失败码（给运维看）

| 信号 | 含义 | 处理 |
|------|------|------|
| `need_worker` | 无在线抖音 Worker 心跳 | 跑 `start-meat-hands.bat` / `start-douyin-meat-worker.bat` |
| `need_login` | 蝉妈妈未登录 / Cookie 失效 | `python scripts\chanmama_login.py` 后重启 Worker |
| Worker 在线但任务一直「采集」 | claim 卡住或 Playwright 挂起 | 看 Worker 控制台；必要时重启 Worker |
| 报告「数据源：stub」 | API 仍是旧计划或 stub 回退 | 确认 `AGENT_ENV=prod`、`MCP_ALLOW_STUB_FALLBACK=false`；热补丁/部署新 API |
| 工具状态：上架 Agent 离线 | Temu 手未开（不影响抖音采集） | 启动 Commander Agent |
| 工具状态：抖音肉机离线 | 抖音手未开或 Token 不一致 | 核对 `.env` 的 `DOUYIN_WORKER_TOKEN` 与服务器一致 |

## 禁止

- 把 Cookie / Token 发到群聊或写进 git  
- 关掉 Worker 后假装任务成功  
- 要求改 Commander Agent「顺便采蝉妈妈」——架构上禁止（见 handoff）
