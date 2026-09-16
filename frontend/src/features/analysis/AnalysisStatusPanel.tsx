import { Panel, PanelHeader } from '@/components/Panel'
import { EmptyState } from '@/components/EmptyState'
import { ErrorPanel } from '@/components/ErrorPanel'
import { LayersIcon, CheckIcon, SpinnerIcon } from '@/components/icons'
import type { AnalysisResult } from '@/types/analysis'

function TraceStep({ step }: { step: AnalysisResult['executionTrace'][number] }) {
  return (
    <li className="flex items-start gap-2.5">
      <div
        className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
          step.status === 'done'
            ? 'border-[var(--color-success)] bg-[var(--color-success)]/15 text-[var(--color-success)]'
            : step.status === 'active'
              ? 'border-[var(--color-accent)] text-[var(--color-accent)]'
              : step.status === 'failed'
                ? 'border-[var(--color-error)] text-[var(--color-error)]'
                : 'border-[var(--color-border-strong)] text-transparent'
        }`}
      >
        {step.status === 'done' && <CheckIcon width={9} height={9} />}
        {step.status === 'active' && <SpinnerIcon width={9} height={9} />}
      </div>
      <div className="min-w-0">
        <p
          className={`text-xs ${
            step.status === 'pending'
              ? 'text-[var(--color-text-muted)]'
              : 'text-[var(--color-text-secondary)]'
          }`}
        >
          {step.label}
        </p>
      </div>
    </li>
  )
}

export function AnalysisStatusPanel({
  result,
  isAnalyzing,
  error,
}: {
  result: AnalysisResult | null
  isAnalyzing: boolean
  error: string | null
}) {
  return (
    <Panel>
      <PanelHeader title="Analysis status" subtitle="Execution trace" />
      <div className="p-4">
        {error && <ErrorPanel description={error} />}

        {!error && !result && !isAnalyzing && (
          <EmptyState
            icon={<LayersIcon width={18} height={18} />}
            title="No analysis yet"
            description="Upload imagery and ask a question to see the execution trace here."
          />
        )}

        {!error && result && (
          <ul className="space-y-3">
            {result.executionTrace.map((step) => (
              <TraceStep key={step.id} step={step} />
            ))}
          </ul>
        )}
      </div>
    </Panel>
  )
}
