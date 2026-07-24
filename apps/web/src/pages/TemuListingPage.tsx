import { useState } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import { api } from '../api/client'

/**
 * Temu black-box listing: no chat composer; model picker conceptually disabled.
 */
export function TemuListingPage() {
  const navigate = useNavigate()
  const { isDev } = useOutletContext<{ isDev?: boolean }>() ?? {}
  const [shopId, setShopId] = useState('')
  const [agentId, setAgentId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file || !shopId.trim()) return
    setLoading(true)
    setError('')
    try {
      const task = await api.createTemuListing({
        shopId: shopId.trim(),
        file,
        agentId: agentId.trim() || undefined,
      })
      navigate(isDev ? `/dev/tasks/${task.id}` : `/tasks/${task.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 560 }}>
      <h2 className="page-title">Temu 批量上架</h2>
      <p
        className="composer-chip composer-chip--model composer-chip--disabled"
        style={{ cursor: 'default', marginBottom: 8 }}
      >
        本任务不走对话模型
      </p>
      <p style={{ color: 'var(--muted)', marginTop: 0, fontSize: '0.9rem' }}>
        上传 Excel 后经 MCP 调用 Commander / 肉机完成上架（黑盒 Job）。
      </p>

      <form onSubmit={handleSubmit} className="card" style={{ marginTop: 16 }}>
        <div className="form-group">
          <label htmlFor="shop">店铺 ID</label>
          <input
            id="shop"
            type="text"
            value={shopId}
            onChange={(e) => setShopId(e.target.value)}
            placeholder="如：8381218"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="agent">Agent（可选，默认服务端配置）</label>
          <input
            id="agent"
            type="text"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            placeholder="如：肉机"
          />
        </div>
        <div className="form-group">
          <label htmlFor="excel">批量上货 Excel</label>
          <input
            id="excel"
            type="file"
            accept=".xlsx,.xls"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
        </div>

        {error && (
          <p style={{ color: 'var(--down)', marginBottom: 12, fontSize: '0.9rem' }}>{error}</p>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !file || !shopId.trim()}
        >
          {loading ? '提交中…' : '开始上架'}
        </button>
        <p style={{ marginTop: 12, fontSize: '0.85rem' }}>
          <Link to={isDev ? '/dev' : '/'}>返回对话</Link>
        </p>
      </form>
    </div>
  )
}
