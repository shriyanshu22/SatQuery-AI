import type { SatQueryApiClient } from './client'
import { mockClient } from './mock/mockClient'
import { realClient } from './real/realClient'
import { getApiBaseUrl, setApiBaseUrl, resetApiBaseUrl } from './config'

export { getApiBaseUrl, setApiBaseUrl, resetApiBaseUrl }

let cachedBackendOnline: boolean | null = null

export const apiClient: SatQueryApiClient = {
  async checkBackendStatus() {
    const status = await realClient.checkBackendStatus()
    cachedBackendOnline = status.online
    return status
  },

  async uploadImage(file, onProgress) {
    if (cachedBackendOnline) {
      try {
        return await realClient.uploadImage(file, onProgress)
      } catch (err) {
        console.warn('[GeoLens] Real upload failed, falling back to local simulation:', err)
        return mockClient.uploadImage(file, onProgress)
      }
    }
    return mockClient.uploadImage(file, onProgress)
  },

  async submitQuery(query) {
    if (cachedBackendOnline) {
      try {
        return await realClient.submitQuery(query)
      } catch (err) {
        console.warn('[GeoLens] Real query failed, falling back to local simulation:', err)
        return mockClient.submitQuery(query)
      }
    }
    return mockClient.submitQuery(query)
  },

  async getAnalysis(analysisId) {
    if (cachedBackendOnline) {
      try {
        return await realClient.getAnalysis(analysisId)
      } catch {
        return mockClient.getAnalysis(analysisId)
      }
    }
    return mockClient.getAnalysis(analysisId)
  },

  async downloadReport(analysisId) {
    if (cachedBackendOnline) {
      try {
        return await realClient.downloadReport(analysisId)
      } catch {
        return mockClient.downloadReport(analysisId)
      }
    }
    return mockClient.downloadReport(analysisId)
  },
}

export const apiMode = 'dynamic'
export type { SatQueryApiClient } from './client'
