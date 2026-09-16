import type { ReactNode } from 'react'
import { ErrorIcon } from './icons'

export function ErrorPanel({
  title = 'Something went wrong',
  description,
  action,
}: {
  title?: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div
      className="flex items-start gap-3 rounded-xl border border-[var(--color-error)]/30 bg-[var(--color-error-dim)] px-4 py-3"
      role="alert"
    >
      <ErrorIcon
        width={16}
        height={16}
        className="mt-0.5 shrink-0 text-[var(--color-error)]"
      />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-[var(--color-text-primary)]">{title}</p>
        {description && (
          <p className="mt-1 text-xs text-[var(--color-text-secondary)]">{description}</p>
        )}
        {action && <div className="mt-2">{action}</div>}
      </div>
    </div>
  )
}
