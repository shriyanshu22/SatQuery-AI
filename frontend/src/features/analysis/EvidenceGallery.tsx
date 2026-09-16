import type {
  Evidence,
  BoundingBoxEvidence,
  ChangeMapEvidence,
  CrossModalEvidence,
  NumericalEvidence,
  TextEvidence,
  ImageEvidence,
} from '@/types/evidence'
import { GroundingViewer } from '@/features/grounding/GroundingViewer'
import { BeforeAfterViewer } from '@/features/change-detection/BeforeAfterViewer'
import { ChangeMetricsChart } from '@/features/change-detection/ChangeMetricsChart'
import { OpticalSarViewer } from '@/features/cross-modal/OpticalSarViewer'
import { Panel, PanelHeader } from '@/components/Panel'

interface EvidenceGalleryProps {
  evidence: Evidence[]
  defaultImageUrl?: string
}

export function EvidenceGallery({ evidence, defaultImageUrl }: EvidenceGalleryProps) {
  if (!evidence || evidence.length === 0) return null

  // Group bounding box items together for unified spatial overlay
  const boundingBoxes = evidence.filter(
    (e): e is BoundingBoxEvidence => e.type === 'bounding_box',
  )
  const changeMaps = evidence.filter(
    (e): e is ChangeMapEvidence => e.type === 'change_map',
  )
  const crossModalItems = evidence.filter(
    (e): e is CrossModalEvidence => e.type === 'cross_modal',
  )
  const numericalItems = evidence.filter(
    (e): e is NumericalEvidence => e.type === 'numerical',
  )
  const textItems = evidence.filter(
    (e): e is TextEvidence => e.type === 'text',
  )
  const imageItems = evidence.filter(
    (e): e is ImageEvidence => e.type === 'image' || e.type === 'crop',
  )

  return (
    <div className="space-y-5">
      {/* 1. Cross-Modal Optical + SAR Verification */}
      {crossModalItems.map((item) => (
        <OpticalSarViewer key={item.id} evidence={item} />
      ))}

      {/* 2. Bi-Temporal Change Detection Viewers */}
      {changeMaps.map((item) => (
        <BeforeAfterViewer key={item.id} evidence={item} />
      ))}

      {/* 3. Spatial Grounding / Bounding Box Overlay */}
      {boundingBoxes.length > 0 && (
        <GroundingViewer
          imageUrl={
            defaultImageUrl ||
            'https://images.unsplash.com/photo-1578575437130-527eed3abbec?auto=format&fit=crop&w=1200&q=80'
          }
          boxes={boundingBoxes}
        />
      )}

      {/* 4. Numerical Metrics & Recharts Visualizations */}
      {numericalItems.map((item) => (
        <ChangeMetricsChart key={item.id} evidence={item} />
      ))}

      {/* 5. Discrete Image / Crop Artifacts */}
      {imageItems.length > 0 && (
        <Panel>
          <PanelHeader title="Visual Artifacts & Crops" />
          <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2">
            {imageItems.map((img) => (
              <div
                key={img.id}
                className="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)]"
              >
                <img
                  src={img.imageUrl}
                  alt={img.caption || img.label}
                  className="aspect-[16/10] w-full object-cover"
                />
                <div className="p-2.5">
                  <p className="text-xs font-medium text-[var(--color-text-primary)]">
                    {img.label}
                  </p>
                  {img.caption && (
                    <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">
                      {img.caption}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* 6. Text Evidence & Grounded Provenance */}
      {textItems.length > 0 && (
        <Panel>
          <PanelHeader title="Grounded Text Citations" />
          <div className="space-y-3 p-4">
            {textItems.map((txt) => (
              <div
                key={txt.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3.5"
              >
                <p className="text-xs font-semibold text-[var(--color-text-primary)]">
                  {txt.label}
                </p>
                <p className="mt-1 text-xs leading-relaxed text-[var(--color-text-secondary)]">
                  {txt.text}
                </p>
                {txt.provenance && (
                  <p className="font-mono-tabular mt-2 text-[10px] text-[var(--color-data-strong)]">
                    Source: {txt.provenance}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  )
}
