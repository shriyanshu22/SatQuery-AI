import { useState } from 'react'
import type { BoundingBoxEvidence } from '@/types/evidence'
import { BoundingBoxOverlay } from './BoundingBoxOverlay'
import { Panel, PanelHeader } from '@/components/Panel'
import { StatusBadge } from '@/components/StatusBadge'
import { ScanIcon } from '@/components/icons'

interface GroundingViewerProps {
  imageUrl: string
  boxes: BoundingBoxEvidence[]
}

export function GroundingViewer({ imageUrl, boxes }: GroundingViewerProps) {
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  const categories = Array.from(new Set(boxes.map((b) => b.category)))
  const filteredBoxes = activeCategory
    ? boxes.filter((b) => b.category === activeCategory)
    : boxes

  const selectedBox = boxes.find((b) => b.id === selectedBoxId)

  return (
    <Panel className="overflow-hidden">
      <PanelHeader
        title="Spatial Grounding & Detection"
        subtitle="Backend-localized bounding coordinates mapped to raster footprint"
        action={
          <StatusBadge
            kind="success"
            label={`${boxes.length} objects detected`}
          />
        }
      />

      <div className="space-y-4 p-4">
        {/* Category Filter Chips */}
        {categories.length > 1 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={() => setActiveCategory(null)}
              className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                activeCategory === null
                  ? 'bg-[var(--color-accent)] text-[#241207]'
                  : 'border border-[var(--color-border)] bg-[var(--color-panel-raised)] text-[var(--color-text-secondary)] hover:border-[var(--color-accent)]/40'
              }`}
            >
              All Categories ({boxes.length})
            </button>
            {categories.map((cat) => {
              const count = boxes.filter((b) => b.category === cat).length
              const isActive = activeCategory === cat
              return (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setActiveCategory(isActive ? null : cat)}
                  className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-[var(--color-accent)] text-[#241207]'
                      : 'border border-[var(--color-border)] bg-[var(--color-panel-raised)] text-[var(--color-text-secondary)] hover:border-[var(--color-accent)]/40'
                  }`}
                >
                  {cat} ({count})
                </button>
              )
            })}
          </div>
        )}

        {/* Overlay Canvas */}
        <div className="pt-2">
          <BoundingBoxOverlay
            imageUrl={imageUrl}
            boxes={filteredBoxes}
            selectedBoxId={selectedBoxId}
            onSelectBox={setSelectedBoxId}
          />
        </div>

        {/* Selected Box Inspector */}
        {selectedBox && (
          <div className="flex items-start gap-3 rounded-lg border border-[var(--color-accent)]/40 bg-[var(--color-accent-dim)]/40 p-3">
            <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-[var(--color-accent)]/50 bg-[var(--color-panel)] text-[var(--color-accent)]">
              <ScanIcon width={14} height={14} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <p className="text-xs font-semibold text-[var(--color-text-primary)]">
                  {selectedBox.label}
                </p>
                {selectedBox.confidence !== undefined && (
                  <span className="font-mono-tabular text-xs font-medium text-[var(--color-data-strong)]">
                    {Math.round(selectedBox.confidence * 100)}% Confidence
                  </span>
                )}
              </div>
              <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">
                Category: {selectedBox.category} · Coordinates [ymin, xmin, ymax, xmax]: [{selectedBox.box.map((n) => n.toFixed(2)).join(', ')}]
              </p>
            </div>
          </div>
        )}
      </div>
    </Panel>
  )
}
