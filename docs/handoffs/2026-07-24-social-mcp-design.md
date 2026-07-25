# Handoff：社媒黑盒 MCP 设计定稿 + Spike

> 2026-07-24

## 决策

- social-auto-upload 整段 MCP 黑盒；浏览器在 Temu 肉机同机 login-agent  
- 首批 type **1–5**；P2-B 再扩 B站等  
- **P2 提前**（用户批准）  
- 阻塞 S1–S5 已按 spike 关闭 → `docs/wip/spike-social-mcp-s1-s2.md`

## 关键结论

- 鉴权：`SOCIAL_UPLOAD_TOKEN` Bearer；MCP 禁止匿名  
- 终态：现网无 job 轮询 → **上游 Task 0** 补 `job_id` + GET；此前禁止把 `local_queued` 当 success  
- `postVideo` 现可无登录执行（安全债，建议上游加 `@login_required`）

## 文档

- 设计：`docs/wip/spec-social-mcp-blackbox-design.md`  
- Gap：`docs/wip/p2-social-mcp-contract-gap-check.md`  
- Spike：`docs/wip/spike-social-mcp-s1-s2.md`  
- 计划：`docs/wip/social-mcp-implementation-plan.md`  

## 下一步

用户说「开工」后按实现计划编码；上游 Task 0 可并行（sibling 仓）。
