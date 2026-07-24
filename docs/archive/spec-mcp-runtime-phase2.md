# Spec：MCP 运行时接入 · 第二阶段（M1.2）

> 版本：v0.2 · 2026-07-22  
> 前置：M1.1（`mcp_runtime` + act 优先 MCP）  
> 目标：Tool Registry + MCP 管理 API + 开发视图管理页

---

## 1. 目标

实现“前端可管理 MCP 服务 + Skill 逻辑工具名可映射到真实 MCP 工具”：

1. **Tool Registry**：`config/tool_registry.json` 维护 logical name → MCP tool
2. **MCP Config CRUD**：读写 `config/mcp.json`，支持热重载
3. **Health API**：逐 server 探测工具列表与延迟
4. **Dev UI**：`/dev/mcp` 管理页（列表、添加、删除、重载、别名查看）

---

## 2. 新增/修改文件

| 路径 | 作用 |
|------|------|
| `config/tool_registry.json` | Skill 工具别名映射 |
| `src/agent/tools/tool_registry.py` | 别名解析与参数映射 |
| `src/agent/tools/mcp_config.py` | MCP server 配置 CRUD |
| `src/agent/tools/mcp_runtime.py` | 扩展 reload/health/invoke_logical |
| `apps/api/app/routers/mcp.py` | REST API |
| `apps/api/app/services/mcp_service.py` | 服务层 |
| `apps/api/app/schemas/mcp.py` | Pydantic 模型 |
| `apps/web/src/pages/DevMcpPage.tsx` | 开发视图管理页 |

---

## 3. API 契约

### `GET /api/mcp`
返回 runtime 状态、servers、health、aliases、tools。

### `POST /api/mcp/reload`
重载 MCP client 与 tool registry。

### `POST /api/mcp/servers`
新增/更新 server（写入 `config/mcp.json` 后自动 reload）。

### `DELETE /api/mcp/servers/{id}`
删除 server 并 reload。

---

## 4. Tool Registry 约定

```json
{
  "aliases": {
    "douyin_collect_hot_keywords": {
      "mcp_tool": "keyword_cards_pipeline_tool",
      "server": "reverse_lab_tools",
      "arg_map": { "seed": "slugs", "date_range_days": "window_days" },
      "defaults": { "collect": true, "deploy": false }
    }
  }
}
```

- `mcp_tool: null` 表示该逻辑工具不走 MCP（仅 stub）
- `act` 通过 `mcp_runtime.invoke_logical()` 调用

---

## 5. 验收标准

- [ ] `GET /api/mcp` 返回两 server 健康状态与工具数
- [ ] 前端 `/dev/mcp` 可查看、添加、删除 server
- [ ] 保存后 `POST /api/mcp/reload` 或自动 reload 生效
- [ ] `douyin_collect_hot_keywords` 映射到 `keyword_cards_pipeline_tool`
- [ ] 集成测试仍通过

---

## 6. 下一阶段（M1.3）

- 运营视图只读 MCP 状态
- Tool 参数 schema 探测与表单生成
- Skill 步骤动态绑定 registry 别名（减少 act 硬编码）
