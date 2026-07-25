# P0 契约验收核对（Gap Check）

> 状态：核对完成 · 2026-07-23；**2026-07-24 复核**（回主链路抖音）  
> 对照：`docs/spec-architecture-contract.md` §2 P0 / §4 M1  
> 方法：读本仓 `skills/`、`config/*`、`src/agent`、`apps/api`、`mcp/`  
> **本文不是执行计划**；关键阻塞关闭前勿写假细 P0 实现计划。  
> 同日：社媒收口 **PARKED** → `docs/handoffs/2026-07-24-social-mcp-parked.md`。

标记约定：

| 标记 | 含义 |
|------|------|
| **已满足** | 契约要求已在本仓落地 |
| **stub** | 有名字/接口，假数据或 `mcp_tool: null` |
| **规范有、仓库无** | Spec/SKILL 写了但无可调真实实现 |

---

## 0. 采集源口径（已更正 · 2026-07-23）

| 错误旧说法 | 正确产品意图 |
|------------|--------------|
| 「蝉妈妈官方 OpenAPI / 原子 API 套餐」 | **蝉妈妈个人版会员**登录后的 **Cookie/登录态** + **浏览器自动化**拉数 |
| 把站点 `api-service.chanmama.com` 当成「官方开放 API 产品」 | 那是网站登录态下的业务请求，**不是**开放平台 Key 对接 |
| — | 须遵守**个人版**次数/权益限制 |
| — | Cookie **禁止**明文入库 |

词卡流水线（slug→HTML）在 sibling `open-reverselab`；**禁止**整包接进本仓 `douyin-keyword-research`。

---

## 1. P0-1 · Skill Schema

| 检查项 | 标记 | 证据（2026-07-24） |
|--------|------|-------------------|
| 模板含 `schema/input.json` · `output.json` | **已满足** | `skills/_template/schema/` |
| 业务 Skill `douyin-keyword-research` 具备 schema/ | **规范有、仓库无** | 仅有 `SKILL.md`；无 `schema/`、无 `prompts/` |
| 同仓对照：Temu / 社媒 Skill 已有 schema/ | **已满足（他 Skill）** | `temu-product-listing`、`social-media-publish`（社媒暂存） |
| 全 Skill「分步执行按 Schema 校验」 | **规范有、仓库无** | 无 jsonschema 校验 Skill I/O；仅有报告形状校验 `validate.py`（`douyin_keyword`） |
| Schema 校验挂载点（Runtime vs API） | **未定（阻塞 B2）** | 契约未写死 |

**P0-1 结论：** 抖音主 Skill Schema + 可测校验仍未落地。

---

## 2. P0-2 · 真实采集 MCP + Skill 闭环

### 2.1 本仓

| 检查项 | 标记 | 证据（2026-07-24） |
|--------|------|-------------------|
| Skill / API / Web 骨架 | **已满足（骨架）** | `SKILL_PLANS` 四步、tasks API seed、报告 `kind=douyin_keyword` |
| 执行路径 | **stub** | `act.py` → `mcp_tool: null` → `douyin_stub`；报告带 stub warn |
| 采集 MCP（蝉妈妈个人版 Cookie 自动化） | **规范有、仓库无** | 无 douyin/chanmama 业务 server；`mcp.json` 仅有 `example_tools` + `platform_mcp`（Temu/社媒网关，**不含**抖音采集） |
| registry 采集/扩展 | **stub** | `douyin_collect_hot_keywords` / `douyin_expand_suggest_words` → `mcp_tool: null` |
| 本仓拓词 LLM | **规范有、仓库无** | expand 走 stub tool；score 为规则 handler，未见 Completion 拓词节点 |
| `.env` 登录态钩子 | **痕迹级** | `DOUYIN_CHROME_USER_DATA_DIR` 注释；未接采集 Job |

### 2.2 Sibling（参考，非本仓 MCP）

| 检查项 | 标记 | 说明 |
|--------|------|------|
| 蝉妈妈个人版 + 浏览器自动化（产品意图） | **意图已确认** | 非官方 OpenAPI；本仓尚未封装为 MCP |
| 词卡流水线 / 抖音渔具采集包 | **有参考数据** | **禁止**整包接入本仓业务 Skill |

### 2.3 P0-2 结论

本仓仍无「蝉妈妈个人版 Cookie 自动化」MCP。`platform_mcp` 只服务 Temu（及暂存社媒），**不能**当作抖音采集已接通。

---

## 3. 阻塞与歧义

| ID | 问题 | 状态 |
|----|------|------|
| **B1** 采集源形态 | 蝉妈妈个人版 Cookie + 浏览器自动化（非官方 API） | **已关闭（口径）**；封装与登录态落点仍待实现设计 |
| **B2** Schema 谁校验 | API / Runtime / 都要？ | **仍开放** |
| **B3** M1 最小验收范围 | collect 先真、expand/score 是否第二刀？ | **仍开放** |
| **B4** expand 归本仓 LLM 还是第二 MCP | 契约倾向本仓 LLM | **仍开放（实现时对齐）** |
| **B5** 个人版限次/Cookie 如何配置 | 环境变量？本机 Chrome profile？禁止入库 | **仍开放** |

---

## 4. 一句话

**抖音主链路仍是「骨架 + stub」；P0-1/P0-2 未验收。**  
写执行计划前建议关闭 **B2 / B3 / B5**（B4 可随 B3 一并定）。
