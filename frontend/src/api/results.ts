import { apiClient } from './index'

export async function downloadAnalysisReport(analysisId: string) {
  return apiClient.downloadReport(analysisId)
}
