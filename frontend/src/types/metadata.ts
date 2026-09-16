import type { ImageModality, ValidationStatus } from './image'

export interface ExtendedGeospatialMetadata {
  filename: string
  fileType: string
  format?: string
  sizeBytes: number
  width?: number
  height?: number
  bandCount?: number
  dtype?: string
  modality: ImageModality
  crs?: string
  resolutionMeters?: number
  bounds?: [number, number, number, number] // [minX, minY, maxX, maxY]
  acquisitionDate?: string
  sensor?: string
  validationStatus: ValidationStatus
}
