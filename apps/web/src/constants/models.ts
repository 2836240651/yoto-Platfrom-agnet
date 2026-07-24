/** Session model picker options (mirrors agent.constants.ALLOWED_MODEL_IDS). */

export type ModelId =
  | 'agnes-2.0-flash'
  | 'gpt-5.6-luna'
  | 'gpt-5.6-sol'
  | 'gpt-5.6-terra'

export const BLACKBOX_SKILLS = new Set(['temu-product-listing'])

export const MODEL_OPTIONS: { id: ModelId; label: string }[] = [
  { id: 'agnes-2.0-flash', label: 'Agnes' },
  { id: 'gpt-5.6-luna', label: 'GPT 5.6 Luna' },
  { id: 'gpt-5.6-sol', label: 'GPT 5.6 Sol' },
  { id: 'gpt-5.6-terra', label: 'GPT 5.6 Terra' },
]

export function isBlackboxSkill(skill: string | null | undefined): boolean {
  return Boolean(skill && BLACKBOX_SKILLS.has(skill))
}

export function modelLabel(id: ModelId | null | undefined): string {
  if (!id) return '自动'
  return MODEL_OPTIONS.find((o) => o.id === id)?.label ?? id
}

export interface ComposerNavigateState {
  topic?: string
  /** Only set when user explicitly pinned a model (scheme A). */
  model_id?: ModelId | null
}
