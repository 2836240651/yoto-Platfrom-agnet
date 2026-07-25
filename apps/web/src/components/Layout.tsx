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

function ViewSwitcher() {
  return (
    <nav className="view-switcher" aria-label="工作区视角">
      <NavLink to="/" end>运营</NavLink>
      <NavLink to="/boss">BOSS</NavLink>
      <NavLink to="/dev">开发</NavLink>
    </nav>
  )
}

export function Layout() {
  const location = useLocation()
  const isBoss = location.pathname === '/boss' || location.pathname.startsWith('/boss/')
  const isDev = location.pathname.startsWith('/dev')
  const taskBase = isDev ? '/dev/tasks' : '/tasks'
  const homePath = isDev ? '/dev' : '/'
  const [recent, setRecent] = useState<TaskListItem[]>([])

  useEffect(() => {
    if (isBoss) {
      setRecent([])
      return
    }

    api.listTasks(8).then((response) => setRecent(response.items))
  }, [isBoss, location.pathname])

  const isHome = location.pathname === '/' || location.pathname === '/dev'

  return (
    <div className="workspace-shell">
      <aside className="workspace-sidebar">
        <div className="sidebar-brand">Agent Workspace</div>

        {isBoss ? (
          <div className="sidebar-section boss-sidebar-platforms">
            <div className="sidebar-section-label">平台数据</div>
            <SidebarItem to="/boss/douyin" icon="◉" label="抖音" />
            <SidebarItem to="/boss/1688" icon="◉" label="1688" />
            <SidebarItem to="/boss/temu" icon="◉" label="Temu" />
            <SidebarItem to="/boss/amazon" icon="◉" label="Amazon" />
          </div>
        ) : (
          <>
            <SidebarItem to={homePath} icon="✎" label="新对话" end />
            <SidebarItem to={`${taskBase}/temu`} icon="▣" label="Temu 上架" />
            <SidebarItem to={`${taskBase}/social`} icon="◈" label="社媒发布" />
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

            <div className="sidebar-section sidebar-section--scroll">
              <div className="sidebar-section-label">
                <span>对话</span>
                <span style={{ opacity: 0.5 }}>›</span>
              </div>
              {recent.map((task) => (
                <Link
                  key={task.id}
                  className="sidebar-thread"
                  to={`${taskBase}/${task.id}`}
                  title={task.title || task.seed || task.id}
                >
                  {task.title || task.seed || task.id}
                </Link>
              ))}
            </div>
          </>
        )}

        <div className="sidebar-footer">
          <ViewSwitcher />
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
