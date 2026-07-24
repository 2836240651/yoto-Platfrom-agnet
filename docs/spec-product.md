# Spec：跨境电商 Agent Workspace（权威产品定义）

> 状态：**Canonical** · 版本 v1.2 · 2026-07-23  
> 本文件是产品唯一权威定义。旧 baseline / dual-ui / 单 Skill 产品 Spec 见 `docs/archive/`，仅作历史参考。  
> 编码 Agent 入口：`AGENTS.md` → 本文件；**迭代与架构契约**见 `docs/spec-architecture-contract.md`。

---

## 1. 一句话

面向 **跨境电商行业从业者** 的 **Agent Workspace**（对标 Codex 式工作区）：同一套壳服务开发、运营、老板、财务等角色；垂直能力以 **Skill + MCP** 挂载，而不是做成「仅运营填表出报告」的单机工作流。

## 2. 用户与过滤条件

| 维度 | 定义 |
|------|------|
| 行业 | 跨境电商（及紧密配套岗位） |
| 岗位 | **不限**：开发、运营、管理者、财务等均可使用 |
| 差异 | 同一 Workspace；**视图深度 / 可用 Skill / 可见调试信息** 不同，不是多套独立产品 |

典型用法（非穷尽）：

- **运营**：对话或任务启动选品/关键词/上架辅助 → 看行动建议与报告  
- **开发**：同一对话线程上查看执行过程、MCP、预算与事件（开发视图）  
- **老板**：要摘要、风险、优先级，少操作细节  
- **财务**：费用、利润、广告 ROI 等（未来 Skill；当前未实现）

## 3. 产品形态（以当前前端壳为准）

信息架构对齐 Codex 式 Workspace（实现见 `apps/web/`）：

| 区域 | 作用 |
|------|------|
| 侧栏 | 新对话、搜索、已安排、插件（Skill/MCP）、项目、对话线程 |
| 主区首页 | 「我们应该在 workspace 中构建什么？」+ 自由输入 Composer |
| 上下文条 | workspace / 本地模式 / 仓库分支等 |
| 视图切换 | **业务视图**（默认，低工程噪音）↔ **开发视图**（可观测、MCP） |
| 线程 | 一次对话/任务一条线程；历史可回看 |

原则：

- **入口是 Workspace 对话**，不是「只能选任务模板」。  
- 需要结构化参数时，可在线程内二次确认（表单/卡片），但不得把产品定义收成「只有表单」。  
- 业务视图默认不暴露 LangGraph / prompt 等工程术语；开发视图可暴露 MCP、loop、预算等。

## 4. 能力模型

```
Workspace Shell (apps/web)
        ↓
Agent Runtime（目标：Skills 渐进披露 + 工具执行）
        ↓
Skills（跨境领域能力包） + MCP（原子工具）
```

| 层 | 职责 |
|----|------|
| Shell | 多角色入口、线程、视图深浅 |
| Runtime | 路由到 Skill、按需加载指令、调用工具、产出结构化结果 |
| Skill | 领域剧本（关键词、上架、店铺、财务口径…） |
| MCP | 可替换的原子采集/写入工具 |

**禁止**：把 open-reverselab 词卡流水线（Playwright → yoto.work）接进本仓业务 Skill。

### 4.1 垂直业务场景清单（产品层）

Workspace 上挂载的跨境能力场景（步骤级 LLM/Tool 边界见工程侧 WIP，不在此展开实现）：

| 场景 | 一句话 | 本仓优先级 |
|------|--------|------------|
| 抖音关键词挖掘与报告 | 种子词 → 采集/拓展 → 结构化报告 | **最高（当前主 Skill）** |
| Temu 智能上架 | Excel(+图) → 可选 AI 文案/图 → 店小秘上架 | 高（复用外部 Commander，MCP 包装） |
| 1688 铺货 | 采竞品 → 改写/翻新 → 上架 | 中（采集可先；发品待外部可调） |
| OSS 素材托管 | 上传/管理图片视频 | 底座 Tool |
| 社媒批量发布 | 可选 LLM 文案 + 多账号自动发布 | 中 |

边界标准（可编码）：`docs/wip/spec-business-scenarios-llm-tool.md`。  
迭代与接入契约（强制）：`docs/spec-architecture-contract.md`。

## 5. 渐进披露（产品目标 · 非现状）

目标遵循 Agent Skills 标准三层：

1. **Discovery**：仅 Skill `name` + `description` 常驻  
2. **Activation**：匹配后加载该 Skill 的 `SKILL.md`  
3. **Execution**：再按需读 `references/` / `prompts/`；脚本可只执行取输出  

现状与差距见 `docs/spec-engineering.md`（当前仍为硬编码 `SKILL_PLANS` 固定流程）。

## 6. 当前已落地 vs 未落地

| 项 | 状态 |
|----|------|
| Codex 式 Workspace 壳（含业务/开发双视图） | 已有 UI 骨架 |
| 对话 Composer → 任务 | 有入口；创建后仍偏向单 Skill 表单 |
| Skill：`douyin-keyword-research` | 有；采集多为 intentional stub |
| Skills 渐进披露 Runtime | **未实现** |
| 老板/财务专用 Skill | **未实现** |
| 真实蝉妈妈采集 MCP | **未接入**（目标：个人版登录态浏览器自动化，非官方 OpenAPI） |

第一个业务 Skill 的细节契约：以 `skills/douyin-keyword-research/` 与归档中的旧四栏词 Spec 为参考，**不再**把「抖音词分析」当作整个产品定义。

## 7. 成功标准（产品）

1. 任意跨境岗位用户能从 Workspace 发起工作，而不是先学工程概念。  
2. 新垂直能力 = 加 Skill（+ 可选 MCP），不必改壳的信息架构。  
3. 开发视图能诊断失败；业务视图失败为人话，且 MCP 失败不假成功。  
4. 文档以本 Spec + `docs/spec-engineering.md` 为边界；归档文档不参与日常实现决策。

## 8. 文档权威链

| 优先级 | 文档 |
|--------|------|
| 1 | 本文件 `docs/spec-product.md` |
| 2 | `docs/spec-architecture-contract.md`（契约与迭代强制） |
| 3 | `docs/spec-engineering.md`（实现约束与现状） |
| 4 | `docs/wip/spec-business-scenarios-llm-tool.md`（场景 LLM/Tool） |
| 5 | `skills/<id>/SKILL.md`（单能力） |
| 6 | `docs/archive/*`（历史） |

---

变更须更新本文件版本号，并在 `docs/handoffs/` 留交接（`YYYY-MM-DD-<slug>.md`）。
