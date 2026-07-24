# P1-2 Temu / 远程 MCP 契约核对（Gap Check）

> 状态：核对完成 · 2026-07-23  
> 对照：`docs/spec-architecture-contract.md` §2 P1-2；场景 WIP Temu；计划 `temu_commander_mcp`（远程网关修订版）  
> 方法：读本仓 `config/*`、`src/agent/tools/mcp_*`、`mcp/`、`apps/api`、`skills/`；对照线上 Commander 日志与 spike  
> **本文不是执行计划正文**；关键阻塞关闭前禁止假装「已可编码细节齐全」。

标记：

| 标记 | 含义 |
|------|------|
| **已满足** | 契约/能力已在仓或线上落地 |
| **stub** | 有名字/接口，未接真 |
| **规范有、仓库无** | Spec/计划写了但无可调实现 |

---

## 0. 范围与优先级声明

- 用户确认：**内部共用店铺**；肉机常开；优先 Temu 闭环；**MCP 以服务器长驻网关 + 远程挂载**（提前适应多端）。  
- 契约原文：P0（抖音）在 P1 前；**本迭代按用户指令暂缓 P0-2**，先做 P1-2 风格 Temu——须在 handoff 写明「用户批准的优先级例外」，避免后续 Agent 误判违规。

---

## 1. 契约 P1-2 对照

| 检查项 | 标记 | 证据 |
|--------|------|------|
| Temu Job = Commander 整段黑盒，本仓不做 Lyncr/生图 | **已满足（口径）** | 场景 WIP §1；spike；线上 `product_issue` |
| Skill 只编排 + 调 MCP + 人话总结 | **规范有、仓库无** | 无 `temu-product-listing` Skill / schema / `SKILL_PLANS` 项 |
| Job ≤ 2 MCP tool（submit + status） | **可设计** | 计划已定 2 tool；**仓库无**实现 |
| 外部 MCP 包装、禁止重写引擎 | **已满足（约束）** | AGENTS / 架构契约；本仓无 Commander 业务代码 |

---

## 2. 本仓 MCP / Runtime

| 检查项 | 标记 | 证据 |
|--------|------|------|
| MCP Runtime 可加载 `mcp.json` 并 invoke | **已满足（stdio）** | `mcp_runtime.py` + `example_tools`/`ping` |
| `mcp.json` 远程 SSE/HTTP 配置 | **规范有、仓库无** | 仅 `transport: stdio` |
| Runtime **实测**远程挂载 | **规范有、仓库无** | 代码把 config 交给 `MultiServerMCPClient`；依赖库支持 `sse`/`http`/`streamable`，**本仓未联调** |
| FastMCP 可长驻 HTTP/SSE | **已满足（库能力）** | 本机包：`run_sse_async` / `run_streamable_http_async` |
| platform-mcp 网关进程 / 部署单元 | **规范有、仓库无** | 无 gateway 入口、无 compose/systemd |
| Temu Commander HTTP 客户端 | **规范有、仓库无** | 无 `commander_temu` 实现 |
| registry Temu 别名 | **规范有、仓库无** | 仅 douyin stub + ping |
| 网关鉴权 | **规范有、仓库无** | `.env.example` 有 `MCP_WRITE_TOKEN` 注释痕迹级，未接到网关 |

---

## 3. Skill / API / FE

| 检查项 | 标记 | 证据 |
|--------|------|------|
| `skills/temu-product-listing/` + schema | **规范有、仓库无** | skills 侧无此 id（仅有既有/模板向） |
| `SKILL_PLANS` Temu 步骤 | **规范有、仓库无** | `constants.py` 仅抖音四步 |
| route 关键词 Temu | **规范有、仓库无** | `route.py` 无 Temu 专用；`cross-border-listing` 关键词过宽且无实现 |
| tasks API 支持 `temu-product-listing` | **规范有、仓库无** | schema Literal 仅抖音 |
| Excel 上传 / `excel_path` state | **规范有、仓库无** | API/Web 无 multipart 上架入口 |
| arg_builders Temu | **规范有、仓库无** | 无 |

---

## 4. 外部依赖（线上）

| 检查项 | 标记 | 证据 |
|--------|------|------|
| Commander `https://www.yoto.work` | **已满足** | web `API_BASE_URL`；openapi 200 |
| 肉机 Agent 在线 | **已满足（核对日）** | 线上日志 `Agent 注册成功: 肉机 (肉机)` + shop_list |
| `product_issue` / `task_list` 契约 | **已满足（spike）** | `docs/wip/temu-commander-mcp-spike.md` |
| 提交返回 taskId | **缺口（可接受）** | 计划用 task_list 推断；不改 Commander |

---

## 5. 远程 MCP 特有缺口（易漏）

| 检查项 | 标记 | 说明 |
|--------|------|------|
| Excel 文件谁可读 | **阻塞设计** | MCP 在服务器上时，**不能**读运营笔记本本地路径；必须先上传到 API/网关可读的 `uploads/`（同机共享卷），或 tool 收文件字节/URL |
| 本机开发 API + 远程网关 | **须约定** | 开发机挂远程网关时，Excel 仍须先上传到**网关所在机**可读位置，或走「上传 API → 返回 server-side path」 |
| 网关与 API 同机 | **推荐默认** | 共享 `uploads/`；免对象存储（P2 才上 OSS） |
| list_tools / transport 选型 | **待最小 spike** | SSE vs streamable_http 与当前 `mcp`/`langchain_mcp_adapters` 版本组合需一次打通证明 |

---

## 6. 阻塞与歧义（执行前）

| ID | 问题 | 状态 | 关闭条件 |
|----|------|------|----------|
| **T1** | `COMMANDER_API_BASE` | **可关** | 默认 `https://www.yoto.work/api/v1` |
| **T2** | Commander 鉴权 | **仍开放** | 提供可用 `COMMANDER_ACCESS_TOKEN`，或批准用账号登录换 token 的运维方式 |
| **T3** | taskId | **可关（接受推断）** | 不改 Commander |
| **T4** | agent / shop | **可关** | agent=`肉机`；shop 用户每次指定 |
| **T5** | Excel 摄入 | **仍开放（形态）** | 确认：同机 `uploads/` + API multipart（推荐） |
| **T6** | precheck 并入 submit | **可关** | 并入 |
| **G1** | 网关部署主机 | **仍开放** | 确认：与现网 `124.223.27.98` 同机新容器/进程，或另述 |
| **G2** | 网关 URL + 鉴权 | **仍开放** | 路径、端口、token；禁止裸公网 |
| **G3** | 远程 transport 联通 | **已关闭** | 本机 `127.0.0.1:18765/mcp` streamable_http：`list` 得 `ping`/`temu_*`，`ping` invoke 成功（2026-07-23） |
| **P0** | 契约顺序例外 | **须文档化** | handoff 写明用户批准先 P1-2 |

**建议关闭顺序：** G3（最小 spike，1～2h）→ T2/G1/G2/T5 口头拍板 → 再编码。

---

## 7. 结论

| 问题 | 结论 |
|------|------|
| 能不能直接「执行计划」开写 Skill/FE？ | **不能**。远程网关 + Temu 工具 + Excel 同机可读性 + Commander token 未齐。 |
| 契约方向对不对？ | **对**（P1-2 黑盒 + ≤2 tool + 远程挂载提前适应）。 |
| 下一步 | ① 最小 spike：远程 MCP list/invoke；② 拍板 T2/G1/G2/T5；③ 再按计划编码。 |

---

## 8. 与计划文档关系

- 执行计划：Cursor plan `temu_commander_mcp`（含远程网关修订）  
- 前置 spike（Commander HTTP）：`docs/wip/temu-commander-mcp-spike.md`  
- **本文：** 编码前契约/仓库差距；发现缺口须回写计划「阻塞」节  
