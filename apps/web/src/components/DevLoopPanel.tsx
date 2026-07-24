import type { TaskDetail } from '../types/task'

export function DevLoopPanel({ task }: { task: TaskDetail }) {
  const debug = task.debug
  const events = debug?.events ?? []
  const plan = debug?.plan ?? []

  return (
    <div className="card" style={{ marginTop: 16 }}>
      <h2 style={{ fontSize: '1.05rem', marginBottom: 12, fontWeight: 600 }}>Loop 监督面板</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>当前动作</div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{debug?.current_action ?? '—'}</div>
        </div>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>micro_route</div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{debug?.micro_route ?? '—'}</div>
        </div>

        <div>
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>failure_class</div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{debug?.failure_class ?? '—'}</div>
        </div>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>quality_score</div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
            {debug?.quality_score !== null && debug?.quality_score !== undefined ? debug.quality_score : '—'}
          </div>
        </div>

        <div>
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>last_tool_error</div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
            {debug?.last_tool_error ?? '—'}
          </div>
        </div>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>global_loop_used</div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{debug?.global_loop_used ?? '—'}</div>
        </div>
      </div>

      {plan.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ color: 'var(--muted)', fontSize: '0.85rem', marginBottom: 8 }}>Macro 步骤状态</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {plan.map((s, idx) => (
              <span
                key={`${s.id ?? s.name ?? idx}`}
                style={{
                  fontSize: '0.8rem',
                  padding: '6px 10px',
                  borderRadius: 8,
                  background: s.status === 'done' ? 'var(--accent-light)' : '#f1f5f9',
                  border: '1px solid transparent',
                }}
              >
                {idx + 1}. {s.label ?? s.name ?? '—'} · {s.status ?? 'pending'}
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <div style={{ color: 'var(--muted)', fontSize: '0.85rem', marginBottom: 8 }}>
          事件流（最近 {events.length} 条）
        </div>
        <div
          style={{
            maxHeight: 320,
            overflowY: 'auto',
            border: '1px solid var(--border)',
            borderRadius: 12,
            padding: 12,
            background: '#0b1220',
            color: '#e5e7eb',
            fontFamily: 'monospace',
            fontSize: 12,
          }}
        >
          {events.length === 0 ? (
            <div style={{ color: 'rgba(229,231,235,0.7)' }}>暂无事件</div>
          ) : (
            events.map((e, idx) => (
              <div
                key={`${e.ts ?? idx}-${e.node ?? 'evt'}-${idx}`}
                style={{
                  padding: '6px 0',
                  borderBottom: idx === events.length - 1 ? 'none' : '1px solid rgba(229,231,235,0.08)',
                }}
              >
                <div style={{ color: 'rgba(229,231,235,0.7)' }}>
                  {e.ts ?? '—'} [{e.node ?? '—'}]
                </div>
                <div style={{ whiteSpace: 'pre-wrap' }}>{e.message ?? '—'}</div>
                {(e.attempt ?? null) !== null && e.attempt !== undefined && (
                  <div style={{ color: 'rgba(229,231,235,0.7)' }}>
                    attempt={e.attempt}
                    {e.quality !== undefined && e.quality !== null ? ` · quality=${e.quality}` : ''}
                    {e.failure_class ? ` · failure_class=${e.failure_class}` : ''}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

