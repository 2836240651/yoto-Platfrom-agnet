# Handoff：Temu MCP 远程网关接线（进行中）

**日期：** 2026-07-23  
**优先级例外：** 用户批准先做 P1-2 Temu（内部共用店），暂缓抖音 P0-2。

## 已完成

- G3：`streamable_http` → `http://127.0.0.1:18765/mcp` list+ping 成功  
- [`mcp/servers/platform_mcp_gateway.py`](../../mcp/servers/platform_mcp_gateway.py) + [`commander_temu_client.py`](../../mcp/servers/commander_temu_client.py)  
- [`config/mcp.json`](../../config/mcp.json) 远程 `platform_mcp`  
- registry Temu 两 tool；Skill `temu-product-listing` + `SKILL_PLANS`  
- Runtime：分 server 加载（网关挂了不影响其它 stdio）；mcp_config 保留 `url`  
- API：`POST /tasks/upload`、`POST /tasks/temu-listing`  
- 单测：`tests/unit_tests/test_temu_listing_skill.py`

## 运维待办（上线前）

1. 网关常驻：`FASTMCP_TRANSPORT=streamable-http FASTMCP_PORT=18765 python mcp/servers/platform_mcp_gateway.py`（建议同机 docker/systemd；**须用户明确要求才部署远程**）  
2. 环境变量：`COMMANDER_ACCESS_TOKEN`、`COMMANDER_API_BASE=https://www.yoto.work/api/v1`、`COMMANDER_DEFAULT_AGENT_ID=肉机`  
3. Excel：上传到 API 后路径须对**网关进程可读**（API 与网关同机共享 `uploads/`）  
4. 肉机 Agent 保持在线  

## 调用示例

```http
POST /tasks/temu-listing
Content-Type: multipart/form-data
shop_id=8381218
file=<xlsx>
```

或先 `POST /tasks/upload` 再 `POST /tasks` JSON：`skill=temu-product-listing` + `excel_path` + `shop_id`。
