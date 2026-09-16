/**
 * Domain types for uploaded imagery.
 *
 * These types are a clean abstraction over whatever the backend eventually
 * returns. No API contract document was available at build time, so this
 * shape is intentionally conservative and easy to reconcile against the
 * real contract later — see src/api/README.md.
 */

export type ImageModality = 'optical' | 'sar' | 'multispectral' | 'unknown'

export type ValidationStatus = 'valid' | 'warning' | 'invalid' | 'pending'

export interface ValidationIssue {
  id: string
  message: string
  severity: 'warning' | 'error'
}

export interface ImageValidation {
  status: ValidationStatus
  issues: ValidationIssue[]
}

export interface ImageMetadata {
  filename: string
  fileType: string
  sizeBytes: number
  width?: number
  height?: number
  bandCount?: number
  modality: ImageModality
  crs?: string
  acquisitionDate?: string
  sensor?: string
}

export type UploadStage = 'queued' | 'uploading' | 'processing' | 'ready' | 'failed'

export interface UploadedImage {
  id: string
  /** Local object URL for immediate preview, revoked on removal. */
  previewUrl: string
  /** Backend-generated preview, preferred over previewUrl once available. */
  remotePreviewUrl?: string
  stage: UploadStage
  progress: number
  metadata: ImageMetadata
  validation: ImageValidation
  role?: ImageRole
}

/**
 * How this image participates in the analysis set. The user never picks
 * this explicitly — the backend infers it from what's uploaded, and the
 * frontend just reflects it back.
 */
export type ImageRole =
  | 'single'
  | 'temporal-before'
  | 'temporal-after'
  | 'optical-pair'
  | 'sar-pair'
