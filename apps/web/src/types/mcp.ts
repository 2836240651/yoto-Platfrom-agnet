export interface MCPServer {
  id: string
  transport: string
  command: string
  args: string[]
  env: Record<string, string>
}

export interface MCPServerHealth {
  id: string
  ok: boolean
  tool_count: number
  latency_ms: number
  error?: string | null
  tools_sample?: string[]
}

export interface MCPRuntimeStatus {
  ok: boolean
  error?: string | null
  tool_count: number
  config_path: string
}

export interface ToolAlias {
  logical_name: string
  mcp_tool?: string | null
  server?: string | null
  description: string
  arg_map: Record<string, string>
  defaults: Record<string, unknown>
  use_mcp: boolean
  allow_in_skills?: string[]
}

export interface MCPOverview {
  runtime: MCPRuntimeStatus
  servers: MCPServer[]
  server_health: MCPServerHealth[]
  aliases: ToolAlias[]
  tools: string[]
}

export interface MCPServerCreateRequest {
  id: string
  transport?: string
  command: string
  args?: string[]
  env?: Record<string, string>
}
