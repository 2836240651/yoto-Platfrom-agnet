import { FormEvent, useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { MCPOverview } from '../types/mcp'

const EMPTY_FORM = {
  id: '',
  command: 'python',
  args: '',
  transport: 'stdio',
}

export function DevMcpPage() {
  const [data, setData] = useState<MCPOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async (withHealth = false) => {
    setLoading(true)
    setError(null)
    try {
      const overview = await api.mcpOverview(withHealth)
      setData(overview)
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load(false)
  }, [load])

  async function onHealthCheck() {
    setBusy(true)
    try {
      await load(true)
    } finally {
      setBusy(false)
    }
  }

  async function onReload() {
    setBusy(true)
    try {
      await api.mcpReload()
      await load(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : '重载失败')
    } finally {
      setBusy(false)
    }
  }

  async function onDelete(serverId: string) {
    if (!confirm(`删除 MCP 服务 ${serverId}？`)) return
    setBusy(true)
    try {
      await api.mcpDeleteServer(serverId)
      await load(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : '删除失败')
    } finally {
      setBusy(false)
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!form.id.trim() || !form.command.trim()) return
    setBusy(true)
    setError(null)
    try {
      await api.mcpCreateServer({
        id: form.id.trim(),
        transport: form.transport,
        command: form.command.trim(),
        args: form.args
          .split('\n')
          .map((s) => s.trim())
          .filter(Boolean),
        env: {},
      })
      setForm(EMPTY_FORM)
      await load(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : '添加失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mcp-page">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">MCP 服务管理</h1>
          <p className="page-subtitle">开发视图 · 注册 MCP server、健康检查、工具别名映射</p>
        </div>
        <button type="button" className="btn-primary" onClick={onReload} disabled={busy || loading}>
          重载 Runtime
        </button>
        <button type="button" className="btn" onClick={onHealthCheck} disabled={busy || loading}>
          健康检查
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <p className="muted">加载中…</p>}

      {data && (
        <>
          <section className="card-block">
            <h2>Runtime 状态</h2>
            <div className="stat-grid">
              <div className="stat-item">
                <div className="stat-value">{data.runtime.ok ? 'OK' : 'FAIL'}</div>
                <div className="stat-label">连接状态</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{data.runtime.tool_count}</div>
                <div className="stat-label">已发现工具</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{data.servers.length}</div>
                <div className="stat-label">已注册 Server</div>
              </div>
            </div>
            {!data.runtime.ok && data.runtime.error && (
              <p className="muted" style={{ marginTop: 12 }}>
                {data.runtime.error}
              </p>
            )}
            <p className="muted" style={{ marginTop: 8, fontSize: '0.8rem' }}>
              配置：{data.runtime.config_path}
            </p>
          </section>

          <section className="card-block">
            <h2>Server 列表</h2>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Command</th>
                    <th>Args</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {data.servers.map((s) => (
                    <tr key={s.id}>
                      <td>{s.id}</td>
                      <td className="mono">{s.command}</td>
                      <td className="mono">{(s.args || []).join(' ')}</td>
                      <td>
                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={() => onDelete(s.id)}
                          disabled={busy}
                        >
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="card-block">
            <h2>Server 健康检查（按需）</h2>
            {data.server_health.length === 0 ? (
              <p className="muted">尚未探测。点击「健康检查」运行。</p>
            ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>状态</th>
                    <th>工具数</th>
                    <th>延迟</th>
                    <th>示例工具</th>
                  </tr>
                </thead>
                <tbody>
                  {data.server_health.map((s) => (
                    <tr key={s.id}>
                      <td>{s.id}</td>
                      <td>{s.ok ? '✅' : '❌'}</td>
                      <td>{s.tool_count}</td>
                      <td>{s.latency_ms}ms</td>
                      <td className="mono">{(s.tools_sample || []).join(', ') || s.error || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            )}
          </section>

          <section className="card-block">
            <h2>添加 MCP Server</h2>
            <form className="mcp-form" onSubmit={onSubmit}>
              <label>
                Server ID
                <input
                  value={form.id}
                  onChange={(e) => setForm({ ...form, id: e.target.value })}
                  placeholder="reverse_lab_tools"
                  required
                />
              </label>
              <label>
                Command
                <input
                  value={form.command}
                  onChange={(e) => setForm({ ...form, command: e.target.value })}
                  placeholder="python"
                  required
                />
              </label>
              <label>
                Args（每行一个）
                <textarea
                  value={form.args}
                  onChange={(e) => setForm({ ...form, args: e.target.value })}
                  placeholder={'D:/path/to/server.py'}
                  rows={3}
                />
              </label>
              <button type="submit" className="btn-primary" disabled={busy}>
                保存并热重载
              </button>
            </form>
          </section>

          <section className="card-block">
            <h2>Tool 别名映射</h2>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>逻辑名 (Skill)</th>
                    <th>MCP Tool</th>
                    <th>Server</th>
                    <th>说明</th>
                  </tr>
                </thead>
                <tbody>
                  {data.aliases.map((a) => (
                    <tr key={a.logical_name}>
                      <td className="mono">{a.logical_name}</td>
                      <td className="mono">{a.mcp_tool || '—'}</td>
                      <td>{a.server || '—'}</td>
                      <td>{a.description || (a.use_mcp ? '' : 'stub only')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="muted" style={{ marginTop: 8, fontSize: '0.8rem' }}>
              映射文件：config/tool_registry.json
            </p>
          </section>

          <section className="card-block">
            <h2>已发现 MCP 工具（前 40）</h2>
            <pre className="code-block">{data.tools.slice(0, 40).join('\n')}</pre>
          </section>
        </>
      )}
    </div>
  )
}
