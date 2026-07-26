import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type DouyinBossRange, type DouyinBossReport } from '../api/client'

const PLATFORMS = [
  { id: 'douyin', name: '抖音', description: '内容电商运营数据', connected: true },
  { id: '1688', name: '1688', description: '货源与采购运营数据', connected: false },
  { id: 'temu', name: 'Temu', description: '跨境店铺运营数据', connected: false },
  { id: 'amazon', name: 'Amazon', description: '跨境店铺运营数据', connected: false },
] as const

const RANGES: Array<{ id: DouyinBossRange; label: string }> = [
  { id: 'day', label: '单日' },
  { id: '7d', label: '近 7 天' },
  { id: '30d', label: '近 30 天' },
]

type PlatformId = (typeof PLATFORMS)[number]['id']

function isPlatformId(value: string | undefined): value is PlatformId {
  return PLATFORMS.some((platform) => platform.id === value)
}

function formatNumber(value: number | null | undefined): string {
  return value === null || value === undefined ? '—' : new Intl.NumberFormat('zh-CN').format(value)
}

function formatMoney(value: string | null | undefined): string {
  return value === null || value === undefined ? '—' : `¥${new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 2 }).format(Number(value))}`
}

function formatRate(value: string | null | undefined): string {
  return value === null || value === undefined ? '—' : `${(Number(value) * 100).toFixed(2)}%`
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  if (/^\d{8}$/.test(value)) return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`
  return value
}

function toInputDate(value: string | null | undefined): string {
  return value && /^\d{8}$/.test(value)
    ? `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`
    : ''
}

function fromInputDate(value: string): string {
  return value.replaceAll('-', '')
}

function DouyinBossView() {
  const [range, setRange] = useState<DouyinBossRange>('day')
  const [endDate, setEndDate] = useState('')
  const [report, setReport] = useState<DouyinBossReport | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    api.getDouyinBossReport(range, endDate ? fromInputDate(endDate) : undefined)
      .then((data) => {
        if (cancelled) return
        setReport(data)
        if (!endDate && data.data_as_of) setEndDate(toInputDate(data.data_as_of))
      })
      .catch(() => {
        if (!cancelled) setError('抖音运营数据暂不可用，请稍后重试。')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [range, endDate])

  const metrics = report?.metrics
  const metricItems = [
    ['支付金额', formatMoney(metrics?.user_payment_amount)],
    ['成交订单', formatNumber(metrics?.transaction_order_count)],
    ['支付用户', formatNumber(metrics?.transaction_user_count)],
    ['成交件数', formatNumber(metrics?.transaction_item_count)],
    ['商品曝光', formatNumber(metrics?.product_impression_count)],
    ['商品点击', formatNumber(metrics?.product_click_count)],
    ['曝光点击率', formatRate(metrics?.product_impression_click_rate)],
    ['点击转化率', formatRate(metrics?.product_click_conversion_rate)],
    ['退款金额', formatMoney(metrics?.refund_amount)],
    ['退款订单', formatNumber(metrics?.refund_order_count)],
  ]

  return (
    <section className="boss-page">
      <Link className="boss-back-link" to="/boss">← 返回平台运营数据</Link>
      <div className="boss-page-header boss-page-header--row">
        <div>
          <p className="boss-page-eyebrow">抖音</p>
          <h1>抖音运营数据</h1>
          <p>{report?.available ? `统计范围 ${formatDate(report.start_date)} 至 ${formatDate(report.data_as_of)}` : '选择截止日期与汇总范围查看数据'}</p>
        </div>
        <div className="boss-report-controls">
          <label>
            <span>截止日期</span>
            <input
              type="date"
              value={endDate}
              min={toInputDate(report?.available_start_date)}
              max={toInputDate(report?.available_end_date)}
              onChange={(event) => setEndDate(event.target.value)}
            />
          </label>
          <div className="boss-period-switcher" aria-label="数据范围">
            {RANGES.map((item) => (
              <button
                key={item.id}
                type="button"
                className={range === item.id ? 'active' : ''}
                onClick={() => setRange(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading && <div className="boss-loading">正在读取抖音运营数据…</div>}
      {error && <div className="alert-error">{error}</div>}
      {report && !loading && !report.available && (
        <div className="boss-empty-state boss-empty-state--report">
          <h2>暂无可展示数据</h2>
          <p>{report.empty_message || '所选日期范围没有可用数据。'}</p>
          {report.available_start_date && report.available_end_date && (
            <span>当前已导入日报范围：{formatDate(report.available_start_date)} 至 {formatDate(report.available_end_date)}</span>
          )}
        </div>
      )}
      {report?.available && !loading && (
        <>
          <div className="boss-freshness">来源：服务器 `douyin_reports` · 最近导入：{report.imported_at || '—'}</div>
          <div className="boss-metric-grid">
            {metricItems.map(([label, value]) => (
              <div key={label} className="boss-metric-card">
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>

          <div className="boss-report-grid">
            <section className="boss-report-card">
              <h2>商品成交榜</h2>
              {report.products.length === 0 ? <p className="muted">所选范围暂无商品成交数据。</p> : (
                <div className="boss-rank-list">
                  {report.products.map((item, index) => (
                    <div key={item.product_id} className="boss-rank-item">
                      <span className="boss-rank-number">{index + 1}</span>
                      <div><strong>{item.product_name || item.product_id}</strong><small>订单 {formatNumber(item.transaction_order_count)} · 点击转化 {formatRate(item.product_click_conversion_rate)}</small></div>
                      <b>{formatMoney(item.user_payment_amount)}</b>
                    </div>
                  ))}
                </div>
              )}
            </section>
            <section className="boss-report-card">
              <h2>视频成交榜</h2>
              {report.videos.length === 0 ? <p className="muted">所选范围没有同口径的视频数据。</p> : (
                <div className="boss-rank-list">
                  {report.videos.map((item, index) => (
                    <div key={`${item.video_id}-${index}`} className="boss-rank-item">
                      <span className="boss-rank-number">{index + 1}</span>
                      <div><strong>{item.video_title || item.video_id}</strong><small>播放 {formatNumber(item.view_count)} · 完播 {formatRate(item.completion_rate)}</small></div>
                      <b>{formatMoney(item.video_user_payment_amount)}</b>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        </>
      )}
    </section>
  )
}

export function BossPlatformPage() {
  const { platform: platformId } = useParams()
  const platform = isPlatformId(platformId)
    ? PLATFORMS.find((item) => item.id === platformId)
    : undefined

  if (platform?.id === 'douyin') return <DouyinBossView />

  if (platform) {
    return (
      <section className="boss-page">
        <Link className="boss-back-link" to="/boss">← 返回平台运营数据</Link>
        <div className="boss-empty-state">
          <p className="boss-page-eyebrow">{platform.name}</p>
          <h1>{platform.name} 运营数据</h1>
          <p>该平台运营数据暂未接入。</p>
          <span>数据源接入后将在此处展示。</span>
        </div>
      </section>
    )
  }

  return (
    <section className="boss-page">
      <div className="boss-page-header">
        <p className="boss-page-eyebrow">BOSS 视角</p>
        <h1>平台运营数据</h1>
        <p>选择一个平台查看运营数据接入状态。</p>
      </div>
      <div className="boss-platform-grid">
        {PLATFORMS.map((item) => (
          <Link key={item.id} className="boss-platform-card" to={`/boss/${item.id}`}>
            <span className="boss-platform-card__name">{item.name}</span>
            <span className="boss-platform-card__description">{item.description}</span>
            <span className={`boss-platform-card__status${item.connected ? ' boss-platform-card__status--ready' : ''}`}>{item.connected ? '已接入真实数据' : '暂未接入数据'}</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
