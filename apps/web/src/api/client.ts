import type { TaskCreateRequest, TaskDetail, TaskListItem } from '../types/task'
import type { MCPOverview, MCPServer, MCPServerCreateRequest } from '../types/mcp'
import type { ToolsStatusResponse } from '../types/tools'


export type DouyinBossRange = 'day' | '7d' | '30d'

export interface DouyinBossReport {
  platform: 'douyin'
  available: boolean
  empty_message: string | null
  range: DouyinBossRange
  data_as_of: string
  start_date: string | null
  statistics_period: string
  video_statistics_period: string | null
  available_start_date: string | null
  available_end_date: string | null
  imported_at: string | null
  metrics: {
    user_payment_amount: string | null
    transaction_order_count: number | null
    transaction_user_count: number | null
    transaction_item_count: number | null
    product_impression_count: number | null
    product_click_count: number | null
    product_impression_click_rate: string | null
    product_click_conversion_rate: string | null
    refund_amount: string | null
    refund_order_count: number | null
  } | null
  products: Array<{
    product_id: string
    product_name: string | null
    user_payment_amount: string | null
    transaction_order_count: number | null
    product_click_conversion_rate: string | null
  }>
  videos: Array<{
    video_id: string
    video_title: string | null
    video_user_payment_amount: string | null
    transaction_order_count: number | null
    view_count: number | null
    completion_rate: string | null
  }>
}
const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `请求失败: ${res.status}`)
  }
  return res.json() as Promise<T>
}

function mcpWriteHeaders(): HeadersInit {
  const token = (import.meta as { env?: { VITE_MCP_WRITE_TOKEN?: string } }).env?.VITE_MCP_WRITE_TOKEN
  return token ? { 'X-MCP-Write-Token': token } : {}
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  createTask: (body: TaskCreateRequest) =>
    request<TaskDetail>('/tasks', { method: 'POST', body: JSON.stringify(body) }),
  createTemuListing: async (params: {
    shopId: string
    file: File
    agentId?: string
    platform?: string
  }) => {
    const fd = new FormData()
    fd.append('shop_id', params.shopId)
    fd.append('file', params.file)
    if (params.agentId) fd.append('agent_id', params.agentId)
    fd.append('platform', params.platform || 'temu')
    const res = await fetch(`${BASE}/tasks/temu-listing`, { method: 'POST', body: fd })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || `请求失败: ${res.status}`)
    }
    return res.json() as Promise<TaskDetail>
  },
  createSocialPublish: async (params: {
    platformType: number
    title: string
    accountList: string
    file: File
    tags?: string
    agentId?: string
  }) => {
    const fd = new FormData()
    fd.append('platform_type', String(params.platformType))
    fd.append('title', params.title)
    fd.append('account_list', params.accountList)
    fd.append('file', params.file)
    if (params.tags) fd.append('tags', params.tags)
    if (params.agentId) fd.append('agent_id', params.agentId)
    const res = await fetch(`${BASE}/tasks/social-publish`, { method: 'POST', body: fd })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || `请求失败: ${res.status}`)
    }
    return res.json() as Promise<TaskDetail>
  },
  listTasks: (limit = 20) =>
    request<{ items: TaskListItem[]; total: number }>(`/tasks?limit=${limit}`),
  getTask: (id: string) => request<TaskDetail>(`/tasks/${id}`),
  toolsStatus: () => request<ToolsStatusResponse>('/tools/status'),
  getDouyinBossReport: (range: DouyinBossRange, endDate?: string) =>
    request<DouyinBossReport>(
      '/boss/douyin?range=' + range + (endDate ? '&end_date=' + encodeURIComponent(endDate) : ''),
    ),

  mcpOverview: (health = false) =>
    request<MCPOverview>(`/mcp${health ? '?health=1' : ''}`),
  mcpReload: () =>
    request<{ ok: boolean; message: string }>('/mcp/reload', {
      method: 'POST',
      headers: mcpWriteHeaders(),
    }),
  mcpCreateServer: (body: MCPServerCreateRequest) =>
    request<MCPServer>('/mcp/servers', {
      method: 'POST',
      body: JSON.stringify(body),
      headers: mcpWriteHeaders(),
    }),
  mcpDeleteServer: (id: string) =>
    request<{ ok: boolean; deleted: string }>(`/mcp/servers/${id}`, {
      method: 'DELETE',
      headers: mcpWriteHeaders(),
    }),
}
