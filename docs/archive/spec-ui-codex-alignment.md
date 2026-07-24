# Spec：双视图界面对齐 Codex 风格

> 版本：v0.1  
> 日期：2026-07-22  
> 状态：Draft（待你确认后进入开发）

---

## 1. 目标

把现有“抖音词分析助手”重构为两套视图，并在信息架构与视觉节奏上对齐 Codex 最新风格：

- `Ops（运营）`：低认知负担，聚焦任务结果和行动建议。
- `Dev（开发）`：高可观测性，聚焦 Loop 执行监督和调试。

对齐来源（公开）：
- OpenAI 发布页：Codex App 强调“project/thread/review pane”与多任务指挥台。
- Codex changelog：持续强化 thread navigation、tool activity、diff/review、状态指示与 UI polish。

---

## 2. 信息架构

### 2.1 全局结构

- 左侧：任务导航（历史 + 快速新建）
- 中间：主内容区（进度/报告）
- 右侧：活动/调试面板（Ops 简化，Dev 完整）

### 2.2 路由

- 运营：
  - `/tasks`
  - `/tasks/new`
  - `/tasks/:id`
- 开发：
  - `/dev/tasks`
  - `/dev/tasks/new`
  - `/dev/tasks/:id`

---

## 3. 两套视图差异

### 3.1 Ops（运营）

- 显示：
  - 宏观步骤（采集→扩展→打分→报告）
  - 百分比进度
  - 报告摘要 + 关键词卡片 + 行动建议
- 隐藏：
  - micro/replan 计数
  - node 事件流
  - current_action / failure_class / last_tool_error

### 3.2 Dev（开发）

- 显示：
  - Ops 全部内容
  - `current_action`, `micro_route`, `failure_class`
  - `quality_score`, `global_loop_used`, `micro_budget_*`, `replan_budget_used`
  - `events`（最近 N 条）
  - macro step 状态（pending/running/done/failed）

---

## 4. 视觉规范（对齐 Codex 气质）

- 设计原则：中性、紧凑、可扫描、可监督。
- 间距：8px 栅格；卡片内边距 12/16/20 分层。
- 圆角：8（标签）/12（卡片）/16（大容器）。
- 边框：低对比浅边框，hover 才抬升强调。
- 字号层级：
  - H1: 24
  - H2: 18
  - Body: 14
  - Meta: 12
- 状态色：
  - running：teal
  - completed：green
  - failed：red
  - pending：slate

---

## 5. 数据契约（前端依赖）

`GET /api/tasks/{id}` 维持 `report/progress`，新增可选 `debug`：

- `debug.current_action`
- `debug.micro_route`
- `debug.failure_class`
- `debug.last_tool_error`
- `debug.quality_score`
- `debug.global_loop_used`
- `debug.micro_budget_*`
- `debug.replan_budget_used`
- `debug.plan[]`
- `debug.events[]`

Ops 页面不得展示 `debug` 原始字段；Dev 页面可视化展示。

---

## 6. 可用性约束

- 运营页禁止出现 MCP/LangGraph/prompt 等工程术语。
- 失败提示必须“人话化”，不能暴露堆栈。
- Dev 页允许技术字段，但仍需结构化与可读性。

---

## 7. 验收标准（Spec 级）

1. 同一任务 ID 在 Ops 与 Dev 页面均可访问。
2. Ops 页面不出现任何 Loop 内部字段。
3. Dev 页面可以连续看到事件流增长（任务运行时）。
4. 两套页面共用同一后端 API，不新增第二套后端。
5. 视觉层级明显优于当前版本（见基准校验文档）。

