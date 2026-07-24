import { sourceBadgeLabel, type TemuListingReport } from '../types/task'

export function TemuListingReportView({ report }: { report: TemuListingReport }) {
  const ok = report.ok && report.status === 'success'
  const source = report.data_source?.source
  const rows: { label: string; value: string }[] = [
    { label: '状态', value: report.status },
    { label: '说明', value: report.message || '—' },
    { label: '店铺', value: report.shop_id || '—' },
    { label: 'Agent', value: report.agent_id || '—' },
    { label: 'Commander 任务', value: report.task_id || '—' },
  ]

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem', color: ok ? 'var(--p0)' : 'var(--down)' }}>
          {ok ? 'Temu 上架成功' : 'Temu 上架未成功'}
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
        本任务不走对话模型（黑盒 MCP / Commander）
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
