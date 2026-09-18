import type { SatQueryApiClient } from '../client'
import type { ImageMetadata, ImageValidation, ImageModality } from '@/types/image'
import type { AnalysisResult, ExecutionStep } from '@/types/analysis'
import type { Evidence } from '@/types/evidence'
import { getApiBaseUrl } from '../config'

export const realClient: SatQueryApiClient = {
  async checkBackendStatus() {
    const baseUrl = getApiBaseUrl()
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 3000)

      let res = await fetch(`${baseUrl}/health`, {
        signal: controller.signal,
      }).catch(() => null)

      if (!res || !res.ok) {
        res = await fetch(`${baseUrl}/api/v1/health`, {
          signal: controller.signal,
        }).catch(() => null)
      }

      clearTimeout(timeoutId)
      return { online: Boolean(res && res.ok), mode: 'real' }
    } catch {
      return { online: false, mode: 'real' }
    }
  },

  async uploadImage(file, onProgress) {
    const baseUrl = getApiBaseUrl()
    const formData = new FormData()
    formData.append('file', file)

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', `${baseUrl}/api/v1/upload`)

      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const pct = Math.round((event.loaded / event.total) * 100)
            onProgress(pct)
          }
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText)
            const meta = data.metadata || {}
            const val = data.validation || {}

            const modality: ImageModality =
              meta.modality === 'sar'
                ? 'sar'
                : meta.modality === 'multispectral'
                  ? 'multispectral'
                  : 'optical'

            const metadata: ImageMetadata = {
              filename: data.filename || file.name,
              fileType: data.file_format || file.type || 'image/tiff',
              sizeBytes: data.size_bytes || file.size,
              width: meta.width ?? 2048,
              height: meta.height ?? 2048,
              bandCount: meta.band_count ?? (modality === 'sar' ? 1 : 3),
              modality,
              crs: meta.crs || 'EPSG:4326',
              acquisitionDate: meta.acquisition_date || new Date().toISOString().split('T')[0],
              sensor: meta.sensor || (modality === 'sar' ? 'Sentinel-1 C-SAR' : 'Optical Sensor'),
            }

            const validation: ImageValidation = {
              status: val.status === 'invalid' ? 'invalid' : val.warnings?.length ? 'warning' : 'valid',
              issues: [
                ...(val.errors || []).map((msg: string, i: number) => ({
                  id: `err-${i}`,
                  message: msg,
                  severity: 'error' as const,
                })),
                ...(val.warnings || []).map((msg: string, i: number) => ({
                  id: `warn-${i}`,
                  message: msg,
                  severity: 'warning' as const,
                })),
              ],
            }

            let remotePreviewUrl: string | undefined = undefined
            if (data.preview_url) {
              remotePreviewUrl = data.preview_url.startsWith('http')
                ? data.preview_url
                : `${baseUrl}${data.preview_url}`
            }

            const imageId = data.image_id

            resolve({ imageId, metadata, validation, remotePreviewUrl })
          } catch (e) {
            reject(new Error(`Failed to parse backend upload response: ${e}`))
          }
        } else {
          // Attempt fallback to /upload
          if (xhr.status === 404) {
            const fallbackXhr = new XMLHttpRequest()
            fallbackXhr.open('POST', `${baseUrl}/upload`)
            if (fallbackXhr.upload && onProgress) {
              fallbackXhr.upload.onprogress = xhr.upload.onprogress
            }
            fallbackXhr.onload = () => {
              if (fallbackXhr.status >= 200 && fallbackXhr.status < 300) {
                try {
                  const data = JSON.parse(fallbackXhr.responseText)
                  // reuse parsing
                  resolve({
                    imageId: data.image_id,
                    metadata: {
                      filename: file.name,
                      fileType: file.type || 'image/tiff',
                      sizeBytes: file.size,
                      width: 2048,
                      height: 2048,
                      bandCount: 3,
                      modality: 'optical',
                      crs: 'EPSG:4326',
                    },
                    validation: { status: 'valid', issues: [] },
                    remotePreviewUrl: data.preview_url ? `${baseUrl}${data.preview_url}` : undefined,
                  })
                } catch {
                  reject(new Error('Upload failed on fallback endpoint.'))
                }
              } else {
                reject(new Error(`Upload failed with status ${fallbackXhr.status}`))
              }
            }
            fallbackXhr.onerror = () => reject(new Error('Network error during upload.'))
            fallbackXhr.send(formData)
            return
          }
          reject(new Error(`Upload failed with status ${xhr.status}: ${xhr.statusText}`))
        }
      }

      xhr.onerror = () => reject(new Error('Network connection error during upload.'))
      xhr.send(formData)
    })
  },

  async submitQuery(query) {
    const baseUrl = getApiBaseUrl()
    const endpoint = `${baseUrl}/api/v1/query`

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query.prompt,
        image_ids: query.imageIds,
        include_evidence: true,
        include_trace: true,
      }),
    })

    if (!response.ok) {
      throw new Error(`Query submission failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    const taskId = data.task_id || `task-${Date.now()}`

    // If query returned immediately with completed result
    if (data.status === 'completed' && data.result) {
      return formatBackendResult(taskId, data.result)
    }

    // Polling if processing asynchronously
    let attempts = 0
    while (attempts < 60) {
      await new Promise((r) => setTimeout(r, 1000))
      attempts += 1

      const statusRes = await fetch(`${baseUrl}/api/v1/status/${taskId}`).catch(() => null)
      if (statusRes && statusRes.ok) {
        const statusData = await statusRes.json()
        if (statusData.status === 'completed') {
          const resultRes = await fetch(`${baseUrl}/api/v1/result/${taskId}`)
          if (resultRes.ok) {
            const resultData = await resultRes.json()
            return formatBackendResult(taskId, resultData.result || resultData)
          }
        }
        if (statusData.status === 'failed') {
          throw new Error(statusData.error || 'Analysis execution failed in backend.')
        }
      }
    }

    throw new Error('Analysis timed out waiting for backend computation.')
  },

  async getAnalysis(analysisId) {
    const baseUrl = getApiBaseUrl()
    const res = await fetch(`${baseUrl}/api/v1/result/${analysisId}`)
    if (!res.ok) {
      throw new Error(`Failed to fetch analysis ${analysisId}: ${res.statusText}`)
    }
    const data = await res.json()
    return formatBackendResult(analysisId, data.result || data)
  },

  async downloadReport(analysisId) {
    const baseUrl = getApiBaseUrl()
    let res = await fetch(`${baseUrl}/api/v1/artifacts/${analysisId}`).catch(() => null)
    if (!res || !res.ok) {
      res = await fetch(`${baseUrl}/api/v1/analysis/${analysisId}/report`)
    }

    if (!res.ok) {
      throw new Error(`Failed to download report for analysis ${analysisId}`)
    }

    const blob = await res.blob()
    return {
      blob,
      filename: `GeoLens_Analysis_${analysisId}.pdf`,
    }
  },
}

function formatBackendResult(
  analysisId: string,
  rawResult: Record<string, any>,
): AnalysisResult {
  const answer = rawResult.answer || rawResult.summary || 'Analysis completed successfully.'

  const executionTrace: ExecutionStep[] = (rawResult.execution_trace || []).map(
    (step: any, idx: number) => ({
      id: `step-${step.step_number ?? idx}`,
      label: step.action || `Pipeline stage ${idx + 1}`,
      status:
        step.status === 'completed'
          ? ('done' as const)
          : step.status === 'failed'
            ? ('failed' as const)
            : ('done' as const),
      timestamp: new Date().toISOString(),
      durationMs: step.duration_ms,
      detail: step.observable_output,
    }),
  )

  const evidence: Evidence[] = (rawResult.evidence || []).map((ev: any, idx: number) => {
    const type = ev.type || 'text'
    const d = ev.data || {}
    return {
      id: `ev-${idx + 1}`,
      type: type,
      label: d.label || `${type.replace('_', ' ').toUpperCase()} Evidence`,
      ...d,
    } as Evidence
  })

  return {
    id: analysisId,
    queryId: `query-${analysisId}`,
    status: 'succeeded',
    answer,
    confidence: rawResult.confidence
      ? {
          status: 'available',
          score: rawResult.confidence.value ?? 0.9,
          method: 'calibrated',
          explanation: `Source: ${rawResult.confidence.source || 'Multimodal verification'}`,
        }
      : {
          status: 'unavailable',
        },
    executionTrace,
    evidence,
    warnings: rawResult.warnings || [],
    technicalDetails: rawResult.metadata
      ? {
          modelUsed: rawResult.metadata.model_backend || 'FastAPI Remote Sensing Engine',
          processingTimeMs: rawResult.metadata.execution_time_ms,
          crs: rawResult.metadata.crs,
          sensor: rawResult.metadata.sensor,
        }
      : undefined,
  }
}
