import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { TaskListItem } from '../types/task'

function statusLabel(s: TaskListItem['status']) {
  const map = { pending: '排队中', running: '执行中', completed: '已完成', failed: '失败' }
  return map[s]
}

export function TaskListPage() {
  const [tasks, setTasks] = useState<TaskListItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.listTasks(50).then((r) => {
      setTasks(r.items)
      setTotal(r.total)
    }).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 className="page-title">对话与任务 ({total})</h2>
        <Link to="/tasks/new" className="btn btn-primary" style={{ textDecoration: 'none' }}>
          新建任务
        </Link>
      </div>
      {loading ? (
        <p style={{ color: 'var(--muted)' }}>加载中…</p>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="table-shell">
            <thead>
              <tr>
                <th>主题</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontWeight: 600 }}>{t.title || t.seed || t.id}</td>
                  <td>
                    <span className={`status-badge status-${t.status}`}>{statusLabel(t.status)}</span>
                  </td>
                  <td style={{ color: 'var(--muted)' }}>
                    {new Date(t.created_at).toLocaleString('zh-CN')}
                  </td>
                  <td>
                    <Link to={`/tasks/${t.id}`}>查看</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
