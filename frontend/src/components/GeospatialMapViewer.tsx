import { Panel, PanelHeader } from './Panel'
import { StatusBadge } from './StatusBadge'

interface GeospatialMapViewerProps {
  centerLat?: number
  centerLng?: number
  zoom?: number
  crs?: string
  sceneExtent?: [number, number, number, number] // [minLat, minLng, maxLat, maxLng]
}

export function GeospatialMapViewer({
  centerLat = 28.6139,
  centerLng = 77.2090,
  crs = 'EPSG:4326',
}: GeospatialMapViewerProps) {
  return (
    <Panel className="overflow-hidden">
      <PanelHeader
        title="Geospatial Spatial Context"
        subtitle={`WGS 84 Reference Frame · ${crs}`}
        action={<StatusBadge kind="neutral" label={crs} />}
      />

      <div className="p-4">
        <div className="relative aspect-[16/9] w-full overflow-hidden rounded-xl border border-[var(--color-border)] bg-[#0b171c]">
          {/* Spatial Grid & Coordinate HUD */}
          <div className="absolute inset-0 bg-[radial-gradient(#2b4b56_1px,transparent_1px)] [background-size:16px_16px] opacity-40" />

          {/* Coordinate Crosshairs */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-24 w-24 rounded-full border border-dashed border-[var(--color-accent)]/40 bg-[var(--color-accent-dim)]/20 animate-pulse" />
            <div className="absolute h-px w-32 bg-[var(--color-accent)]/50" />
            <div className="absolute h-32 w-px bg-[var(--color-accent)]/50" />
          </div>

          {/* Map Status HUD Overlay */}
          <div className="absolute bottom-3 left-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-panel)]/90 px-3 py-1.5 font-mono text-[11px] text-[var(--color-text-secondary)] backdrop-blur">
            Centroid: {centerLat.toFixed(4)}° N, {centerLng.toFixed(4)}° E
          </div>

          <div className="absolute top-3 right-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-panel)]/90 px-3 py-1.5 text-[11px] text-[var(--color-text-muted)] backdrop-blur">
            Interactive Leaflet CRS Layer
          </div>
        </div>
      </div>
    </Panel>
  )
}
