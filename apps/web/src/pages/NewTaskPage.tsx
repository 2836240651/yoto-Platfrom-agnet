import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { ComposerNavigateState, ModelId } from '../constants/models'
import { modelLabel } from '../constants/models'

export function NewTaskPage() {
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
      navigate(`/tasks/${task.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 560 }}>
      <h2 className="page-title">配置任务参数</h2>
      <form onSubmit={handleSubmit} className="card">
        <div className="form-group">
          <label htmlFor="seed">任务主题 / 种子词</label>
          <input
            id="seed"
            type="text"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            placeholder="如：渔具、欧鲤钓、反底钓、路亚"
            maxLength={20}
            required
          />
          <p style={{ margin: '6px 0 0', fontSize: '0.82rem', color: 'var(--muted)' }}>
            支持细分玩法词；若蝉妈妈未收录，会自动桥接父词再分析热搜/潜力词。
          </p>
        </div>

        <div className="form-group">
          <label>会话模型</label>
          <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--muted)' }}>
            {pinnedModelId
              ? `已钉扎：${modelLabel(pinnedModelId)}`
              : '自动（按任务类型走 catalog，未钉扎）'}
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
            内容洞察模块（趋势 + 潜力）
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={includeProduct}
              onChange={(e) => setIncludeProduct(e.target.checked)}
            />
            商业机会模块（需求 + 转化）
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

        <div
          style={{
            background: '#f0fdfa',
            border: '1px solid #99f6e4',
            borderRadius: 10,
            padding: 14,
            marginBottom: 16,
            fontSize: '0.9rem',
          }}
        >
          <strong>将执行：</strong>采集 → 扩展长尾 → 热搜/潜力打分 → 四栏报告
          <br />
          <span style={{ color: 'var(--muted)' }}>目标数据源：蝉妈妈（肉机 MCP 真采）</span>
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

        <button
          type="submit"
          className="btn btn-primary"
          disabled={!confirmed || loading || !seed.trim()}
        >
          {loading ? '提交中…' : '开始执行'}
        </button>
      </form>
    </div>
  )
}
