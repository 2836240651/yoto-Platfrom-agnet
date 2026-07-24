# Spec：抖音关键词分析智能体 · Web 产品

> 版本：v0.1 · 2026-07-22  
> 前端：React · 后端：FastAPI · Agent：LangGraph（后续接入）

---

## 1. 产品定位

面向公司内部运营的 **抖音种子词分析工具**：输入种子词（如「渔具」「路亚竿」），自动输出四类词表——视频热搜、视频潜力、商品热搜、商品潜力——以优先级卡片形式交付，可导出。

**原则：** 任务模板化、结果卡片化、失败人话化。

---

## 2. 用户角色

| 角色 | 权限 |
|------|------|
| 运营 | 创建任务、查看报告、导出、历史列表 |
| 管理员（后续） | 登录态配置、MCP 状态、任务监控 |

V1 不做登录，单租户本地使用。

---

## 3. 信息架构

```
/                     首页 · 概览 + 最近任务 + 快捷新建
/tasks/new            新建分析 · 参数表单 + 确认
/tasks/:id            任务详情 · 进度 或 报告
/tasks                历史任务列表
```

---

## 4. 页面规格

### 4.1 首页 `/`

**模块：**
- 页头：产品名「抖音词分析助手」+ 一句话说明
- 快捷统计：今日任务数、本周完成数、最近种子词（mock）
- CTA：「新建分析」主按钮
- 最近任务表：名称、种子词、状态、创建时间、操作（查看）

### 4.2 新建分析 `/tasks/new`

**表单字段：**

| 字段 | 类型 | 必填 | 默认 | 校验 |
|------|------|------|------|------|
| `seed` | text | 是 | 渔具 | 1~20 字 |
| `include_video` | checkbox | 否 | true | - |
| `include_product` | checkbox | 否 | true | - |
| `date_range_days` | select | 否 | 30 | 7/30/90 |

**交互：**
1. 填写表单
2. 勾选「我已确认参数」
3. 点击「开始分析」→ POST `/api/tasks` → 跳转 `/tasks/:id`

### 4.3 任务详情 `/tasks/:id`

**状态 = running：**
- 步骤条：采集 → 扩展 → 打分 → 报告（当前步高亮）
- 文案：「预计还需约 2 分钟」（mock）
- 每 2s 轮询 GET `/api/tasks/:id`

**状态 = completed：**
- 报告头：种子词、周期、标签
- 摘要统计 4 格
- Tab：视频热搜 | 视频潜力 | 商品热搜 | 商品潜力
- 每 Tab 内关键词卡片列表（按 P0→P1→P2 排序）
- 操作：导出 Excel（后续）、返回首页

**状态 = failed：**
- 错误说明（中文）
- 按钮：重试、返回

---

## 5. API 契约

### 5.1 `GET /api/health`

```json
{ "status": "ok", "version": "0.1.0" }
```

### 5.2 `POST /api/tasks`

Request:
```json
{
  "seed": "渔具",
  "include_video": true,
  "include_product": true,
  "date_range_days": 30
}
```

Response `201`:
```json
{
  "id": "task_abc123",
  "status": "running",
  "seed": "渔具",
  "created_at": "2026-07-22T08:00:00Z"
}
```

### 5.3 `GET /api/tasks`

Query: `?limit=20&offset=0`

Response:
```json
{
  "items": [{ "id", "seed", "status", "created_at", "completed_at" }],
  "total": 1
}
```

### 5.4 `GET /api/tasks/{id}`

Response（running）:
```json
{
  "id": "task_abc123",
  "status": "running",
  "seed": "渔具",
  "progress": {
    "step": 2,
    "total_steps": 4,
    "step_name": "扩展联想词",
    "percent": 50
  },
  "created_at": "..."
}
```

Response（completed）:
```json
{
  "id": "task_abc123",
  "status": "completed",
  "seed": "渔具",
  "report": {
    "summary": {
      "keyword_count": 24,
      "video_sample_count": 66,
      "product_sku_count": 44,
      "p0_count": 3
    },
    "tags": ["种子词：渔具", "周期：近30天"],
    "alerts": [{ "type": "info|warn", "text": "..." }],
    "categories": {
      "video_hot": [ KeywordCard ],
      "video_potential": [ KeywordCard ],
      "product_hot": [ KeywordCard ],
      "product_potential": [ KeywordCard ]
    }
  }
}
```

### 5.5 KeywordCard

```json
{
  "keyword": "碳素路亚竿",
  "priority": "P0",
  "trend": "up",
  "reason": "关联视频数 30 天 +45%，带货占比高",
  "metrics": [
    { "label": "关联视频", "value": "128" },
    { "label": "30天销量", "value": "2.3万" },
    { "label": "增速", "value": "+45%" }
  ],
  "evidence": ["蝉妈妈视频库", "近7天发片量上升"],
  "action": "建议本周拍 3 条 #碳素路亚竿 话题片"
}
```

---

## 6. 后端架构

```
apps/api/
├── app/
│   ├── main.py           # FastAPI app + CORS
│   ├── routers/
│   │   ├── health.py
│   │   └── tasks.py
│   ├── schemas/
│   │   └── tasks.py      # Pydantic models
│   ├── services/
│   │   ├── task_runner.py    # 异步执行任务（mock → LangGraph）
│   │   └── mock_report.py    # V1 示例报告数据
│   └── store/
│       └── task_store.py     # 内存任务存储
└── requirements.txt
```

**V1：** `task_runner` 用 `asyncio` 模拟 4 步进度，8 秒后写入 mock 报告。  
**V2：** 替换为 `graph.invoke()` 调用 LangGraph + DouyinDataMCP。

---

## 7. 前端架构

```
apps/web/
├── src/
│   ├── api/client.ts
│   ├── types/task.ts
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── NewTaskPage.tsx
│   │   ├── TaskDetailPage.tsx
│   │   └── TaskListPage.tsx
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── StatGrid.tsx
│   │   ├── KeywordCard.tsx
│   │   ├── TaskProgress.tsx
│   │   ├── ReportTabs.tsx
│   │   └── AlertBanner.tsx
│   └── styles/global.css
└── vite.config.ts          # proxy /api → :8000
```

---

## 8. 非功能需求

| 项 | V1 目标 |
|----|--------|
| 首屏加载 | < 2s（本地） |
| 任务创建 | < 500ms 返回 task id |
| 进度刷新 | 2s 轮询 |
| 移动端 | 响应式，卡片单列 |
| 错误 | 全中文，无 stack trace |

---

## 9. 里程碑

| 阶段 | 交付 |
|------|------|
| **M0（本次）** | Spec + React 页面 + FastAPI mock 跑通 |
| M1 | 接 LangGraph 真实执行 |
| M2 | 接 DouyinDataMCP 真实采集 |
| M3 | 导出 Excel + 用户登录 |
| M4 | 多 Skill 扩展（跨境上架） |

---

## 10. 验收标准（M0）

- [ ] 运营可从首页新建「渔具」分析任务
- [ ] 任务页展示 4 步进度并最终显示报告
- [ ] 报告含 4 个 Tab，每 Tab 至少 2 张关键词卡片
- [ ] 首页展示历史任务列表
- [ ] API 文档可访问 `/docs`

---

## 11. M1 增量规格（LangGraph 混合 Loop）

> 详细技术方案见：`docs/requirements-langgraph-integration.md`

### 11.1 Loop 策略

- Macro 步骤仍保持 4 步：采集 → 扩展 → 打分 → 报告（运营可见）
- 每个 Macro 步内采用 micro loop：`think -> act -> observe -> judge`
- micro loop 不再固定 3 次：采用 **默认预算 + 自适应扩展 + 硬上限**

### 11.2 进度 API 扩展（running）

`GET /api/tasks/{id}` 在 `progress` 增加以下字段：

```json
{
  "progress": {
    "step": 2,
    "total_steps": 4,
    "step_name": "扩展联想词",
    "percent": 41,
    "micro_attempt": 4,
    "micro_budget": 8,
    "replan_used": 1
  }
}
```

### 11.3 终止与保护

- 强制预算：`global_loop_budget`、`run_timeout_s`、`run_token_budget`
- 代码判定终止；LLM 不拥有终止权
- 必须配置 LangGraph `recursion_limit` 作为兜底保险丝

### 11.4 M1 验收补充

- [ ] 任务在慢数据源场景下可超过 3 次 micro 尝试仍可收敛
- [ ] 触发预算上限时稳定终止并返回中文原因
- [ ] 进度条与实际节点执行一致，非固定 sleep
- [ ] 报告输出通过 `TaskReport` schema 校验
