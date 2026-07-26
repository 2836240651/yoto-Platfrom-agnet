import type { KeywordCard as KeywordCardType } from '../types/task'

const priorityStyle: Record<string, { bg: string; color: string }> = {
  P0: { bg: 'var(--p0-bg)', color: 'var(--p0)' },
  P1: { bg: 'var(--p1-bg)', color: 'var(--p1)' },
  P2: { bg: 'var(--p2-bg)', color: 'var(--p2)' },
}

const trendLabel = { up: '↑ 上升', flat: '→ 平稳', down: '↓ 下降' }
const trendStyle = {
  up: { bg: '#dcfce7', color: 'var(--up)' },
  flat: { bg: '#f1f5f9', color: 'var(--flat)' },
  down: { bg: '#fee2e2', color: 'var(--down)' },
}

function isMutedHeat(value: string): boolean {
  return value === '暂无指数' || value === '—' || value === '-'
}

export function KeywordCard({
  card,
  side,
}: {
  card: KeywordCardType
  side?: 'video' | 'product'
}) {
  const p = priorityStyle[card.priority]
  const t = trendStyle[card.trend]
  const sideLabel = side === 'product' ? '商品' : side === 'video' ? '视频' : null
  const sideColor = side === 'product' ? '#b45309' : '#0369a1'
  const sideBg = side === 'product' ? '#fff7ed' : '#e0f2fe'

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <h3 style={{ fontSize: '1.2rem', flex: 1, minWidth: 160 }}>{card.keyword}</h3>
        {sideLabel ? (
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '4px 10px',
              borderRadius: 6,
              background: sideBg,
              color: sideColor,
            }}
          >
            {sideLabel}
          </span>
        ) : null}
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            padding: '4px 10px',
            borderRadius: 6,
            background: p.bg,
            color: p.color,
          }}
        >
          {card.priority}
        </span>
        <span
          style={{
            fontSize: '0.85rem',
            fontWeight: 600,
            padding: '3px 8px',
            borderRadius: 6,
            background: t.bg,
            color: t.color,
          }}
        >
          {trendLabel[card.trend]}
        </span>
      </div>

      <div
        style={{
          background: '#f8fafc',
          borderLeft: '4px solid var(--accent)',
          padding: '10px 14px',
          marginBottom: 14,
          fontSize: '0.92rem',
          lineHeight: 1.55,
          whiteSpace: 'pre-wrap',
        }}
      >
        {card.reason}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
          gap: 10,
          marginBottom: 14,
        }}
      >
        {card.metrics.map((m) => {
          const muted = isMutedHeat(m.value)
          return (
            <div
              key={m.label}
              style={{ textAlign: 'center', padding: '10px 6px', background: '#f8fafc', borderRadius: 8 }}
            >
              <div
                style={{
                  fontSize: muted ? '0.95rem' : '1.15rem',
                  fontWeight: muted ? 600 : 700,
                  color: muted ? 'var(--muted)' : 'var(--text)',
                }}
              >
                {m.value}
              </div>
              <div style={{ fontSize: '0.68rem', color: 'var(--muted)', marginTop: 2 }}>{m.label}</div>
            </div>
          )
        })}
      </div>

      <ul style={{ fontSize: '0.88rem', color: 'var(--muted)', margin: '12px 0', paddingLeft: 18 }}>
        {card.evidence.map((e) => (
          <li key={e}>{e}</li>
        ))}
      </ul>

      {card.queried_term ? (
        <div style={{ color: 'var(--muted)', fontSize: '0.78rem', marginBottom: 12 }}>
          查询词：{card.queried_term}
          {card.query_level === 'explicit_expansion' ? '（知识库窄扩词）' : ''}
          {card.query_dimension ? ` · 维度：${card.query_dimension}` : ''}
        </div>
      ) : null}

      <div style={{ background: '#f0fdfa', borderRadius: 8, padding: '12px 14px', fontSize: '0.9rem', lineHeight: 1.5 }}>
        <strong style={{ color: '#0f766e' }}>行动建议：</strong> {card.action}
      </div>
    </div>
  )
}
