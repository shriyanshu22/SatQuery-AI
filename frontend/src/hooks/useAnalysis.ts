import { useCallback, useState } from 'react'
import { apiClient } from '@/api'
import type { AnalysisResult } from '@/types/analysis'

export function useAnalysis() {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runQuery = useCallback(async (prompt: string, imageIds: string[]) => {
    setIsAnalyzing(true)
    setError(null)
    try {
      const submitted = await apiClient.submitQuery({ prompt, imageIds })
      setResult(submitted)
      const final = await apiClient.getAnalysis(submitted.id)
      setResult(final)
    } catch {
      setError('Analysis failed to complete. Check your connection and try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }, [])

  const reset = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  return { result, isAnalyzing, error, runQuery, reset }
}
