import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { WorkspaceComposer } from '../components/WorkspaceComposer'
import type { TaskListItem } from '../types/task'

export function DevHomePage() {
  const [tasks, setTasks] = useState<TaskListItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.listTasks(6).then((r) => setTasks(r.items)).finally(() => setLoading(false))
  }, [])

  return (
    <>
      <h1 className="workspace-hero-title">我们应该在 workspace 中构建什么？</h1>
      <WorkspaceComposer devMode />

      <div className="thread-list">
        {!loading &&
          tasks.map((t) => (
            <Link key={t.id} className="thread-list-item" to={`/dev/tasks/${t.id}`}>
              <span className="thread-list-icon">◷</span>
              <span>{t.title || t.seed || t.id}</span>
            </Link>
          ))}

        <div className="thread-list-hint">
          <span>+</span>
          <span>开发视图：点「+」选 Skill/Temu；工具状态只读；MCP 管理见侧栏</span>
        </div>
      </div>
    </>
  )
}
