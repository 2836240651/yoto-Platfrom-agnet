# 会话级模型选择 Implementation Plan

> **Design:** `docs/wip/session-model-picker-design.md`（v2 · 已确认）  
> **Status:** 已实现（2026-07-24）

**Goal:** Composer 显式钉扎 `model_id` → NewTask → API；未钉扎走 catalog；黑盒忽略。

## Tasks

- [x] Runtime：`ALLOWED_MODEL_IDS` / `BLACKBOX_SKILLS` / `resolve_chat_endpoint(model_id=)`
- [x] API：`model_id` 字段、非法 400、黑盒 strip、runner 透传
- [x] FE：Composer 自动/四模型；`location.state`；NewTask 仅钉扎时 POST
- [x] 文档：设计已确认、`AGENTS.md` 优先级、本计划
- [x] 单测：`test_llm_routing` + `test_task_model_id`（27 passed）

## Note

Web 尚无独立 Temu 上架页；黑盒由 API strip。`WorkspaceComposer` 预留 `blackbox` prop。
