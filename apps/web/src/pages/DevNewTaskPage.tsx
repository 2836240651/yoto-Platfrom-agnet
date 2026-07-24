import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { ComposerNavigateState, ModelId } from '../constants/models'
import { modelLabel } from '../constants/models'

export function DevNewTaskPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const navState = (location.state as ComposerNavigateState | null) ?? {}
  const initialTopic = navState.topic ?? ''
  const pinnedModelId = (navState.model_id ?? null) as ModelId | null
  const [seed, setSeed] = useState(initialTopic || '渔具')
  const [includeVideo, setIncludeVideo] = useState(true)
  const [includeProduct, setIncludeProduct] = useState(true)
  const [dateRange, setDateRange] = useState<7 | 30 | 90>(30)
  const [confirmed, setConfirmed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!confirmed) return
    setLoading(true)
    setError('')
    try {
      const body: Parameters<typeof api.createTask>[0] = {
        skill: 'douyin-keyword-research',
        seed: seed.trim(),
        include_video: includeVideo,
        include_product: includeProduct,
        date_range_days: dateRange,
      }
      if (pinnedModelId) {
        body.model_id = pinnedModelId
      }
      const task = await api.createTask(body)
      navigate(`/dev/tasks/${task.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setLoading(false)
    }
  }

  const canSubmit = confirmed && !loading && Boolean(seed.trim())

  return (
    <div style={{ maxWidth: 560 }}>
      <h2 className="page-title">配置任务参数（开发）</h2>
      <form onSubmit={handleSubmit} className="card">
        <div className="form-group">
          <label htmlFor="seed">种子词</label>
          <input
            id="seed"
            type="text"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            placeholder="如：渔具"
            maxLength={20}
            required
          />
        </div>
        <div className="form-group">
          <label>会话模型</label>
          <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--muted)' }}>
            {pinnedModelId
              ? `已钉扎：${modelLabel(pinnedModelId)}（model_id=${pinnedModelId}）`
              : '自动 / catalog（model_id=null）'}
          </p>
        </div>
        <div className="form-group">
          <label>执行模块</label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={includeVideo}
              onChange={(e) => setIncludeVideo(e.target.checked)}
            />
            内容洞察模块
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={includeProduct}
              onChange={(e) => setIncludeProduct(e.target.checked)}
            />
            商业机会模块
          </label>
        </div>

        <div className="form-group">
          <label htmlFor="range">时间窗口</label>
          <select
            id="range"
            value={dateRange}
            onChange={(e) => setDateRange(Number(e.target.value) as 7 | 30 | 90)}
          >
            <option value={7}>近 7 天</option>
            <option value={30}>近 30 天</option>
            <option value={90}>近 90 天</option>
          </select>
        </div>

        <label className="checkbox-row" style={{ marginBottom: 16 }}>
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          我已确认参数无误
        </label>

        {error && (
          <p style={{ color: 'var(--down)', marginBottom: 12, fontSize: '0.9rem' }}>{error}</p>
        )}

        <button type="submit" className="btn btn-primary" disabled={!canSubmit}>
          {loading ? '提交中…' : '开始执行（Dev）'}
        </button>
      </form>
    </div>
  )
}
