/** Read-only tools status (MCP + 肉机). No API keys. */

export interface ToolProbe {
  id: string
  label: string
  ok: boolean
  detail?: string
  online?: boolean | null
}

export interface ToolsStatusResponse {
  ok: boolean
  probes: ToolProbe[]
  note?: string
}
