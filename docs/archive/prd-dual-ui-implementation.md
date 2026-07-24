# 开发 PRD：双视图界面（Ops / Dev）

> 版本：v0.1  
> 日期：2026-07-22  
> 类型：Implementation PRD（可直接执行）

---

## 1. 目标与成功标准

在不改动核心业务流程的前提下，完成 Ops / Dev 双视图：
- Ops：面向运营决策
- Dev：面向执行监督

成功标准：
- 研发可通过 Dev 页面定位 loop 失败原因
- 运营无需理解技术字段即可完成业务操作

---

## 2. 范围

### In Scope
- 新增 Dev 路由与页面
- Ops 页面降噪（去 loop 细节）
- API `TaskDetail` 增加 `debug` 可选结构
- 文案与视觉层级重构（对齐 Codex 风格）

### Out of Scope
- 新业务功能（导出、权限、多租户）
- Agent 执行策略改造

---

## 3. 里程碑

## M1 文档冻结（本次）
- 完成 Spec/需求/PRD/测试/校验文档

## M2 UI 骨架重构
- 导航、布局、双视图路由

## M3 Dev 可观测面
- Loop 指标面板 + 事件流面板

## M4 回归与收敛
- 用例通过 + 基准校验通过

---

## 4. 技术方案

### 4.1 后端
- `TaskDetail` 新增 `debug?: dict`
- `langgraph_runner` 每次 `_apply_state` 同步 `debug`
- `merge_live_detail` 返回实时 `debug`

### 4.2 前端
- 路由：
  - Ops: `/tasks/*`
  - Dev: `/dev/tasks/*`
- 组件：
  - `TaskProgressBar`（Ops，宏观）
  - `DevTaskProgressBar`（Dev，微观）
  - `DevLoopPanel`（Dev 调试面板）

---

## 5. 接口定义（PRD 级）

`TaskDetail.debug` 推荐字段：
- `status`
- `current_action`
- `micro_route`
- `failure_class`
- `last_tool_error`
- `quality_score`
- `global_loop_used`
- `micro_budget_default/current/max/used`
- `replan_budget_used`
- `current_step`
- `plan[]`
- `events[]`

---

## 6. 埋点与观测（后续可选）

- `ui_view_mode`: ops/dev
- `dev_panel_expand`: true/false
- `task_detail_render_ms`

---

## 7. 验收清单

- [ ] Ops/Dev 路由可访问
- [ ] Ops 不显示 debug 字段
- [ ] Dev 显示当前 action + events
- [ ] 任务失败时 Dev 能定位失败节点
- [ ] `npm run build` 通过
- [ ] API schema 与前端类型一致

---

## 8. 发布与回滚

发布：
1. 后端先发（兼容性新增字段）
2. 前端发版

回滚：
- 前端回到单视图路由
- 后端保留 `debug` 字段（向后兼容）

