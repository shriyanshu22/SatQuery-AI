import { useCallback, useRef, useState } from 'react'
import { apiClient } from '@/api'
import type { UploadedImage } from '@/types/image'

let idCounter = 0
function nextId() {
  idCounter += 1
  return `img-${idCounter}-${Date.now()}`
}

/**
 * Infers each image's role in the analysis set from what's currently
 * uploaded. This is a display-only heuristic — the backend is the real
 * source of truth for how images are actually used in analysis.
 */
function inferRoles(images: UploadedImage[]): UploadedImage[] {
  const ready = images.filter((img) => img.stage === 'ready')
  if (ready.length < 2) {
    return images.map((img) => ({ ...img, role: img.stage === 'ready' ? 'single' : img.role }))
  }

  const modalities = new Set(ready.map((img) => img.metadata.modality))
  if (modalities.has('sar') && (modalities.has('optical') || modalities.has('multispectral'))) {
    return images.map((img) => {
      if (img.stage !== 'ready') return img
      return { ...img, role: img.metadata.modality === 'sar' ? 'sar-pair' : 'optical-pair' }
    })
  }

  // Same modality, multiple images → treat as a temporal pair by upload order.
  return images.map((img) => {
    if (img.stage !== 'ready') return img
    const readyIdx = ready.findIndex((r) => r.id === img.id)
    return { ...img, role: readyIdx === 0 ? 'temporal-before' : 'temporal-after' }
  })
}

export function useImageUpload() {
  const [images, setImages] = useState<UploadedImage[]>([])
  const objectUrls = useRef<Set<string>>(new Set())

  const addFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files)

    for (const file of fileArray) {
      const id = nextId()
      const previewUrl = URL.createObjectURL(file)
      objectUrls.current.add(previewUrl)

      const placeholder: UploadedImage = {
        id,
        previewUrl,
        stage: 'uploading',
        progress: 0,
        metadata: {
          filename: file.name,
          fileType: file.type || 'unknown',
          sizeBytes: file.size,
          modality: 'unknown',
        },
        validation: { status: 'pending', issues: [] },
      }

      setImages((prev) => [...prev, placeholder])

      apiClient
        .uploadImage(file, (pct) => {
          setImages((prev) =>
            prev.map((img) => (img.id === id ? { ...img, progress: pct } : img)),
          )
        })
        .then(({ metadata, validation, remotePreviewUrl }) => {
          setImages((prev) => {
            const next = prev.map((img) =>
              img.id === id
                ? {
                    ...img,
                    stage: 'ready' as const,
                    progress: 100,
                    metadata,
                    validation,
                    remotePreviewUrl,
                  }
                : img,
            )
            return inferRoles(next)
          })
        })
        .catch(() => {
          setImages((prev) =>
            prev.map((img) =>
              img.id === id
                ? {
                    ...img,
                    stage: 'failed' as const,
                    validation: {
                      status: 'invalid',
                      issues: [
                        { id: 'upload-failed', message: 'Upload failed. Try again.', severity: 'error' },
                      ],
                    },
                  }
                : img,
            ),
          )
        })
    }
  }, [])

  const removeImage = useCallback((id: string) => {
    setImages((prev) => {
      const target = prev.find((img) => img.id === id)
      if (target && objectUrls.current.has(target.previewUrl)) {
        URL.revokeObjectURL(target.previewUrl)
        objectUrls.current.delete(target.previewUrl)
      }
      return inferRoles(prev.filter((img) => img.id !== id))
    })
  }, [])

  const clearImages = useCallback(() => {
    for (const url of objectUrls.current) {
      URL.revokeObjectURL(url)
    }
    objectUrls.current.clear()
    setImages([])
  }, [])

  return { images, addFiles, removeImage, clearImages }
}
