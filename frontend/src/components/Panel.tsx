import type { ReactNode } from 'react'

export function Panel({
  children,
  className = '',
  as: Component = 'div',
}: {
  children: ReactNode
  className?: string
  as?: 'div' | 'section'
  /** @deprecated kept for compatibility; panels are always softly rounded now */
  sharp?: boolean
}) {
  return (
    <Component
      className={`rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] shadow-[0_1px_2px_rgba(58,51,42,0.04),0_4px_16px_rgba(58,51,42,0.04)] ${className}`}
    >
      {children}
    </Component>
  )
}

export function PanelHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
}) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[var(--color-border)] px-4 py-3">
      <div>
        <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">{title}</h2>
        {subtitle && (
          <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  )
}
