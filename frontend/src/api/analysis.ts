import { apiClient } from './index'
import type { AnalysisQuery } from '@/types/analysis'

export async function submitAnalysisQuery(query: Pick<AnalysisQuery, 'prompt' | 'imageIds'>) {
  return apiClient.submitQuery(query)
}

export async function fetchAnalysisResult(analysisId: string) {
  return apiClient.getAnalysis(analysisId)
}
