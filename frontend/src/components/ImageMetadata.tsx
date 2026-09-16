import type { ImageMetadata as ImageMetadataType } from '@/types/image'
import { formatBytes, formatModality } from '@/utils/format'

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1">
      <dt className="text-[11px] text-[var(--color-text-muted)]">{label}</dt>
      <dd className="font-mono-tabular truncate text-[11px] text-[var(--color-text-secondary)]">
        {value}
      </dd>
    </div>
  )
}

export function ImageMetadata({ metadata }: { metadata: ImageMetadataType }) {
  return (
    <dl className="divide-y divide-[var(--color-border)]/60">
      <Row label="Type" value={formatModality(metadata.modality)} />
      <Row label="Size" value={formatBytes(metadata.sizeBytes)} />
      {metadata.width && metadata.height && (
        <Row label="Dimensions" value={`${metadata.width} × ${metadata.height}`} />
      )}
      {metadata.bandCount !== undefined && (
        <Row label="Bands" value={String(metadata.bandCount)} />
      )}
      {metadata.crs && <Row label="CRS" value={metadata.crs} />}
      <Row
        label="Acquired"
        value={metadata.acquisitionDate ?? '—'}
      />
    </dl>
  )
}
