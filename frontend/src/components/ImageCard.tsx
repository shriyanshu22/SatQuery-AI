import type { UploadedImage } from '@/types/image'
import { Panel } from './Panel'
import { StatusBadge } from './StatusBadge'
import { ImageMetadata } from './ImageMetadata'
import { TrashIcon, ImageIcon } from './icons'
import { formatRole } from '@/utils/format'

export function ImageCard({
  image,
  onRemove,
}: {
  image: UploadedImage
  onRemove: (id: string) => void
}) {
  const roleLabel = formatRole(image.role)

  return (
    <Panel className="overflow-hidden">
      <div className="relative aspect-[16/10] bg-[var(--color-panel-raised)]">
        {image.previewUrl ? (
          <img
            src={image.remotePreviewUrl ?? image.previewUrl}
            alt={`Preview of ${image.metadata.filename}`}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-[var(--color-text-muted)]">
            <ImageIcon width={24} height={24} />
          </div>
        )}

        {image.stage === 'uploading' && (
          <div className="absolute inset-x-0 bottom-0 h-1 bg-black/20">
            <div
              className="h-full bg-[var(--color-accent)] transition-all"
              style={{ width: `${image.progress}%` }}
            />
          </div>
        )}

        <button
          type="button"
          onClick={() => onRemove(image.id)}
          aria-label={`Remove ${image.metadata.filename}`}
          className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-panel)]/90 text-[var(--color-text-secondary)] shadow-sm backdrop-blur transition-colors hover:border-[var(--color-error)]/50 hover:text-[var(--color-error)]"
        >
          <TrashIcon width={14} height={14} />
        </button>
      </div>

      <div className="space-y-2 p-3">
        <div className="flex items-start justify-between gap-2">
          <p className="min-w-0 truncate text-xs font-medium text-[var(--color-text-primary)]" title={image.metadata.filename}>
            {image.metadata.filename}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {image.stage === 'uploading' && (
            <StatusBadge kind="pending" label={`Uploading ${image.progress}%`} />
          )}
          {image.stage === 'processing' && <StatusBadge kind="pending" label="Processing" />}
          {image.stage === 'ready' && image.validation.status === 'valid' && (
            <StatusBadge kind="success" label="Validated" />
          )}
          {image.stage === 'ready' && image.validation.status === 'warning' && (
            <StatusBadge kind="warning" label="Validated with warnings" />
          )}
          {image.stage === 'failed' && <StatusBadge kind="error" label="Upload failed" />}
          {roleLabel && <StatusBadge kind="neutral" label={roleLabel} />}
        </div>

        {image.validation.issues.length > 0 && (
          <ul className="space-y-1">
            {image.validation.issues.map((issue) => (
              <li
                key={issue.id}
                className="text-[11px] leading-snug text-[var(--color-text-muted)]"
              >
                {issue.severity === 'error' ? '✕' : '⚠'} {issue.message}
              </li>
            ))}
          </ul>
        )}

        {image.stage === 'ready' && (
          <div className="border-t border-[var(--color-border)] pt-2">
            <ImageMetadata metadata={image.metadata} />
          </div>
        )}
      </div>
    </Panel>
  )
}
