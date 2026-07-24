# Spec：迭代优先级 · 架构契约 · 开发规范（强制）

> 状态：**Canonical（架构契约）** · 版本 v1.1 · 2026-07-23  
> 编码 Agent **全程强制遵守**。产品定义见 `docs/spec-product.md`；工程现状见 `docs/spec-engineering.md`；场景 LLM/Tool 细节见 `docs/wip/spec-business-scenarios-llm-tool.md`。  
> 冲突时：本文件的**契约与优先级** > 过时实现习惯（如无限延续硬编码 `SKILL_PLANS`）。  
> v1.1：P0-2 采集源更正为蝉妈妈**个人版 Cookie + 浏览器自动化**（非官方 OpenAPI）。

---

## 1. 核心架构契约（P0 锁定，无例外）

### 1.1 模式名

**Skill Schema + 外部 Job = 1～2 个 MCP**

```
Skill（编排 / 校验 / 本仓该做的 LLM / 结果组装）
        ↓ 仅通过 MCP
Job（外部黑盒：1 个 MCP，或「采集 MCP + 执行 MCP」最多 2 个）
```

### 1.2 Skill 层

| 允许 | 禁止 |
|------|------|
| 流程编排、入参/出参 Schema 校验、步骤串联、结果组装 | 直连第三方 HTTP/浏览器/SDK |
| 触发**本仓职责内**的 LLM（如抖音拓词） | 在 Skill 内重写已有外部引擎逻辑 |
| 调用已注册 MCP（按剧本） | 单 Job 拆成零散多 MCP 乱调 |

**必备文件（每个 Skill）：**

```
skills/<id>/
  SKILL.md
  schema/input.json      # JSON Schema
  schema/output.json
  prompts/<step>.md      # 分步提示（按需加载）
```

LLM 输出与 MCP 入参/出参均须可对照 Schema 校验；禁止无契约野字段作为正式接口。

### 1.3 Job / MCP 层

- 一个完整外部业务 Job → **仅 1 个 MCP**，或 **最多 2 个**（例：采集 + 执行推送）。  
- 外部系统若内部已含模型（分析/生图），整段仍算 **一个黑盒 Job**，本仓不再拆 LLM 步。  
- 禁止 Skill 裸调第三方 API。

### 1.4 契约目的

统一 Temu / 1688 / 抖音 / OSS / 社媒 的接入范式；摆脱死板全局 `SKILL_PLANS`、场景难扩展、调试混乱。

### 1.5 开发红线（P0/P1 验收前）

在 **架构契约落地** 且 **抖音真实采集 MCP + Temu Commander MCP** 验证跑通前，**禁止**开工：

- 完整电商域模型目录  
- 完整 OAuth / 多商户 RBAC  
- Celery / Redis / Rabbit 等重型队列全家桶  

优先跑通「Skill + MCP 黑盒」闭环，不提前堆基建。

---

## 2. 迭代优先级（严格 P0 → P1 → P2）

### P0：架构底座 + 抖音真实 MCP（最高优先）

| ID | 内容 | 验收 |
|----|------|------|
| **P0-1** | 全 Skill 补齐 `schema/input.json`、`schema/output.json`；分步执行按 Schema 校验 | 规范目录存在；校验可测 |
| **P0-2** | `douyin-keyword-research`：废弃采集 stub，接**真实采集 MCP**（数据源：**蝉妈妈个人版会员登录态 + 浏览器自动化拉数**；**不是**蝉妈妈开放平台官方 API；须遵守个人版次数/权益限制；**禁止**把词卡流水线整包冒充四栏 Skill）+ Skill 编排/拓词 LLM + 报告渲染 | 种子词 → 真实采集 → 结构化报告可跑通 |

**P0 里程碑：** Schema 规范落地 + 抖音「Skill + 真实 MCP」全链路可运行，证明契约可行。

### P1：Runtime 升级 + Temu 黑盒 MCP

| ID | 内容 | 验收 |
|----|------|------|
| **P1-1** | 废弃对业务场景的静态硬编码依赖：动态加载 Skill 剧本（`SKILL.md` / prompts / 计划）；按需绑定 MCP；预留 Deep Agents 类扩展 | 新 Skill 可不改死板全局表即可挂载（迁移期允许过渡） |
| **P1-2** | Temu：Commander `product_issue` **整段**封为 MCP Job（提交 + 可选 status） | Excel/`file_id` + 店铺 → job 成功/失败可观测 |

**P1-2 校正（相对早期草稿）：**  
Temu Skill **只**做意图匹配、缺参确认、调用 MCP、人话总结。  
**禁止**在本仓 Skill 再做商品文案生成、图片提示词、生图——这些已在 Commander（Lyncr）黑盒内。详见场景边界 WIP §1。

**P1 里程碑：** Runtime 可动态调度 + Temu 黑盒 MCP 跑通。

### P2：延后（P0/P1 未验收禁止启动）

- OSS MCP、社媒发布 MCP  
- 统一素材底座深化  
- 完整域模型、店铺 OAuth、Celery 等  

---

## 3. 编码 Agent 强制规则

1. **架构优先：** 先 Schema、先 MCP 契约、先闭环，再堆业务细节。  
2. **分层隔离：** 本仓该做的语义/生成 → Skill/LLM；固定作业与外部闭环 → MCP。外部已含模型的 Job → 整段 MCP。  
3. **Job 绑定：** 完整外部 Job ≤ 2 个 MCP。  
4. **基建延后：** 未过抖音 + Temu 两套闭环前，禁止重型底座。  
5. **可观测可复用：** 可配置、可测、避免一次性硬编码；迁移期改 `SKILL_PLANS` 须同步文档。  
6. **文档同步：** 每完成一个 Skill/MCP，更新 Spec、Schema、handoff；代码与契约一致。

与场景步骤清单交叉阅读：`docs/wip/spec-business-scenarios-llm-tool.md`。

---

## 4. 里程碑一览

| 里程碑 | 完成标志 |
|--------|----------|
| M1 = P0 | Schema 规范 + 抖音真实采集 MCP 链路 |
| M2 = P1 | Runtime 动态调度 + Temu Commander MCP |
| M3 = P2 启动 | 仅当 M1/M2 验收通过 |

---

## 5. 文档关系

| 文档 | 角色 |
|------|------|
| 本文件 | **迭代与架构契约（强制）** |
| `docs/spec-product.md` | 产品是什么 |
| `docs/spec-engineering.md` | 现状真话 + 实现路径指针 |
| `docs/wip/spec-business-scenarios-llm-tool.md` | 五场景 LLM/Tool 与实盘映射 |
