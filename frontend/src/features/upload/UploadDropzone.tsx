import { useRef, useState } from 'react'
import { UploadIcon } from '@/components/icons'

export function UploadDropzone({ onFiles }: { onFiles: (files: FileList | File[]) => void }) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragOver(false)
    if (e.dataTransfer.files.length > 0) {
      onFiles(e.dataTransfer.files)
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload imagery — drag and drop files or press Enter to browse"
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          inputRef.current?.click()
        }
      }}
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragOver(true)
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      className={`group flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
        isDragOver
          ? 'border-[var(--color-accent)] bg-[var(--color-accent-dim)]'
          : 'border-[var(--color-border-strong)] bg-[var(--color-panel-raised)] hover:border-[var(--color-accent)]/50 hover:bg-[var(--color-accent-dim)]/40'
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="image/*,.tif,.tiff,.geotiff"
        className="sr-only"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            onFiles(e.target.files)
            e.target.value = ''
          }
        }}
      />
      <div
        className={`flex h-11 w-11 items-center justify-center rounded-full border transition-colors ${
          isDragOver
            ? 'border-[var(--color-accent)] text-[var(--color-accent)]'
            : 'border-[var(--color-border-strong)] bg-[var(--color-panel)] text-[var(--color-text-muted)] group-hover:text-[var(--color-accent)]'
        }`}
      >
        <UploadIcon width={20} height={20} />
      </div>
      <div>
        <p className="text-sm font-medium text-[var(--color-text-primary)]">
          Drop imagery here, or click to browse
        </p>
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          GeoTIFF, optical, multispectral, or SAR — single scenes or pairs
        </p>
      </div>
    </div>
  )
}
