import type { TaskProgress } from '../types/task'

const STEP_LABELS = ['采集数据', 'LLM 分析', '生成报告']

interface Props {
  progress?: TaskProgress | null
}

export function TaskProgressBar({ progress }: Props) {
  const step = progress?.step ?? 0
  const percent = progress?.percent ?? 0

  return (
    <div className="card">
      <h2 style={{ fontSize: '1.1rem', marginBottom: 16 }}>任务执行中…</h2>
      <div style={{ marginBottom: 16 }}>
        <div style={{ height: 8, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${percent}%`,
              background: 'linear-gradient(90deg, #0d9488, #14b8a6)',
              transition: 'width 0.4s ease',
            }}
          />
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: 8 }}>
          {progress?.step_name ?? '准备中'} · {percent}%
        </p>
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {STEP_LABELS.map((label, i) => {
          const idx = i + 1
          const active = idx === step
          const done = idx < step
          return (
            <span
              key={label}
              style={{
                fontSize: '0.8rem',
                padding: '6px 12px',
                borderRadius: 8,
                background: done ? 'var(--accent-light)' : active ? '#ccfbf1' : '#f1f5f9',
                color: done || active ? '#0f766e' : 'var(--muted)',
                fontWeight: active ? 700 : 500,
                border: active ? '1px solid #5eead4' : '1px solid transparent',
              }}
            >
              {done ? '✓ ' : ''}{label}
            </span>
          )
        })}
      </div>
      <p style={{ marginTop: 16, fontSize: '0.88rem', color: 'var(--muted)' }}>
        正在执行工作流，请稍候…
      </p>
    </div>
  )
}
