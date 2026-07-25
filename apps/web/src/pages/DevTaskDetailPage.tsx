import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { ReportTabs } from '../components/ReportTabs'
import { StatGrid } from '../components/StatGrid'
import { DevTaskProgressBar } from '../components/DevTaskProgress'
import { DevLoopPanel } from '../components/DevLoopPanel'
import { TemuListingReportView } from '../components/TemuListingReportView'
import { SocialPublishReportView } from '../components/SocialPublishReportView'
import {
  isDouyinReport,
  isSocialPublishReport,
  isTemuListingReport,
  type TaskDetail,
} from '../types/task'

export function DevTaskDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [task, setTask] = useState<TaskDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    let active = true
    let timer: ReturnType<typeof setInterval>

    const load = async () => {
      try {
        const data = await api.getTask(id)
        if (!active) return
        setTask(data)
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(timer)
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : '加载失败')
      }
    }

    load()
    timer = setInterval(load, 2000)
    return () => {
      active = false
      clearInterval(timer)
    }
  }, [id])

  if (error) {
    return <p style={{ color: 'var(--down)' }}>{error}</p>
  }

  if (!task) {
    return <p style={{ color: 'var(--muted)' }}>加载中…</p>
  }

  const retryTo =
    task.skill === 'temu-product-listing'
      ? '/dev/tasks/temu'
      : task.skill === 'social-media-publish'
        ? '/dev/tasks/social'
        : '/dev/tasks/new'

  if (task.status === 'failed') {
    return (
      <div>
        <div className="card">
          <h2 style={{ color: 'var(--down)', marginBottom: 12 }}>任务失败（Dev）</h2>
          <p style={{ marginBottom: 16 }}>{task.error_message ?? '未知错误，请稍后重试'}</p>
          <Link to={retryTo} className="btn btn-primary" style={{ textDecoration: 'none' }}>
            重新执行（Dev）
          </Link>
        </div>
        <DevLoopPanel task={task} />
      </div>
    )
  }

  if (task.status !== 'completed') {
    return (
      <div>
        <DevTaskProgressBar progress={task.progress} />
        <DevLoopPanel task={task} />
      </div>
    )
  }

  const report = task.report
  if (!report) {
    return (
      <div>
        <p style={{ color: 'var(--muted)' }}>无报告数据</p>
        <DevLoopPanel task={task} />
      </div>
    )
  }

  if (isTemuListingReport(report)) {
    return (
      <div>
        <header style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>
            Temu 上架 · {task.shop_id || task.id}（Dev）
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: 6 }}>
            完成时间：
            {task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '—'}
            {task.model_id ? ` · model_id=${task.model_id}（黑盒已忽略）` : ' · model_id=null'}
          </p>
        </header>
        <TemuListingReportView report={report} />
        <DevLoopPanel task={task} />
        <div style={{ marginTop: 32 }}>
          <Link
            to="/dev/tasks/temu"
            className="btn btn-secondary"
            style={{ textDecoration: 'none' }}
          >
            再上一批
          </Link>
          <Link
            to="/dev/tasks"
            className="btn btn-secondary"
            style={{ textDecoration: 'none', marginLeft: 8 }}
          >
            返回开发历史
          </Link>
        </div>
      </div>
    )
  }

  if (isSocialPublishReport(report)) {
    return (
      <div>
        <header style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>
            社媒发布 · {report.title || task.id}（Dev）
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: 6 }}>
            完成时间：
            {task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '—'}
          </p>
        </header>
        <SocialPublishReportView report={report} />
        <DevLoopPanel task={task} />
        <div style={{ marginTop: 32 }}>
          <Link
            to="/dev/tasks/social"
            className="btn btn-secondary"
            style={{ textDecoration: 'none' }}
          >
            再发一条
          </Link>
          <Link
            to="/dev/tasks"
            className="btn btn-secondary"
            style={{ textDecoration: 'none', marginLeft: 8 }}
          >
            返回开发历史
          </Link>
        </div>
      </div>
    )
  }

  if (!isDouyinReport(report)) {
    return (
      <div>
        <div className="card">
          <p style={{ color: 'var(--down)' }}>未知报告类型</p>
        </div>
        <DevLoopPanel task={task} />
      </div>
    )
  }

  return (
    <div>
      <header style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>
          {(task.seed || task.skill || task.id)} · 任务交付报告（Dev）
        </h2>
        <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: 6 }}>
          完成时间：{task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '—'}
          {task.model_id ? ` · model_id=${task.model_id}` : ' · catalog'}
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
          {report.tags.map((tag) => (
            <span
              key={tag}
              style={{
                fontSize: '0.78rem',
                padding: '4px 10px',
                borderRadius: 999,
                background: '#e6f7f5',
                color: '#0f766e',
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      </header>

      <StatGrid summary={report.summary} />

      {report.alerts.map((a) => (
        <div
          key={a.text}
          style={{
            background: a.type === 'warn' ? '#fff7ed' : '#ecfdf5',
            border: `1px solid ${a.type === 'warn' ? '#fed7aa' : '#a7f3d0'}`,
            borderRadius: 12,
            padding: '14px 18px',
            marginBottom: 12,
            fontSize: '0.92rem',
          }}
        >
          {a.text}
        </div>
      ))}

      <h2
        style={{
          fontSize: '1.15rem',
          margin: '28px 0 16px',
          paddingBottom: 8,
          borderBottom: '2px solid var(--accent)',
        }}
      >
        结果明细
      </h2>
      <ReportTabs report={report} />

      <DevLoopPanel task={task} />

      <div style={{ marginTop: 32 }}>
        <Link to="/dev/tasks" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
          返回开发历史
        </Link>
      </div>
    </div>
  )
}
