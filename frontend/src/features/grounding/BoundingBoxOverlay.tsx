import { useState } from 'react'
import type { BoundingBoxEvidence } from '@/types/evidence'

interface BoundingBoxOverlayProps {
  imageUrl: string
  altText?: string
  boxes: BoundingBoxEvidence[]
  selectedBoxId?: string | null
  onSelectBox?: (boxId: string | null) => void
}

export function BoundingBoxOverlay({
  imageUrl,
  altText = 'Satellite image with spatial detections',
  boxes,
  selectedBoxId,
  onSelectBox,
}: BoundingBoxOverlayProps) {
  const [hoveredBoxId, setHoveredBoxId] = useState<string | null>(null)

  return (
    <div className="relative overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)]">
      {/* Base Satellite Imagery */}
      <img
        src={imageUrl}
        alt={altText}
        className="block h-auto w-full object-cover select-none"
      />

      {/* SVG Spatial Bounding Boxes Layer */}
      <div className="absolute inset-0 pointer-events-none">
        {boxes.map((box) => {
          const [ymin, xmin, ymax, xmax] = box.box
          const top = `${ymin * 100}%`
          const left = `${xmin * 100}%`
          const width = `${(xmax - xmin) * 100}%`
          const height = `${(ymax - ymin) * 100}%`
          const isHovered = hoveredBoxId === box.id
          const isSelected = selectedBoxId === box.id
          const color = box.color || '#e08a5b'

          return (
            <div
              key={box.id}
              role="button"
              tabIndex={0}
              onClick={() => onSelectBox?.(box.id === selectedBoxId ? null : box.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onSelectBox?.(box.id === selectedBoxId ? null : box.id)
                }
              }}
              onMouseEnter={() => setHoveredBoxId(box.id)}
              onMouseLeave={() => setHoveredBoxId(null)}
              className="absolute pointer-events-auto cursor-pointer transition-all"
              style={{
                top,
                left,
                width,
                height,
                border: `2px solid ${color}`,
                backgroundColor: isHovered || isSelected ? `${color}33` : `${color}18`,
                boxShadow: isHovered || isSelected ? `0 0 12px ${color}88` : 'none',
              }}
              title={`${box.label} (${Math.round((box.confidence ?? 0) * 100)}% confidence)`}
            >
              {/* Floating Label Badge */}
              <div
                className="absolute -top-6 left-0 inline-flex items-center gap-1.5 whitespace-nowrap rounded px-1.5 py-0.5 text-[10px] font-medium text-white shadow-sm"
                style={{ backgroundColor: color }}
              >
                <span>{box.label}</span>
                {box.confidence !== undefined && (
                  <span className="font-mono-tabular opacity-90">
                    {Math.round(box.confidence * 100)}%
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
