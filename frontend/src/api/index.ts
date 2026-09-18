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
    if (!cachedBackendOnline) {
      throw new Error('Backend is offline. Cannot upload image in live mode.')
    }
    return realClient.uploadImage(file, onProgress)
  },

  async submitQuery(query) {
    if (!cachedBackendOnline) {
      throw new Error('Backend is offline. Cannot submit query in live mode.')
    }
    return realClient.submitQuery(query)
  },

  async getAnalysis(analysisId) {
    if (!cachedBackendOnline) {
      throw new Error('Backend is offline. Cannot fetch analysis.')
    }
    return realClient.getAnalysis(analysisId)
  },

  async downloadReport(analysisId) {
    if (!cachedBackendOnline) {
      throw new Error('Backend is offline. Cannot download report.')
    }
    return realClient.downloadReport(analysisId)
  },
}

export const apiMode = 'dynamic'
export type { SatQueryApiClient } from './client'
