import { useState } from 'react'
import type { DouyinTaskReport, TaskReport } from '../types/task'
import { isDouyinReport, isTemuListingReport, sourceBadgeLabel } from '../types/task'
import { KeywordCard } from './KeywordCard'

const VIDEO_TABS = [
  { key: 'video_hot', label: '视频热搜' },
  { key: 'video_potential', label: '视频潜力' },
] as const

const PRODUCT_TABS = [
  { key: 'product_hot', label: '商品热搜' },
  { key: 'product_potential', label: '商品潜力' },
] as const

const TABS = [...VIDEO_TABS, ...PRODUCT_TABS] as const

type TabKey = (typeof TABS)[number]['key']
type Side = 'video' | 'product'

function sideOf(tab: TabKey): Side {
  return tab.startsWith('video') ? 'video' : 'product'
}

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

function SideSwitch({
  side,
  onChange,
  videoCount,
  productCount,
}: {
  side: Side
  onChange: (s: Side) => void
  videoCount: number
  productCount: number
}) {
  const btn = (id: Side, label: string, count: number) => (
    <button
      key={id}
      type="button"
      className="btn"
      onClick={() => onChange(id)}
      style={{
        background: side === id ? 'var(--accent)' : '#fff',
        color: side === id ? '#fff' : 'var(--text)',
        border: '1px solid var(--border)',
        padding: '10px 18px',
        fontWeight: 700,
      }}
    >
      {label}（{count}）
    </button>
  )
  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
      {btn('video', '视频侧 · 内容', videoCount)}
      {btn('product', '商品侧 · 带货', productCount)}
    </div>
  )
}

function DouyinReportView({ report }: { report: DouyinTaskReport }) {
  const [tab, setTab] = useState<TabKey>('video_hot')
  const side = sideOf(tab)
  const tabs = side === 'video' ? VIDEO_TABS : PRODUCT_TABS
  const cards = report.categories[tab]
  const source = report.data_source?.source || 'stub'
  const videoCount =
    report.categories.video_hot.length + report.categories.video_potential.length
  const productCount =
    report.categories.product_hot.length + report.categories.product_potential.length

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
        <SourceBadge source={source} />
        <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
          先选侧别，再看热搜 / 潜力分层
        </span>
      </div>

      <SideSwitch
        side={side}
        videoCount={videoCount}
        productCount={productCount}
        onChange={(s) => setTab(s === 'video' ? 'video_hot' : 'product_hot')}
      />

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            className="btn"
            onClick={() => setTab(t.key)}
            style={{
              background: tab === t.key ? '#0f766e' : '#fff',
              color: tab === t.key ? '#fff' : 'var(--text)',
              border: '1px solid var(--border)',
              padding: '8px 16px',
            }}
          >
            {t.label} ({report.categories[t.key].length})
          </button>
        ))}
      </div>

      <p style={{ fontSize: '0.88rem', color: 'var(--muted)', marginBottom: 16 }}>
        {side === 'video'
          ? '视频侧：话题 / 玩法 / 内容标题向关键词，适合做短视频与直播话术。'
          : '商品侧：可挂车规格 / 配件 / 卖点词，适合商品卡与带货转化。'}
      </p>

      {cards.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>本分类暂无数据</p>
      ) : (
        cards.map((c) => <KeywordCard key={c.keyword} card={c} side={side} />)
      )}
    </div>
  )
}
