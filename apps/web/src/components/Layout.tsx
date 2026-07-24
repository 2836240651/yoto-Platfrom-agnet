import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { api } from '../api/client'
import type { TaskListItem } from '../types/task'

function SidebarItem({
  to,
  icon,
  label,
  end,
}: {
  to: string
  icon: string
  label: string
  end?: boolean
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `sidebar-nav-item${isActive ? ' sidebar-nav-item--active' : ''}`
      }
    >
      <span className="sidebar-nav-icon">{icon}</span>
      {label}
    </NavLink>
  )
}

export function Layout() {
  const location = useLocation()
  const isDev = location.pathname.startsWith('/dev')
  const taskBase = isDev ? '/dev/tasks' : '/tasks'
  const homePath = isDev ? '/dev' : '/'
  const [recent, setRecent] = useState<TaskListItem[]>([])

  useEffect(() => {
    api.listTasks(8).then((r) => setRecent(r.items))
  }, [location.pathname])

  const isHome = location.pathname === '/' || location.pathname === '/dev'

  return (
    <div className="workspace-shell">
      <aside className="workspace-sidebar">
        <div className="sidebar-brand">Codex</div>

        <SidebarItem to={homePath} icon="✎" label="新对话" end />
        <SidebarItem to={`${taskBase}/temu`} icon="▣" label="Temu 上架" />
        <SidebarItem to={isDev ? '/dev/tools' : '/tools'} icon="◎" label="工具状态" />
        <SidebarItem to={taskBase} icon="◷" label="任务" />
        {isDev && <SidebarItem to="/dev/mcp" icon="⚙" label="MCP 管理" />}

        <div className="sidebar-section">
          <div className="sidebar-section-label">
            <span>项目</span>
            <span style={{ opacity: 0.5 }}>›</span>
          </div>
          <Link className="sidebar-thread" to={homePath}>
            agent-platform
          </Link>
        </div>

        <div className="sidebar-section" style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
          <div className="sidebar-section-label">
            <span>对话</span>
            <span style={{ opacity: 0.5 }}>›</span>
          </div>
          {recent.map((t) => (
            <Link
              key={t.id}
              className="sidebar-thread"
              to={`${taskBase}/${t.id}`}
              title={t.title || t.seed || t.id}
            >
              {t.title || t.seed || t.id}
            </Link>
          ))}
        </div>

        <div className="sidebar-footer">
          <Link className="sidebar-nav-item" to={isDev ? '/' : '/dev'}>
            <span className="sidebar-nav-icon">⇄</span>
            {isDev ? '运营视图' : '开发视图'}
          </Link>
        </div>
      </aside>

      <main className="workspace-main">
        <div
          className={`workspace-content${
            isHome ? ' workspace-content--center' : ' workspace-content--wide'
          }`}
        >
          <Outlet context={{ isDev }} />
        </div>
      </main>
    </div>
  )
}
