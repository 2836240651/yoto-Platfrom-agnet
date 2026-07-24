export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed'
export type SkillId = 'douyin-keyword-research'

export interface MetricItem {
  label: string
  value: string
}

export interface KeywordCard {
  keyword: string
  priority: 'P0' | 'P1' | 'P2'
  trend: 'up' | 'flat' | 'down'
  reason: string
  metrics: MetricItem[]
  evidence: string[]
  action: string
}

export interface AlertItem {
  type: 'info' | 'warn'
  text: string
}

export interface DataSourceMeta {
  source: 'mcp' | 'stub' | 'stub_fallback'
  tool?: string | null
  resolved_tool?: string | null
  mcp_error?: string | null
}

export interface DouyinTaskReport {
  kind: 'douyin_keyword'
  summary: {
    keyword_count: number
    video_sample_count: number
    product_sku_count: number
    p0_count: number
  }
  tags: string[]
  alerts: AlertItem[]
  categories: {
    video_hot: KeywordCard[]
    video_potential: KeywordCard[]
    product_hot: KeywordCard[]
    product_potential: KeywordCard[]
  }
  data_source?: DataSourceMeta | null
}

export interface TemuListingReport {
  kind: 'temu_listing'
  ok: boolean
  status: 'processing' | 'success' | 'failed' | 'cancelled' | 'unknown'
  message: string
  shop_id?: string | null
  agent_id?: string | null
  task_id?: string | null
  data_source?: DataSourceMeta | null
}

export type TaskReport = DouyinTaskReport | TemuListingReport

export interface TaskProgress {
  step: number
  total_steps: number
  step_name: string
  percent: number
  micro_attempt?: number
  micro_budget?: number
  replan_used?: number
}

export interface TaskDebug {
  status?: string | null
  skill?: string | null
  current_action?: string | null
  micro_route?: string | null
  failure_class?: string | null
  user_error_message?: string | null
  last_tool_error?: string | null
  quality_score?: number | null
  consecutive_no_gain?: number | null
  global_loop_used?: number | null
  micro_budget_default?: number | null
  micro_budget_current?: number | null
  micro_budget_max?: number | null
  micro_budget_used?: number | null
  replan_budget_used?: number | null
  replan_used?: number | null
  current_step?: number | null
  plan?: Array<{
    id?: string
    name?: string
    label?: string
    tool?: string | null
    status?: string
  }> | null
  events?: Array<{
    ts?: string
    node?: string
    message?: string
    attempt?: number
    quality?: number
    failure_class?: string
  }> | null
  collected_meta?: Record<string, DataSourceMeta | null | undefined>
}

export interface TaskDetail {
  id: string
  skill?: SkillId | string
  seed?: string | null
  status: TaskStatus
  include_video: boolean
  include_product: boolean
  date_range_days: number
  shop_id?: string | null
  excel_path?: string | null
  agent_id?: string | null
  platform?: string | null
  /** Explicit session pin; null = catalog. */
  model_id?: string | null
  created_at: string
  completed_at?: string | null
  progress?: TaskProgress | null
  error_message?: string | null
  report?: TaskReport | null
  debug?: TaskDebug | null
}

export interface TaskListItem {
  id: string
  seed?: string | null
  skill?: string
  title?: string
  status: TaskStatus
  created_at: string
  completed_at?: string | null
}

export interface TaskCreateRequest {
  skill?: SkillId
  seed?: string
  include_video?: boolean
  include_product?: boolean
  date_range_days: 7 | 30 | 90
  /** Only when user explicitly pinned a model in composer. */
  model_id?: string | null
}

export function isDouyinReport(report: TaskReport): report is DouyinTaskReport {
  return report.kind === 'douyin_keyword'
}

export function isTemuListingReport(report: TaskReport): report is TemuListingReport {
  return report.kind === 'temu_listing'
}

export function sourceBadgeLabel(source?: string | null): string {
  if (source === 'mcp') return '真实 MCP'
  if (source === 'stub_fallback') return 'MCP 失败已降级'
  return '模拟数据'
}
