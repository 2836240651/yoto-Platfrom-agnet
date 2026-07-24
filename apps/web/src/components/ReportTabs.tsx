import { useState } from 'react'
import type { DouyinTaskReport, TaskReport } from '../types/task'
import { isDouyinReport, isTemuListingReport, sourceBadgeLabel } from '../types/task'
import { KeywordCard } from './KeywordCard'

const TABS = [
  { key: 'video_hot', label: '内容热点' },
  { key: 'video_potential', label: '内容潜力' },
  { key: 'product_hot', label: '机会热点' },
  { key: 'product_potential', label: '机会潜力' },
] as const

type TabKey = (typeof TABS)[number]['key']

function SourceBadge({ source }: { source?: string | null }) {
  const label = sourceBadgeLabel(source)
  const color =
    source === 'mcp' ? 'var(--p0)' : source === 'stub_fallback' ? '#d97706' : 'var(--muted)'
  return (
    <span
      style={{
        display: 'inline-block',
        fontSize: '0.75rem',
        fontWeight: 600,
        padding: '3px 8px',
        borderRadius: 6,
        border: `1px solid ${color}`,
        color,
        marginBottom: 12,
      }}
    >
      {label}
    </span>
  )
}

export function ReportTabs({ report }: { report: TaskReport }) {
  if (isTemuListingReport(report)) {
    return null
  }
  if (!isDouyinReport(report)) {
    return <p style={{ color: 'var(--down)' }}>未知报告类型：{(report as { kind?: string }).kind}</p>
  }
  return <DouyinReportView report={report} />
}

function DouyinReportView({ report }: { report: DouyinTaskReport }) {
  const [tab, setTab] = useState<TabKey>('video_hot')
  const cards = report.categories[tab]
  const source = report.data_source?.source || 'stub'

  return (
    <div>
      <SourceBadge source={source} />
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className="btn"
            onClick={() => setTab(t.key)}
            style={{
              background: tab === t.key ? 'var(--accent)' : '#fff',
              color: tab === t.key ? '#fff' : 'var(--text)',
              border: '1px solid var(--border)',
              padding: '8px 16px',
            }}
          >
            {t.label} ({report.categories[t.key].length})
          </button>
        ))}
      </div>
      {cards.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>本分类暂无数据</p>
      ) : (
        cards.map((c) => <KeywordCard key={c.keyword} card={c} />)
      )}
    </div>
  )
}
