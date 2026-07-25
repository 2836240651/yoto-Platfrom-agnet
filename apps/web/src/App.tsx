import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { NewTaskPage } from './pages/NewTaskPage'
import { TaskDetailPage } from './pages/TaskDetailPage'
import { TaskListPage } from './pages/TaskListPage'
import { DevHomePage } from './pages/DevHomePage'
import { DevNewTaskPage } from './pages/DevNewTaskPage'
import { DevTaskDetailPage } from './pages/DevTaskDetailPage'
import { DevTaskListPage } from './pages/DevTaskListPage'
import { DevMcpPage } from './pages/DevMcpPage'
import { TemuListingPage } from './pages/TemuListingPage'
import { SocialPublishPage } from './pages/SocialPublishPage'
import { ToolsStatusPage } from './pages/ToolsStatusPage'
import { BossPlatformPage } from './pages/BossPlatformPage'
import './styles/global.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/tools" element={<ToolsStatusPage />} />
          <Route path="/boss" element={<BossPlatformPage />} />
          <Route path="/boss/:platform" element={<BossPlatformPage />} />
          <Route path="/tasks" element={<TaskListPage />} />
          <Route path="/tasks/new" element={<NewTaskPage />} />
          <Route path="/tasks/temu" element={<TemuListingPage />} />
          <Route path="/tasks/social" element={<SocialPublishPage />} />
          <Route path="/tasks/:id" element={<TaskDetailPage />} />

          <Route path="/dev" element={<DevHomePage />} />
          <Route path="/dev/tools" element={<ToolsStatusPage />} />
          <Route path="/dev/tasks" element={<DevTaskListPage />} />
          <Route path="/dev/tasks/new" element={<DevNewTaskPage />} />
          <Route path="/dev/tasks/temu" element={<TemuListingPage />} />
          <Route path="/dev/tasks/social" element={<SocialPublishPage />} />
          <Route path="/dev/tasks/:id" element={<DevTaskDetailPage />} />
          <Route path="/dev/mcp" element={<DevMcpPage />} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
