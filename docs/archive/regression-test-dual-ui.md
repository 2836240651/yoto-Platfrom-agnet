# 回归测试文档：双视图 UI

> 版本：v0.1  
> 日期：2026-07-22

---

## 1. 测试目标

验证 Ops / Dev 双视图在功能、数据一致性与展示边界上均符合预期。

---

## 2. 测试环境

- 前端：`apps/web`（Vite dev + build）
- 后端：`apps/api`（FastAPI）
- 数据：LangGraph stub 流程

---

## 3. 核心用例矩阵

| ID | 用例 | 步骤 | 预期 |
|---|---|---|---|
| UI-01 | Ops 列表访问 | 打开 `/tasks` | 列表正常，显示历史任务 |
| UI-02 | Dev 列表访问 | 打开 `/dev/tasks` | 列表正常，显示开发历史任务 |
| UI-03 | Ops 新建任务 | `/tasks/new` 提交 | 跳转 `/tasks/:id`，显示宏观进度 |
| UI-04 | Dev 新建任务 | `/dev/tasks/new` 提交 | 跳转 `/dev/tasks/:id`，显示宏观+微观信息 |
| UI-05 | 数据一致性 | 同 task_id 打开 Ops/Dev | `status/progress/report` 一致 |
| UI-06 | Ops 降噪 | 观察 Ops 详情 | 不显示 current_action/events 等 debug 信息 |
| UI-07 | Dev 可观测 | 观察 Dev 详情 | 显示 action、route、budget、events |
| UI-08 | 失败态（Ops） | 制造失败任务 | 人话错误提示，无堆栈 |
| UI-09 | 失败态（Dev） | 制造失败任务 | 可见 failure_class、last_tool_error、事件上下文 |
| UI-10 | 构建检查 | 执行 `npm run build` | 构建通过 |
| API-01 | Schema 兼容 | GET task detail | 有无 debug 都不影响 Ops |
| API-02 | Debug 实时性 | 运行中轮询 detail | debug.events 条数随执行增长 |

---

## 4. 重点断言

- 断言 A：`/tasks/:id` 页面 DOM 不出现关键词：`current_action`, `micro_route`, `failure_class`.
- 断言 B：`/dev/tasks/:id` 必须出现“Loop 调试信息”区块。
- 断言 C：Dev 面板 events 至少显示 1 条（任务开始后）。

---

## 5. 冒烟脚本（手动）

1. 启动 API + Web
2. Ops 新建任务并查看完成
3. Dev 用相同 seed 新建任务
4. 比对同状态字段一致性
5. 检查 Dev 事件流可见

---

## 6. 退出标准

- P0 用例全部通过：UI-01~UI-07, UI-10, API-01
- 无阻塞级 UI 崩溃
- 无明显文案误导（Ops 页出现技术术语算阻塞）

