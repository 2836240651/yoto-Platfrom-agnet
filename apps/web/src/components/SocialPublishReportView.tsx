import { sourceBadgeLabel, type SocialPublishReport } from '../types/task'

const PLATFORM_LABEL: Record<number, string> = {
  1: '小红书',
  2: '视频号',
  3: '抖音',
  4: '快手',
  5: 'TikTok',
}

export function SocialPublishReportView({ report }: { report: SocialPublishReport }) {
  const ok = report.ok && report.status === 'success'
  const source = report.data_source?.source
  const platform =
    report.platform_type != null
      ? PLATFORM_LABEL[report.platform_type] || String(report.platform_type)
      : '—'
  const rows: { label: string; value: string }[] = [
    { label: '状态', value: report.status },
    { label: '说明', value: report.message || '—' },
    { label: '平台', value: platform },
    { label: '标题', value: report.title || '—' },
    { label: '账号', value: (report.account_list || []).join(', ') || '—' },
    { label: '任务 ID', value: report.job_id || '—' },
    { label: '运行时', value: report.publish_runtime || '—' },
  ]

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem', color: ok ? 'var(--p0)' : 'var(--down)' }}>
          {ok ? '社媒发布成功' : '社媒发布未成功'}
        </h3>
        {source && (
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '3px 8px',
              borderRadius: 6,
              border: '1px solid var(--border-strong)',
              color: 'var(--muted)',
            }}
          >
            {sourceBadgeLabel(source)}
          </span>
        )}
      </div>
      <p style={{ margin: '0 0 16px', color: 'var(--muted)', fontSize: '0.88rem' }}>
        本任务不走对话模型（黑盒 MCP / automedia）
      </p>
      <dl style={{ margin: 0, display: 'grid', gap: 10 }}>
        {rows.map((r) => (
          <div key={r.label} style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
            <dt style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>{r.label}</dt>
            <dd style={{ margin: 0, fontSize: '0.92rem', wordBreak: 'break-all' }}>{r.value}</dd>
          </div>
        ))}
      </dl>
      {report.data_source?.mcp_error && (
        <p style={{ marginTop: 14, color: 'var(--down)', fontSize: '0.88rem' }}>
          MCP：{report.data_source.mcp_error}
        </p>
      )}
    </div>
  )
}
