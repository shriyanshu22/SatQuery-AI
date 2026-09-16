import { useState, useRef } from 'react'
import type { ChangeMapEvidence } from '@/types/evidence'
import { Panel, PanelHeader } from '@/components/Panel'
import { StatusBadge } from '@/components/StatusBadge'

interface BeforeAfterViewerProps {
  evidence: ChangeMapEvidence
}

export function BeforeAfterViewer({ evidence }: BeforeAfterViewerProps) {
  const [viewMode, setViewMode] = useState<'slider' | 'side-by-side' | 'change-map'>('slider')
  const [sliderPosition, setSliderPosition] = useState(50)
  const containerRef = useRef<HTMLDivElement>(null)

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
    const pct = Math.round((x / rect.width) * 100)
    setSliderPosition(pct)
  }

  return (
    <Panel className="overflow-hidden">
      <PanelHeader
        title="Bi-Temporal Change Analysis"
        subtitle={evidence.label || 'Multi-epoch remote sensing comparison'}
        action={
          <div className="flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-1">
            <button
              type="button"
              onClick={() => setViewMode('slider')}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                viewMode === 'slider'
                  ? 'bg-[var(--color-accent)] text-[#241207]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
              }`}
            >
              Split Slider
            </button>
            <button
              type="button"
              onClick={() => setViewMode('side-by-side')}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                viewMode === 'side-by-side'
                  ? 'bg-[var(--color-accent)] text-[#241207]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
              }`}
            >
              Side by Side
            </button>
            <button
              type="button"
              onClick={() => setViewMode('change-map')}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                viewMode === 'change-map'
                  ? 'bg-[var(--color-accent)] text-[#241207]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
              }`}
            >
              Change Map
            </button>
          </div>
        }
      />

      <div className="space-y-4 p-4">
        {/* Visual Inspection Canvas */}
        {viewMode === 'slider' && (
          <div
            ref={containerRef}
            onMouseMove={handleMouseMove}
            className="relative aspect-[16/9] w-full cursor-ew-resize overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] select-none"
          >
            {/* After Image (Full width background) */}
            <img
              src={evidence.afterImageUrl}
              alt="Post-epoch satellite scene"
              className="absolute inset-0 h-full w-full object-cover"
            />
            <div className="absolute right-3 top-3 rounded-full bg-black/60 px-2.5 py-1 text-[11px] font-medium text-white backdrop-blur">
              After (Post-Epoch)
            </div>

            {/* Before Image (Clipped overlay) */}
            <div
              className="absolute inset-y-0 left-0 overflow-hidden"
              style={{ width: `${sliderPosition}%` }}
            >
              <img
                src={evidence.beforeImageUrl}
                alt="Pre-epoch satellite scene"
                className="absolute inset-y-0 left-0 h-full max-w-none object-cover"
                style={{ width: containerRef.current?.offsetWidth ?? '100%' }}
              />
              <div className="absolute left-3 top-3 rounded-full bg-black/60 px-2.5 py-1 text-[11px] font-medium text-white backdrop-blur">
                Before (Pre-Epoch)
              </div>
            </div>

            {/* Split Divider Line with Handle */}
            <div
              className="absolute inset-y-0 w-0.5 bg-[var(--color-accent)] shadow-[0_0_10px_rgba(224,138,91,0.8)]"
              style={{ left: `${sliderPosition}%` }}
            >
              <div className="absolute top-1/2 -ml-3 -mt-3 flex h-6 w-6 items-center justify-center rounded-full border border-[var(--color-accent)] bg-[var(--color-panel)] text-[10px] font-bold text-[var(--color-accent)] shadow-md">
                ↔
              </div>
            </div>
          </div>
        )}

        {viewMode === 'side-by-side' && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <div className="relative aspect-[16/10] overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)]">
                <img
                  src={evidence.beforeImageUrl}
                  alt="Pre-epoch satellite scene"
                  className="h-full w-full object-cover"
                />
                <div className="absolute left-2.5 top-2.5 rounded bg-black/70 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur">
                  Before (Pre-Epoch)
                </div>
              </div>
            </div>
            <div className="space-y-1.5">
              <div className="relative aspect-[16/10] overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)]">
                <img
                  src={evidence.afterImageUrl}
                  alt="Post-epoch satellite scene"
                  className="h-full w-full object-cover"
                />
                <div className="absolute left-2.5 top-2.5 rounded bg-black/70 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur">
                  After (Post-Epoch)
                </div>
              </div>
            </div>
          </div>
        )}

        {viewMode === 'change-map' && (
          <div className="relative aspect-[16/9] w-full overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)]">
            <img
              src={evidence.changeMapUrl}
              alt="Backend-generated change heatmap overlay"
              className="h-full w-full object-cover"
            />
            <div className="absolute left-3 top-3 rounded-full bg-black/70 px-3 py-1 text-xs font-medium text-[var(--color-accent)] backdrop-blur">
              Calculated Change Mask (Altered Pixels)
            </div>
          </div>
        )}

        {/* Change Metrics Summary Badges */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {evidence.changedAreaHectares !== undefined && (
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3">
              <p className="text-[11px] text-[var(--color-text-muted)]">Changed Area</p>
              <p className="font-mono-tabular mt-1 text-lg font-semibold text-[var(--color-accent)]">
                +{evidence.changedAreaHectares} ha
              </p>
            </div>
          )}
          {evidence.changedAreaKm2 !== undefined && (
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3">
              <p className="text-[11px] text-[var(--color-text-muted)]">Area ($km^2$)</p>
              <p className="font-mono-tabular mt-1 text-lg font-semibold text-[var(--color-data-strong)]">
                {evidence.changedAreaKm2} km²
              </p>
            </div>
          )}
          {evidence.changeType && (
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3">
              <p className="text-[11px] text-[var(--color-text-muted)]">Classification</p>
              <p className="mt-1 truncate text-xs font-semibold text-[var(--color-text-primary)]">
                {evidence.changeType}
              </p>
            </div>
          )}
          {evidence.confidence !== undefined && (
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3">
              <p className="text-[11px] text-[var(--color-text-muted)]">Detection Certainty</p>
              <div className="mt-1 flex items-center gap-1.5">
                <StatusBadge
                  kind="success"
                  label={`${Math.round(evidence.confidence * 100)}%`}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </Panel>
  )
}
