import { CheckIcon, WarningIcon, ErrorIcon, SpinnerIcon } from './icons'

export type StatusKind = 'success' | 'warning' | 'error' | 'pending' | 'neutral'

const STYLES: Record<StatusKind, { text: string; bg: string; border: string; icon: 'check' | 'warn' | 'error' | 'spin' | null }> = {
  success: {
    text: 'text-[var(--color-success)]',
    bg: 'bg-[var(--color-success-dim)]',
    border: 'border-[var(--color-success)]/30',
    icon: 'check',
  },
  warning: {
    text: 'text-[var(--color-warning)]',
    bg: 'bg-[var(--color-warning-dim)]',
    border: 'border-[var(--color-warning)]/30',
    icon: 'warn',
  },
  error: {
    text: 'text-[var(--color-error)]',
    bg: 'bg-[var(--color-error-dim)]',
    border: 'border-[var(--color-error)]/30',
    icon: 'error',
  },
  pending: {
    text: 'text-[var(--color-data)]',
    bg: 'bg-[var(--color-panel-raised)]',
    border: 'border-[var(--color-border-strong)]',
    icon: 'spin',
  },
  neutral: {
    text: 'text-[var(--color-text-secondary)]',
    bg: 'bg-[var(--color-panel-raised)]',
    border: 'border-[var(--color-border)]',
    icon: null,
  },
}

export function StatusBadge({
  kind,
  label,
  className = '',
}: {
  kind: StatusKind
  label: string
  className?: string
}) {
  const s = STYLES[kind]
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${s.border} ${s.bg} ${s.text} px-2.5 py-1 text-xs font-medium ${className}`}
      role="status"
    >
      {s.icon === 'check' && <CheckIcon width={12} height={12} />}
      {s.icon === 'warn' && <WarningIcon width={12} height={12} />}
      {s.icon === 'error' && <ErrorIcon width={12} height={12} />}
      {s.icon === 'spin' && <SpinnerIcon width={12} height={12} />}
      <span>{label}</span>
    </span>
  )
}
