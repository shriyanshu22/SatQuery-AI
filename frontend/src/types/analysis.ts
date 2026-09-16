import type { TaskType, Confidence, ExecutionEvent, ReportArtifact } from './api'
import type { Evidence } from './evidence'

export type AnalysisStatus =
  | 'idle'
  | 'submitting'
  | 'running'
  | 'succeeded'
  | 'warning'
  | 'failed'

/**
 * ExecutionStep represents an observable event in the backend pipeline.
 * Aligns with ExecutionEvent.
 */
export type ExecutionStep = ExecutionEvent

/**
 * Legacy EvidenceItem kept for backward compatibility.
 * Replaced by the polymorphic Evidence union in ./evidence.ts.
 */
export interface EvidenceItem {
  id: string
  kind: 'text' | 'region' | 'metric' | 'source-image'
  label: string
  value?: string
}

export interface AnalysisQuery {
  id: string
  prompt: string
  imageIds: string[]
  submittedAt: string
}

export interface TechnicalDetails {
  modelUsed?: string
  modelVersion?: string
  processingTimeMs?: number
  crs?: string
  sensor?: string
  modality?: string
  confidenceSource?: string
}

export interface AnalysisResult {
  id: string
  queryId: string
  status: AnalysisStatus
  task?: TaskType
  summary?: string
  answer?: string
  confidence?: Confidence
  executionTrace: ExecutionStep[]
  evidence: Evidence[]
  warnings: string[]
  error?: string
  report?: ReportArtifact
  technicalDetails?: TechnicalDetails
}
