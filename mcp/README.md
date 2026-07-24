# MCP Servers

每个垂直领域一个 MCP Server，暴露原子工具给 LangGraph 调用。

## 规划

| Server | 职责 | 状态 |
|--------|------|------|
| `example_server.py` | 示例 / 健康检查 | stub |
| `douyin_data.py` | 抖音数据采集 | TODO |
| `ecommerce_ops.py` | 跨境平台上架/店铺分析 | TODO |

## 注册

在 `config/mcp.json` 中添加 server 配置，Runtime 通过 `langchain-mcp-adapters` 加载。

开发视图管理页：`/dev/mcp`（API：`GET/POST /api/mcp`）。

逻辑工具别名：`config/tool_registry.json`（Skill 工具名 → MCP 真名）。

## 原则

- 一个 tool = 一个原子操作
- 输入输出有固定 schema
- 复杂流程由 LangGraph + Skill 编排，不写在 MCP 里
