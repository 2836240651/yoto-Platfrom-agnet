# WIP：会话级模型选择（Composer · Codex 位）

> 状态：**已确认** · v2 · 2026-07-24  
> 实现计划：`docs/wip/session-model-picker-plan.md`  
> 关联：`AGENTS.md`「模型路由」· `src/agent/llm.py` · `apps/web` WorkspaceComposer

---

## 1. 目标

在 Workspace composer 工具栏（现 `Agent 1.0 ▾` 位）提供 **会话级模型选择**，对标 Codex 输入框旁模型下拉。

用户可选：

| UI 短名 | `model_id` | Key 通道 |
|---------|------------|----------|
| Agnes | `agnes-2.0-flash` | light（`LLM_LIGHT_*`） |
| GPT 5.6 Luna | `gpt-5.6-luna` | heavy（`LLM_HEAVY_*` / `OPENAI_API_KEY`） |
| GPT 5.6 Sol | `gpt-5.6-sol` | heavy |
| GPT 5.6 Terra | `gpt-5.6-terra` | heavy |

**下拉默认展示**：**自动**（未钉扎；不传 `model_id`，走 catalog）。  
**是否钉扎**：见 §2 方案 A——展示「自动」**不等于**请求里带 `agnes`。

---

## 2. 已拍板行为

| 项 | 决定 |
|----|------|
| 作用域 | **仅当前会话**；新会话恢复「未钉扎 + UI 显示 Agnes」；本阶段不做跨会话记忆 |
| 钉扎策略 | **方案 A（显式钉扎）**——见下 |
| 覆盖强度 | **仅钉扎后硬覆盖**：intent / 记忆压缩 / 分析等全部走该 `model_id`，不再走 light/heavy catalog |
| 未钉扎 | **不传** `model_id`（或 API 收到 `null`）→ 走现有 catalog（`task` / `tier` → light\|heavy） |
| 黑盒任务 | 纯 MCP 黑盒 Skill：选择器 **disabled** +「本任务不走对话模型」；会话钉扎可保留，**本任务忽略** |
| UI 位置 | `WorkspaceComposer` 工具栏右侧，替换 `Agent 1.0 ▾` |
| 非法 `model_id` | **HTTP 400**（白名单外一律拒绝） |

### 2.1 方案 A：显式钉扎（锁定）

| 用户动作 | FE | 请求体 `model_id` | Runtime |
|----------|-----|-------------------|---------|
| 未改下拉（保持视觉默认 Agnes） | `pinned=false` | **省略 / null** | catalog |
| 主动选 Agnes / Luna / Sol / Terra | `pinned=true` | 传对应 id | **硬覆盖** |
| 再选回「自动（推荐）」*可选* | `pinned=false` | 省略 / null | catalog |

说明：

- UI 可增加第五项「自动（按任务）」清除钉扎；若第一版只做四模型，则 **只要用户点开并选过任一项即视为钉扎**（含选 Agnes）。未交互则不传。  
- 禁止「默认就带 `model_id=agnes`」——那会杀死 catalog 的 heavy 路径。

（方案 B `model_pinned: bool` 本版不采用，避免双字段。）

---

## 3. 路由优先级（实现契约）

```
1. Skill ∈ 黑盒集合 → 不调用 get_chat_model；忽略 model_id（若传入可存档但不使用）
2. 请求带合法且非空 model_id（显式钉扎）→ 强制该模型 + 按 id 选 Key
3. 否则 → catalog：tier / task → light|heavy
4. 再否则 → 默认 light（agnes 通道）
```

合法白名单：

```text
agnes-2.0-flash
gpt-5.6-luna
gpt-5.6-sol
gpt-5.6-terra
```

非法 → **HTTP 400**，body 含明确错误（如 `model_id not in allowlist`）。

黑盒 Skill 集合（单源常量，FE/API/Runtime 共用或 API 下发）：

| skill id | 说明 |
|----------|------|
| `temu-product-listing` | Commander Temu 上架黑盒 |

扩展时只改该集合，禁止各端手写分叉。

---

## 4. 会话语义与 FE 传参（写死）

现状：composer → `navigate` → NewTask → `POST` 创建；Runtime `thread_id ≈ task_id`。

| 层 | 「当前会话」 |
|----|----------------|
| FE | 一次 Workspace 停留内的 composer 状态：`model_id: string \| null` + `pinned: boolean`（可 `sessionStorage` 防刷新） |
| 跨页 | **必须**经 `location.state`（或等价）传入下游页，不得丢失 |
| API | 写入 `TaskRecord.model_id`（可为 null）；重试/再跑沿用该字段 |
| Runtime | `AgentState.model_id`；仅非空时硬覆盖 |

### 4.1 FE 数据流

```
WorkspaceComposer
  state: { pinned, modelId | null }   // 未钉扎 modelId 可仍为 UI 展示用 agnes，但不写入 navigate
  navigate(base, { state: {
    topic: string,
    model_id: string | null,   // 仅 pinned 时为白名单 id，否则 null
    model_pinned: boolean      // 可选，便于 NewTask 展示；API 只认 model_id 有无
  }})

NewTaskPage / DevNewTaskPage
  读 location.state.model_id
  POST /api/tasks { ..., model_id?: string }   // 仅非 null 时带字段

Temu 上架页（若独立）
  不依赖 composer 钉扎生效；选择器灰掉；POST temu-listing 可不传或传了也被忽略
```

`model_pinned` 仅 FE 可选；**API 契约只以 `model_id` 有无表示是否钉扎**（有值=钉扎，null/缺省=未钉扎）。

---

## 5. UI 规格与黑盒灰掉（按页面 / skill）

### 5.1 通用

- 控件：chip + 菜单；选项含四模型；未钉扎时展示「Agnes」或「自动 · Agnes」需在实现时统一文案（推荐：**自动** 为未钉扎标签，打开后可选四模型）。  
- 业务 / 开发视图均可显示；开发视图任务详情额外显示原始 `model_id`（null 显示「catalog」）。

### 5.2 灰掉规则（枚举，不靠「将要选」）

| 页面 / 路由 | skill（若已知） | 选择器 |
|-------------|-----------------|--------|
| `/`、`/dev` 首页 composer | 未知 | **可用**（可钉扎） |
| `/tasks/new`、`/dev/tasks/new` 且表单 skill=`douyin-keyword-research` | 非黑盒 | **可用** |
| `/tasks/temu`、`/dev/tasks/temu`（Temu 上架页） | `temu-product-listing` | **进入即 disabled** +「本任务不走对话模型」（`WorkspaceComposer blackbox`） |
| `/tasks/new` 等且 skill=`temu-product-listing` | 黑盒 | **disabled** + 同上文案 |
| 任务详情页（只读回显） | 任意 | 非选择器；黑盒显示「未使用对话模型」 |

判定以 **当前页绑定的 skill / 提交用的 skill** 为准，不以用户意图猜测。

---

## 6. API 创建入口（全量）

凡创建任务的入口统一可选 `model_id`（缺省/null=未钉扎；有值必须在白名单否则 400）。黑盒入口校验通过后 **忽略** 该字段（可不写 400，建议仍校验白名单再忽略，避免脏数据入库；或黑盒直接 strip——实现选 **strip 且不 400** 若仅黑盒页误传）。

| 方法 | 路径 | skill | `model_id` |
|------|------|-------|------------|
| `POST` | `/api/tasks` | body.skill（douyin / temu） | 可选；temu 时忽略 |
| `POST` | `/api/tasks/temu-listing` | 固定 `temu-product-listing` | 可选表单字段；**忽略** |
| `POST` | `/api/tasks/upload` | 仅上传 | **无**（不涉及模型） |

后续若增创建入口：必须同样遵守白名单 + 黑盒忽略。

改动面：

| 层 | 改动 |
|----|------|
| `TaskCreateRequest` / temu 表单 | `model_id: str \| None` |
| `TaskRecord` / `TaskDetail` | 回显 `model_id` |
| `AgentState` | `model_id` |
| `get_chat_model` | `model_id=` 硬覆盖 + 按 id 选 Key |
| 黑盒常量 | 单源（如 `src/agent/constants.py` + FE 镜像或 API 下发） |
| `WorkspaceComposer` + NewTask | §4.1 传参 |
| `AGENTS.md` | 会话显式 `model_id` 优先于 catalog；未传则 catalog |

---

## 7. 非目标

- 按 token/难度自动升档  
- luna/sol/terra 长文对比（UI 可用极短副标题；默认强档推荐 Luna）  
- 黑盒任务假装走用户所选模型  
- 账号级 / 跨设备默认模型  
- 方案 B（`model_pinned` 进 API）

---

## 8. 验收（分层）

### 8.1 必过：工厂 / API 单测（无业务 LLM 节点也可）

1. `model_id=null` → `resolve` 走 catalog（如 `ops_analysis`→heavy 模型名）。  
2. `model_id=gpt-5.6-luna` → 任意 task 标签仍解析为 luna + heavy Key。  
3. `model_id=agnes-2.0-flash` 钉扎 → 不走 heavy catalog。  
4. 非法 `model_id` → API **400**。  
5. `skill=temu-product-listing` → 即使带 `model_id` 也不改变 MCP/Commander 路径（可 assert 未调用 chat factory 或 ignore 标志）。

### 8.2 FE 行为（组件 / 手工）

1. 首页未点模型：navigate state 中 `model_id` 为 null。  
2. 选中 Luna 后：state 与后续 `POST /tasks` 带 `gpt-5.6-luna`。  
3. Temu 上架页：选择器 disabled + 文案；上架 E2E 成功不依赖模型。

### 8.3 暂缓：带真实 LLM 节点的 E2E

当前 Runtime 多数步骤无 `get_chat_model` 调用。待意图分类等节点接线后，再补：

- 钉扎 Luna 时，intent 步实际请求模型 id = `gpt-5.6-luna`（可用 mock transport / 日志断言）。

---

## 9. 确认

**已确认**（2026-07-24）。实现见 `docs/wip/session-model-picker-plan.md`。
