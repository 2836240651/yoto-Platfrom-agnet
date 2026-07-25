# 跨境智能体平台（Agent Platform）

公司内部 **跨境电商行业 Agent Workspace**：同一套工作区服务开发、运营、管理者、财务等岗位；垂直能力通过 **Skill + MCP** 扩展。

> 权威产品定义：[`docs/spec-product.md`](docs/spec-product.md)  
> 工程现状与约束：[`docs/spec-engineering.md`](docs/spec-engineering.md)  
> 词卡流水线（抖音 Playwright → yoto.work）**不在本仓库**；见 sibling `open-reverselab`。

## 组件一览

| 组件 | 路径 | 说明 |
|------|------|------|
| Agent API / Web | `apps/api` · `apps/web` | 任务编排、报告页 |
| Runtime / Skills | `src/agent` · `skills/` | 抖音词分析、Temu 上架等 |
| **platform_mcp（服务器）** | `mcp/servers/` | 黑盒工具网关；部署到 yoto |
| **肉机助手 MeatWorker（本机 EXE）** | **`apps/meat-worker/`** | **出站领任务手**：蝉妈妈 Playwright 采集；**不并入** Commander Agent |

### 肉机助手（标识 · 必读）

抖音真实采集跑在**空闲/肉机 PC** 上，不是服务器里的脚本常驻：

- 源码：[`apps/meat-worker/`](apps/meat-worker/)（托盘 EXE）
- 构建：`scripts\build-meat-worker.bat` → `dist\meat-worker\`（整夹拷到空闲机）
- 文档：[`docs/wip/meat-worker-exe.md`](docs/wip/meat-worker-exe.md) · [`docs/wip/douyin-meat-ops-runbook.md`](docs/wip/douyin-meat-ops-runbook.md)
- 架构：服务器 `platform_mcp` 入队 ← 肉机 `MeatWorker.exe` 出站 claim/complete（与 Temu 的 Commander Agent **同角色、不同进程**）

```
运营 Web → Agent API → platform_mcp
                         ↑ HTTP /worker/*
空闲机 MeatWorker.exe ───┘  （蝉妈妈登录态仅留本机）
```

## 架构

```
Workspace Web (React)     ← 对话 / 线程 / 业务·开发双视图
        ↓
Agent Runtime             ← 目标：Skills 渐进披露；现状：硬编码计划（见工程 Spec）
        ↓
Skills (skills/)          ← 跨境领域能力
        ↓
MCP Servers (mcp/)        ← 原子工具（服务器）
        ↑
MeatWorker (apps/meat-worker)  ← 本机出站手（抖音等需浏览器/登录的黑盒）
```

## 目录

```
agent-platform/
├── src/agent/              # Runtime
├── skills/                 # Skill 能力包
├── mcp/servers/            # MCP 实现（含抖音 job 队列）
├── apps/api/               # FastAPI
├── apps/web/               # Workspace UI
├── apps/meat-worker/       # ★ 肉机助手 EXE 源码（托盘 + 出站 Worker）
├── docs/                   # 权威 Spec + archive / handoffs / wip
├── config/                 # mcp.json · tool_registry.json
└── scripts/                # 启动 / 部署 / build-meat-worker.bat
```

## 快速开始

```powershell
cd d:\reverselab\agent-platform

# 终端 1：API → http://127.0.0.1:8000/docs
scripts\start-api.bat

# 终端 2：Web → http://127.0.0.1:5179
scripts\start-web.bat
```

安装：`pip install -e ".[ui]"` · 环境：`copy .env.example .env`

肉机助手：`scripts\build-meat-worker.bat`，见上文「肉机助手」。

## 文档

| 文档 | 说明 |
|------|------|
| [`docs/spec-product.md`](docs/spec-product.md) | 产品权威定义 |
| [`docs/spec-engineering.md`](docs/spec-engineering.md) | 工程现状与约束 |
| [`docs/wip/meat-worker-exe.md`](docs/wip/meat-worker-exe.md) | **肉机助手 EXE** |
| [`docs/wip/douyin-meat-machine-mcp.md`](docs/wip/douyin-meat-machine-mcp.md) | 抖音肉机 MCP 架构 |
| [`docs/README.md`](docs/README.md) | 文档索引 |
| [`docs/archive/`](docs/archive/) | 已废止历史 Spec |
| [`AGENTS.md`](AGENTS.md) | 编码 Agent 入口 |

## 技术栈

- **Runtime**: LangGraph + LangChain（渐进披露目标见工程 Spec）
- **MCP**: 配置见 `config/mcp.json`；生产网关 `https://www.yoto.work/platform-mcp`
- **UI**: React Workspace（`apps/web`）
- **肉机助手**: PyInstaller 托盘 EXE（`apps/meat-worker`）
- **编码指引**: `AGENTS.md`
