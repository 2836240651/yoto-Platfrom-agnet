# 跨境智能体平台（Agent Platform）

公司内部 **跨境电商行业 Agent Workspace**：同一套工作区服务开发、运营、管理者、财务等岗位；垂直能力通过 **Skill + MCP** 扩展。

> 权威产品定义：[`docs/spec-product.md`](docs/spec-product.md)  
> 工程现状与约束：[`docs/spec-engineering.md`](docs/spec-engineering.md)  
> 词卡流水线（抖音 Playwright → yoto.work）**不在本仓库**；见 sibling `open-reverselab`。

## 架构

```
Workspace Web (React)     ← 对话 / 线程 / 业务·开发双视图
        ↓
Agent Runtime             ← 目标：Skills 渐进披露；现状：硬编码计划（见工程 Spec）
        ↓
Skills (skills/)          ← 跨境领域能力
        ↓
MCP Servers (mcp/)        ← 原子工具
```

## 目录

```
agent-platform/
├── src/agent/              # Runtime
├── skills/                 # Skill 能力包
├── mcp/servers/            # MCP 实现
├── apps/api/               # FastAPI
├── apps/web/               # Workspace UI
├── docs/                   # 权威 Spec + archive / handoffs / wip
├── config/                 # mcp.json · tool_registry.json
└── scripts/                # 启动脚本
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

## 文档

| 文档 | 说明 |
|------|------|
| [`docs/spec-product.md`](docs/spec-product.md) | 产品权威定义 |
| [`docs/spec-engineering.md`](docs/spec-engineering.md) | 工程现状与约束 |
| [`docs/README.md`](docs/README.md) | 文档索引 |
| [`docs/archive/`](docs/archive/) | 已废止历史 Spec |
| [`AGENTS.md`](AGENTS.md) | 编码 Agent 入口 |

## 技术栈

- **Runtime**: LangGraph + LangChain（渐进披露目标见工程 Spec）
- **MCP**: 配置见 `config/mcp.json`
- **UI**: React Workspace（`apps/web`）
- **编码指引**: `AGENTS.md`
