import { useCallback, useEffect, useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { api } from '../api/client'
import type { ToolsStatusResponse } from '../types/tools'

export function ToolsStatusPage() {
  const { isDev } = useOutletContext<{ isDev?: boolean }>() ?? {}
  const [data, setData] = useState<ToolsStatusResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(await api.toolsStatus())
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div style={{ maxWidth: 640 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 className="page-title">工具状态</h2>
        <button type="button" className="btn btn-secondary" onClick={load} disabled={loading}>
          {loading ? '刷新中…' : '刷新'}
        </button>
      </div>
      <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: 0 }}>
        只读探测：抖音词分析依赖 MCP 网关和抖音肉机（蝉妈妈）；跨境上架 Agent（Temu）是独立服务。API Key 由服务端配置。
      </p>

      {error && <p style={{ color: 'var(--down)' }}>{error}</p>}

      {data && (
        <>
          <div
            className="card"
            style={{
              marginBottom: 16,
              borderColor: data.ok ? '#a7f3d0' : '#fed7aa',
              background: data.ok ? '#ecfdf5' : '#fff7ed',
            }}
          >
            <strong>{data.ok ? '整体可用' : '部分不可用'}</strong>
            {data.note && (
              <p style={{ margin: '8px 0 0', fontSize: '0.85rem', color: 'var(--muted)' }}>
                {data.note}
              </p>
            )}
          </div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="table-shell">
              <thead>
                <tr>
                  <th>工具</th>
                  <th>状态</th>
                  <th>说明</th>
                </tr>
              </thead>
              <tbody>
                {data.probes.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 600 }}>{p.label}</td>
                    <td>
                      <span
                        className={`status-badge ${p.ok ? 'status-completed' : 'status-failed'}`}
                      >
                        {p.online === true
                          ? '在线'
                          : p.online === false
                            ? '离线'
                            : p.ok
                              ? '正常'
                              : '异常'}
                      </span>
                    </td>
                    <td style={{ color: 'var(--muted)', fontSize: '0.88rem' }}>
                      {p.detail || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <p style={{ marginTop: 20, fontSize: '0.85rem' }}>
        <Link to={isDev ? '/dev/tasks/temu' : '/tasks/temu'}>去 Temu 上架</Link>
        {' · '}
        <Link to={isDev ? '/dev' : '/'}>新对话</Link>
        {isDev && (
          <>
            {' · '}
            <Link to="/dev/mcp">MCP 管理（开发）</Link>
          </>
        )}
      </p>
    </div>
  )
}
