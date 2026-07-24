import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MODEL_OPTIONS,
  type ModelId,
  modelLabel,
} from '../constants/models'

interface Props {
  /** When true, picker is disabled (black-box skill page). */
  blackbox?: boolean
  devMode?: boolean
}

type AttachMenu = 'closed' | 'open'

/**
 * Scheme A: no interaction → model_id null (catalog).
 * Choosing any model (including Agnes) pins that id into navigate state.
 * "+" opens Skill / Temu shortcuts (no empty attach).
 */
export function WorkspaceComposer({ blackbox = false, devMode = false }: Props) {
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState('')
  const [pinned, setPinned] = useState(false)
  const [modelId, setModelId] = useState<ModelId | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [attachOpen, setAttachOpen] = useState<AttachMenu>('closed')
  const menuRef = useRef<HTMLDivElement>(null)
  const attachRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      const t = e.target as Node
      if (!menuRef.current?.contains(t)) setMenuOpen(false)
      if (!attachRef.current?.contains(t)) setAttachOpen('closed')
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [])

  function goNewDialog() {
    navigate(devMode ? '/dev' : '/')
    setPrompt('')
    setPinned(false)
    setModelId(null)
    setAttachOpen('closed')
  }

  function handleSubmit() {
    const text = prompt.trim()
    if (!text || blackbox) return
    const base = devMode ? '/dev/tasks/new' : '/tasks/new'
    navigate(base, {
      state: {
        topic: text,
        model_id: pinned ? modelId : null,
      },
    })
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  function pickAuto() {
    setPinned(false)
    setModelId(null)
    setMenuOpen(false)
  }

  function pickModel(id: ModelId) {
    setPinned(true)
    setModelId(id)
    setMenuOpen(false)
  }

  function openTemu() {
    setAttachOpen('closed')
    navigate(devMode ? '/dev/tasks/temu' : '/tasks/temu')
  }

  function openDouyinSkill() {
    setAttachOpen('closed')
    navigate(devMode ? '/dev/tasks/new' : '/tasks/new', {
      state: {
        topic: prompt.trim() || undefined,
        model_id: pinned ? modelId : null,
      },
    })
  }

  const chipLabel = blackbox
    ? '本任务不走对话模型'
    : pinned
      ? `${modelLabel(modelId)} ▾`
      : '自动 ▾'

  return (
    <div>
      <div className="composer">
        <textarea
          className="composer-input"
          placeholder="随心输入，或点 + 选择 Skill / Temu 上架"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
        />
        <div className="composer-toolbar">
          <div className="composer-toolbar-left">
            <div className="composer-attach" ref={attachRef}>
              <button
                type="button"
                className="composer-icon-btn"
                title="添加：Skill 或 Temu 上架"
                aria-label="添加 Skill 或 Temu 上架"
                aria-expanded={attachOpen === 'open'}
                onClick={() =>
                  setAttachOpen((s) => (s === 'open' ? 'closed' : 'open'))
                }
              >
                +
              </button>
              {attachOpen === 'open' && (
                <ul className="composer-model-menu composer-attach-menu" role="menu">
                  <li>
                    <button type="button" role="menuitem" onClick={openDouyinSkill}>
                      Skill · 抖音词分析
                    </button>
                  </li>
                  <li>
                    <button type="button" role="menuitem" onClick={openTemu}>
                      打开 Temu 上架
                    </button>
                  </li>
                  <li>
                    <button type="button" role="menuitem" onClick={goNewDialog}>
                      新开对话
                    </button>
                  </li>
                </ul>
              )}
            </div>
            <button
              type="button"
              className="composer-chip"
              title="新开对话"
              onClick={goNewDialog}
            >
              新对话
            </button>
          </div>
          <div className="composer-toolbar-right">
            <div className="composer-model" ref={menuRef}>
              <button
                type="button"
                className={`composer-chip composer-chip--model${blackbox ? ' composer-chip--disabled' : ''}`}
                disabled={blackbox}
                aria-haspopup="listbox"
                aria-expanded={menuOpen}
                title={blackbox ? '本任务不走对话模型' : '选择会话模型（未选=按任务自动）'}
                onClick={() => !blackbox && setMenuOpen((o) => !o)}
              >
                {chipLabel}
              </button>
              {menuOpen && !blackbox && (
                <ul className="composer-model-menu" role="listbox">
                  <li>
                    <button type="button" className={!pinned ? 'is-active' : ''} onClick={pickAuto}>
                      自动（按任务）
                    </button>
                  </li>
                  {MODEL_OPTIONS.map((opt) => (
                    <li key={opt.id}>
                      <button
                        type="button"
                        className={pinned && modelId === opt.id ? 'is-active' : ''}
                        onClick={() => pickModel(opt.id)}
                      >
                        {opt.label}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <button
              type="button"
              className="composer-send"
              disabled={blackbox || !prompt.trim()}
              onClick={handleSubmit}
              aria-label="发送"
            >
              ↑
            </button>
          </div>
        </div>
      </div>

      {blackbox && (
        <p className="composer-model-hint">本任务不走对话模型（纯工具执行）</p>
      )}

      <div className="context-row">
        <span className="context-chip">⌂ workspace</span>
        <button
          type="button"
          className="context-chip"
          style={{ cursor: 'pointer', border: '1px solid var(--border-strong)', background: '#fff' }}
          onClick={() => navigate(devMode ? '/dev/tools' : '/tools')}
        >
          工具状态
        </button>
      </div>
    </div>
  )
}
