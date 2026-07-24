import type { DouyinTaskReport } from '../types/task'

export function StatGrid({ summary }: { summary: DouyinTaskReport['summary'] }) {
  const items = [
    { num: summary.keyword_count, lbl: '候选项总数' },
    { num: summary.video_sample_count, lbl: '内容样本' },
    { num: summary.product_sku_count, lbl: '机会样本' },
    { num: summary.p0_count, lbl: '高优先级' },
  ]

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: 12,
        marginBottom: 24,
      }}
    >
      {items.map((item) => (
        <div key={item.lbl} className="card" style={{ textAlign: 'center', padding: 16 }}>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent)' }}>{item.num}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: 4 }}>{item.lbl}</div>
        </div>
      ))}
    </div>
  )
}
