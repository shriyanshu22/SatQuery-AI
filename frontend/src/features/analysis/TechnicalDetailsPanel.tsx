import { useState } from 'react'
import type { TechnicalDetails, ExecutionStep } from '@/types/analysis'
import { ChevronDownIcon } from '@/components/icons'

interface TechnicalDetailsPanelProps {
  details?: TechnicalDetails
  executionTrace?: ExecutionStep[]
}

export function TechnicalDetailsPanel({
  details,
  executionTrace = [],
}: TechnicalDetailsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!details && executionTrace.length === 0) return null

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)]">
      <button
        type="button"
        onClick={() => setIsExpanded((v) => !v)}
        className="flex w-full items-center justify-between p-3.5 text-left transition-colors hover:bg-[var(--color-panel-raised)]"
        aria-expanded={isExpanded}
      >
        <span className="text-xs font-semibold text-[var(--color-text-secondary)]">
          Technical Details & Model Provenance
        </span>
        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
          <span>{isExpanded ? 'Hide' : 'Inspect'}</span>
          <ChevronDownIcon
            width={12}
            height={12}
            className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          />
        </div>
      </button>

      {isExpanded && (
        <div className="space-y-3.5 border-t border-[var(--color-border)] p-4 text-xs">
          {details && (
            <dl className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              {details.modelUsed && (
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-2.5">
                  <dt className="text-[10px] uppercase text-[var(--color-text-muted)]">Model / Pipeline</dt>
                  <dd className="mt-0.5 font-medium text-[var(--color-text-primary)]">{details.modelUsed}</dd>
                </div>
              )}
              {details.modelVersion && (
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-2.5">
                  <dt className="text-[10px] uppercase text-[var(--color-text-muted)]">Model Version</dt>
                  <dd className="font-mono-tabular mt-0.5 font-medium text-[var(--color-text-primary)]">
                    {details.modelVersion}
                  </dd>
                </div>
              )}
              {details.processingTimeMs !== undefined && (
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-2.5">
                  <dt className="text-[10px] uppercase text-[var(--color-text-muted)]">Inference Latency</dt>
                  <dd className="font-mono-tabular mt-0.5 font-medium text-[var(--color-accent)]">
                    {details.processingTimeMs} ms
                  </dd>
                </div>
              )}
              {details.sensor && (
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-2.5">
                  <dt className="text-[10px] uppercase text-[var(--color-text-muted)]">Sensor Platform</dt>
                  <dd className="mt-0.5 font-medium text-[var(--color-text-primary)]">{details.sensor}</dd>
                </div>
              )}
              {details.crs && (
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-2.5">
                  <dt className="text-[10px] uppercase text-[var(--color-text-muted)]">CRS / Projection</dt>
                  <dd className="font-mono-tabular mt-0.5 font-medium text-[var(--color-data-strong)]">
                    {details.crs}
                  </dd>
                </div>
              )}
              {details.confidenceSource && (
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-2.5">
                  <dt className="text-[10px] uppercase text-[var(--color-text-muted)]">Calibration Method</dt>
                  <dd className="mt-0.5 font-medium text-[var(--color-text-secondary)]">
                    {details.confidenceSource}
                  </dd>
                </div>
              )}
            </dl>
          )}

          {/* Observable Execution Step Log */}
          {executionTrace.length > 0 && (
            <div className="space-y-1.5 pt-2">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Observable Execution Sequence
              </p>
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-2.5 font-mono text-[11px]">
                {executionTrace.map((event, idx) => (
                  <div key={event.id} className="flex items-center gap-2 py-0.5">
                    <span className="text-[var(--color-text-muted)]">[{idx + 1}]</span>
                    <span className="text-[var(--color-success)]">✓</span>
                    <span className="text-[var(--color-text-secondary)]">{event.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
