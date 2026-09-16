/**
 * API Schemas & Data Contracts
 *
 * Corresponds to backend FastAPI + Pydantic contracts.
 * The frontend acts strictly as a client to these schemas.
 */

export type TaskType =
  | 'vqa'
  | 'grounding'
  | 'change_detection'
  | 'cross_modal'
  | 'agentic'

export type ConfidenceStatus = 'available' | 'unavailable'

export type ConfidenceMethod =
  | 'calibrated'
  | 'model-derived'
  | 'evidence-derived'

export interface Confidence {
  status: ConfidenceStatus
  /** Normalized confidence score (0.0 - 1.0) or percentage (0 - 100). */
  score?: number | null
  method?: ConfidenceMethod | null
  explanation?: string | null
}

export interface ExecutionEvent {
  id: string
  label: string
  detail?: string
  status: 'pending' | 'active' | 'done' | 'failed'
  timestamp?: string
}

export interface ValidationIssue {
  id: string
  message: string
  severity: 'warning' | 'error'
  code?: string
}

export interface ValidationResult {
  status: 'valid' | 'warning' | 'invalid'
  issues: ValidationIssue[]
}

export interface ReportArtifact {
  available: boolean
  downloadUrl?: string
  format: 'pdf' | 'geojson' | 'geotiff'
  filename?: string
  generatedAt?: string
}

export interface ApiErrorPayload {
  code: string | number
  message: string
  details?: Record<string, unknown>
}

export interface QueryRequest {
  prompt: string
  imageIds: string[]
  options?: {
    taskHint?: TaskType
    enableSarCorroboration?: boolean
  }
}
