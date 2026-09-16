import { SpinnerIcon } from './icons'

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center"
      role="status"
      aria-live="polite"
    >
      <SpinnerIcon width={22} height={22} className="text-[var(--color-accent)]" />
      <p className="text-sm text-[var(--color-text-secondary)]">{label}</p>
    </div>
  )
}
