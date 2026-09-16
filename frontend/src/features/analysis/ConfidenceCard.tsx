import type { Confidence } from '@/types/api'
import { StatusBadge } from '@/components/StatusBadge'

interface ConfidenceCardProps {
  confidence?: Confidence
}

const METHOD_LABELS: Record<string, string> = {
  calibrated: 'Calibrated Confidence',
  'model-derived': 'Model-Derived Confidence',
  'evidence-derived': 'Evidence-Derived Confidence',
}

export function ConfidenceCard({ confidence }: ConfidenceCardProps) {
  if (!confidence || confidence.status === 'unavailable' || confidence.score == null) {
    return (
      <div className="flex flex-col gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[var(--color-text-secondary)]">
              Confidence Assessment
            </span>
            <StatusBadge kind="neutral" label="Confidence unavailable" />
          </div>
          {confidence?.explanation && (
            <p className="mt-1 text-xs text-[var(--color-text-muted)]">
              {confidence.explanation}
            </p>
          )}
        </div>
        <p className="text-[11px] text-[var(--color-text-muted)]">
          No statistical calibration provided by model pipeline.
        </p>
      </div>
    )
  }

  const scorePct = Math.round(
    confidence.score <= 1.0 ? confidence.score * 100 : confidence.score,
  )
  const methodLabel = confidence.method ? METHOD_LABELS[confidence.method] ?? confidence.method : 'Standard'

  return (
    <div className="rounded-xl border border-[var(--color-border-strong)] bg-[var(--color-panel-raised)] p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              {methodLabel}
            </span>
            <StatusBadge
              kind={scorePct >= 80 ? 'success' : scorePct >= 60 ? 'warning' : 'neutral'}
              label={scorePct >= 80 ? 'High Certainty' : 'Moderate Certainty'}
            />
          </div>
          {confidence.explanation && (
            <p className="text-xs leading-relaxed text-[var(--color-text-secondary)]">
              {confidence.explanation}
            </p>
          )}
        </div>

        {/* Big Score Indicator */}
        <div className="flex shrink-0 items-baseline gap-1 self-start sm:self-auto">
          <span className="font-mono-tabular text-3xl font-bold tracking-tight text-[var(--color-data-strong)]">
            {scorePct}%
          </span>
          <span className="text-xs text-[var(--color-text-muted)]">Score</span>
        </div>
      </div>
    </div>
  )
}
