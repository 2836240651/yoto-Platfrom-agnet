import { useState } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import { api } from '../api/client'

const PLATFORM_OPTIONS = [
  { value: 1, label: '小红书' },
  { value: 2, label: '视频号' },
  { value: 3, label: '抖音' },
  { value: 4, label: '快手' },
  { value: 5, label: 'TikTok' },
]

/**
 * Social black-box publish: no chat composer; model picker disabled.
 */
export function SocialPublishPage() {
  const navigate = useNavigate()
  const { isDev } = useOutletContext<{ isDev?: boolean }>() ?? {}
  const [platformType, setPlatformType] = useState(3)
  const [title, setTitle] = useState('')
  const [accountList, setAccountList] = useState('')
  const [tags, setTags] = useState('')
  const [agentId, setAgentId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file || !title.trim() || !accountList.trim()) return
    setLoading(true)
    setError('')
    try {
      const task = await api.createSocialPublish({
        platformType,
        title: title.trim(),
        accountList: accountList.trim(),
        file,
        tags: tags.trim() || undefined,
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
      <h2 className="page-title">社媒发布</h2>
      <p
        className="composer-chip composer-chip--model composer-chip--disabled"
        style={{ cursor: 'default', marginBottom: 8 }}
      >
        本任务不走对话模型
      </p>
      <p style={{ color: 'var(--muted)', marginTop: 0, fontSize: '0.9rem' }}>
        上传素材后经 MCP 调用 automedia / 肉机 login-agent 发布（黑盒 Job）。TikTok 须助手在线。
      </p>

      <form onSubmit={handleSubmit} className="card" style={{ marginTop: 16 }}>
        <div className="form-group">
          <label htmlFor="platform">平台</label>
          <select
            id="platform"
            value={platformType}
            onChange={(e) => setPlatformType(Number(e.target.value))}
          >
            {PLATFORM_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="title">标题</label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="accounts">账号（cookie 文件名，逗号分隔）</label>
          <input
            id="accounts"
            type="text"
            value={accountList}
            onChange={(e) => setAccountList(e.target.value)}
            placeholder="如：douyin_xxx.json"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="tags">标签（可选，逗号分隔）</label>
          <input
            id="tags"
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label htmlFor="agent">助手 agent_id（可选）</label>
          <input
            id="agent"
            type="text"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label htmlFor="media">视频 / 素材</label>
          <input
            id="media"
            type="file"
            accept="video/*,image/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
        </div>
        {error && <p style={{ color: 'var(--down)' }}>{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? '提交中…' : '开始发布'}
        </button>
      </form>

      <p style={{ marginTop: 16 }}>
        <Link to={isDev ? '/dev/tasks' : '/tasks'}>返回任务列表</Link>
      </p>
    </div>
  )
}
