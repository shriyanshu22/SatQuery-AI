/**
 * Generic Polymorphic Evidence System
 *
 * Implements Master Prompt Section 14 (GENERIC EVIDENCE SYSTEM).
 * The backend returns different evidence types depending on the task.
 * The UI inspects `evidence.type` and dispatches to the appropriate specialized renderer.
 * Coordinates, regions, and metrics MUST come from the backend; frontend never calculates them.
 */

export type EvidenceType =
  | 'bounding_box'
  | 'segmentation_mask'
  | 'change_map'
  | 'cross_modal'
  | 'numerical'
  | 'image'
  | 'crop'
  | 'text'

export interface BaseEvidence {
  id: string
  type: EvidenceType
  label: string
  description?: string
}

/**
 * Spatial Bounding Box Evidence (e.g., building, vehicle, infrastructure detection).
 * Coordinates are normalized [ymin, xmin, ymax, xmax] (0.0 - 1.0) or pixel coordinates.
 */
export interface BoundingBoxEvidence extends BaseEvidence {
  type: 'bounding_box'
  sourceImageId: string
  box: [number, number, number, number] // [ymin, xmin, ymax, xmax] normalized (0 to 1)
  category: string
  confidence?: number
  color?: string
}

/**
 * Segmentation Mask Evidence (e.g. water bodies, burned area, urban footprint).
 */
export interface SegmentationMaskEvidence extends BaseEvidence {
  type: 'segmentation_mask'
  sourceImageId: string
  maskUrl: string
  category: string
  opacity?: number
  coveragePercentage?: number
}

/**
 * Change Map Evidence (bi-temporal comparison).
 */
export interface ChangeMapEvidence extends BaseEvidence {
  type: 'change_map'
  beforeImageUrl: string
  afterImageUrl: string
  changeMapUrl: string
  changedAreaHectares?: number
  changedAreaKm2?: number
  changeType?: string
  confidence?: number
  metrics?: {
    totalAreaHectares?: number
    changedPercentage?: number
    lossHectares?: number
    gainHectares?: number
  }
}

/**
 * Cross-Modal Agreement / Disagreement Evidence (Optical + SAR).
 * Note: 'inconclusive' is a legitimate analytical outcome, never styled as an error.
 */
export type AgreementStatus = 'agree' | 'disagree' | 'inconclusive'

export interface CrossModalEvidence extends BaseEvidence {
  type: 'cross_modal'
  opticalImageUrl: string
  sarImageUrl: string
  agreement: AgreementStatus
  opticalEvidence: string
  sarEvidence: string
  combinedInterpretation: string
  confidence?: number
}

/**
 * Numerical / Metric Evidence (visualized via Recharts or metric cards).
 */
export interface NumericalEvidence extends BaseEvidence {
  type: 'numerical'
  value: number
  unit?: string
  changeDirection?: 'increase' | 'decrease' | 'neutral'
  series?: Array<{
    name: string
    value: number
    secondaryValue?: number
    category?: string
  }>
}

/**
 * Visual Image / Crop Evidence.
 */
export interface ImageEvidence extends BaseEvidence {
  type: 'image' | 'crop'
  imageUrl: string
  caption?: string
  sourceImageId?: string
}

/**
 * Textual / Grounded Fact Evidence.
 */
export interface TextEvidence extends BaseEvidence {
  type: 'text'
  text: string
  provenance?: string
}

/**
 * Polymorphic Union of all supported Evidence types.
 */
export type Evidence =
  | BoundingBoxEvidence
  | SegmentationMaskEvidence
  | ChangeMapEvidence
  | CrossModalEvidence
  | NumericalEvidence
  | ImageEvidence
  | TextEvidence
