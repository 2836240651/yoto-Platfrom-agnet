# P0 契约验收核对（Gap Check）

> 状态：核对完成 · 2026-07-23（同日修订：采集源口径）  
> 对照：`docs/spec-architecture-contract.md` §2 P0 / §4 M1  
> 方法：读本仓 `skills/`、`config/*`、`src/agent`、`apps/api`、`mcp/`；对照 sibling `open-reverselab`（只读）  
> **本文不是执行计划**；关键阻塞关闭前勿写假细 P0 实现计划。

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
| — | 须遵守**个人版**次数/权益限制（见如 `dev/workspace/docs/chanmama-fishing-intercept-v2.html`） |
| — | Cookie **禁止**明文入库 |

词卡流水线（slug→HTML）仍是 sibling 上另一条能力；**禁止**整包接进本仓 `douyin-keyword-research`。

---

## 1. P0-1 · Skill Schema

| 检查项 | 标记 | 证据 |
|--------|------|------|
| 模板含 `schema/input.json` · `output.json` | **已满足** | `skills/_template/schema/` |
| 业务 Skill `douyin-keyword-research` 具备 schema/ | **规范有、仓库无** | 仅有 `SKILL.md`，无 `schema/`、无 `prompts/` |
| 全 Skill「分步执行按 Schema 校验」 | **规范有、仓库无** | 无 jsonschema 校验 Skill I/O；仅有报告形状校验 `validate.py` |
| Schema 校验挂载点（Runtime vs API） | **未定（阻塞 B2）** | 契约未写死 |

**P0-1 结论：** 仅模板示范；主 Skill Schema + 可测校验未落地。

---

## 2. P0-2 · 真实采集 MCP + Skill 闭环

### 2.1 本仓

| 检查项 | 标记 | 证据 |
|--------|------|------|
| Skill / API / Web 骨架 | **已满足（骨架）** | Skill、`SKILL_PLANS`、tasks API、报告 UI |
| 采集 MCP（蝉妈妈个人版 Cookie 自动化） | **规范有、仓库无** | `mcp.json` 仅 `example_tools`/`ping` |
| registry 采集/扩展 | **stub** | `mcp_tool: null` → `douyin_stub` |
| 本仓拓词 LLM | **规范有、仓库无** | 未见 Completion 拓词节点 |

### 2.2 Sibling（参考，非本仓 MCP）

| 检查项 | 标记 | 说明 |
|--------|------|------|
| 蝉妈妈个人版 + 浏览器自动化（产品意图） | **意图已确认** | 非官方 OpenAPI；本仓尚未封装为 MCP |
| 蝉妈妈站点接口观测笔记 | **有参考** | 如 `open-reverselab/notes/ctf-website/chanmama-tik-goods-sale.md`（含登录态/权益字段观察） |
| 词卡流水线 HTML 产物 | **有跑通记录** | `exports/keyword-cards/<stamp>/html/`；实现名含 chanmama，采集常走抖音或 `--skip-live` |
| 抖音渔具采集包（有 jsonl 数据） | **有数据** | `exports/ctf-website/douyin-fishing-gear-hot-data/normalized/` |
| `keyword_cards_pipeline_tool` | **禁止接入本仓业务 Skill** | AGENTS 明令 |

### 2.3 P0-2 结论

本仓仍无「蝉妈妈个人版 Cookie 自动化」MCP。Sibling 有词卡 HTML / 抖音采集数据 / 蝉妈妈观测笔记，**不能**直接当成已接入的 agent-platform 采集 Job。

---

## 3. 阻塞与歧义

| ID | 问题 | 状态 |
|----|------|------|
| **B1** 采集源形态 | 蝉妈妈个人版 Cookie + 浏览器自动化（非官方 API） | **已关闭（口径）**；封装与登录态落点仍待实现设计 |
| **B2** Schema 谁校验 | API / Runtime / 都要？ | **仍开放** |
| **B3** M1 最小验收范围 | collect 先真、expand/score 是否第二刀？ | **仍开放** |
| **B4** expand 归本仓 LLM 还是第二 MCP | 契约倾向本仓 LLM | **仍开放（实现时对齐）** |
| **B5** 个人版限次/Cookie 如何配置 | 环境变量？本机 profile？禁止入库 | **仍开放** |

---

## 4. 一句话

**采集源口径已更正为「蝉妈妈个人版 Cookie + 浏览器自动化」。**  
本仓 P0-1/P0-2 代码仍未落地；写执行计划前建议关闭 B2/B3/B5。
