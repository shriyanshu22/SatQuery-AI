import { SatelliteIcon } from '@/components/icons'

interface AnswerCardProps {
  answer: string
  task?: string
}

export function AnswerCard({ answer, task }: AnswerCardProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border-2 border-[var(--color-accent)]/50 bg-[var(--color-panel)] p-6 shadow-[0_4px_24px_rgba(0,0,0,0.3)]">
      {/* Subtle Background Glow */}
      <div
        className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-[var(--color-accent)]/10 blur-3xl"
        aria-hidden="true"
      />

      <div className="relative z-10 flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[var(--color-accent)]/40 bg-[var(--color-accent-dim)] text-[var(--color-accent)] shadow-sm">
          <SatelliteIcon width={20} height={20} />
        </div>

        <div className="min-w-0 flex-1 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-accent)]">
              Analytical Finding {task ? `· ${task.toUpperCase().replace('_', ' ')}` : ''}
            </span>
          </div>

          <h2 className="text-lg font-semibold leading-relaxed tracking-tight text-[var(--color-text-primary)] sm:text-xl">
            {answer}
          </h2>
        </div>
      </div>
    </div>
  )
}
