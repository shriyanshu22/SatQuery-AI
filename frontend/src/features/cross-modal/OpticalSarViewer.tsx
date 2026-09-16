import type { CrossModalEvidence, AgreementStatus } from '@/types/evidence'
import { Panel, PanelHeader } from '@/components/Panel'
import { CheckIcon, WarningIcon, CompassIcon } from '@/components/icons'

interface OpticalSarViewerProps {
  evidence: CrossModalEvidence
}

function AgreementBadge({ status }: { status: AgreementStatus }) {
  if (status === 'agree') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-[var(--color-success)]/40 bg-[var(--color-success-dim)] px-4 py-2.5">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-success)] text-[#0f2229]">
          <CheckIcon width={14} height={14} />
        </div>
        <div>
          <p className="text-xs font-semibold text-[var(--color-success)]">
            Positive Corroboration · Sensors Agree
          </p>
          <p className="text-[11px] text-[var(--color-text-secondary)]">
            SAR microwave backscatter independently corroborates optical spectral findings.
          </p>
        </div>
      </div>
    )
  }

  if (status === 'disagree') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-[var(--color-warning)]/40 bg-[var(--color-warning-dim)] px-4 py-2.5">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-warning)] text-[#0f2229]">
          <WarningIcon width={14} height={14} />
        </div>
        <div>
          <p className="text-xs font-semibold text-[var(--color-warning)]">
            Conflicting Sensor Evidence · Disagreement
          </p>
          <p className="text-[11px] text-[var(--color-text-secondary)]">
            Optical surface reflectance diverges from SAR dielectric structural permanence.
          </p>
        </div>
      </div>
    )
  }

  // 'inconclusive' is a legitimate analytical outcome — never style as failure
  return (
    <div className="flex items-center gap-2 rounded-xl border border-[var(--color-border-strong)] bg-[var(--color-panel-raised)] px-4 py-2.5">
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-data)] text-[#0f2229]">
        <CompassIcon width={14} height={14} />
      </div>
      <div>
        <p className="text-xs font-semibold text-[var(--color-data-strong)]">
          Sensor Cross-Check Inconclusive
        </p>
        <p className="text-[11px] text-[var(--color-text-muted)]">
          Available radar signal is insufficient to decisively validate or refute optical interpretation.
        </p>
      </div>
    </div>
  )
}

export function OpticalSarViewer({ evidence }: OpticalSarViewerProps) {
  return (
    <Panel className="overflow-hidden">
      <PanelHeader
        title="Cross-Modal Verification"
        subtitle="Optical Imagery + Synthetic Aperture Radar (SAR) Analysis"
        action={
          evidence.confidence !== undefined ? (
            <span className="font-mono-tabular text-xs font-medium text-[var(--color-data-strong)]">
              {Math.round(evidence.confidence * 100)}% Cross-Sensor Confidence
            </span>
          ) : undefined
        }
      />

      <div className="space-y-4 p-4">
        {/* Top Status Banner */}
        <AgreementBadge status={evidence.agreement} />

        {/* Dual-Sensor Split Display */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Optical Modality Column */}
          <div className="space-y-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3.5">
            <div className="flex items-center justify-between">
              <span className="rounded bg-[var(--color-panel)] px-2 py-0.5 text-xs font-semibold text-[var(--color-text-primary)]">
                Optical Imagery
              </span>
              <span className="text-[11px] text-[var(--color-text-muted)]">
                Sentinel-2 MSI (Visible + NIR)
              </span>
            </div>

            <div className="relative aspect-[16/10] overflow-hidden rounded-lg border border-[var(--color-border)]">
              <img
                src={evidence.opticalImageUrl}
                alt="Optical remote sensing view"
                className="h-full w-full object-cover"
              />
            </div>

            <div className="space-y-1">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Optical Evidence
              </p>
              <p className="text-xs leading-relaxed text-[var(--color-text-secondary)]">
                {evidence.opticalEvidence}
              </p>
            </div>
          </div>

          {/* SAR Modality Column */}
          <div className="space-y-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3.5">
            <div className="flex items-center justify-between">
              <span className="rounded bg-[var(--color-panel)] px-2 py-0.5 text-xs font-semibold text-[var(--color-accent)]">
                Synthetic Aperture Radar (SAR)
              </span>
              <span className="text-[11px] text-[var(--color-text-muted)]">
                Sentinel-1 (C-Band Microwave)
              </span>
            </div>

            <div className="relative aspect-[16/10] overflow-hidden rounded-lg border border-[var(--color-border)]">
              <img
                src={evidence.sarImageUrl}
                alt="SAR microwave backscatter view"
                className="h-full w-full object-cover"
              />
            </div>

            <div className="space-y-1">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                SAR Evidence
              </p>
              <p className="text-xs leading-relaxed text-[var(--color-text-secondary)]">
                {evidence.sarEvidence}
              </p>
            </div>
          </div>
        </div>

        {/* Combined Interpretation Synthesis */}
        <div className="rounded-xl border border-[var(--color-border-strong)] bg-[var(--color-panel-raised)] p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-accent)]">
            Combined Analytical Interpretation
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-[var(--color-text-primary)]">
            {evidence.combinedInterpretation}
          </p>
        </div>
      </div>
    </Panel>
  )
}
