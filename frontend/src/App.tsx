import { useEffect, useState, useCallback } from 'react'
import { apiClient } from '@/api'
import { Layout } from '@/components/Layout'
import { Header } from '@/components/Header'
import { Sidebar } from '@/components/Sidebar'
import { Panel, PanelHeader } from '@/components/Panel'
import { EmptyState } from '@/components/EmptyState'
import { HelpPanel } from '@/components/HelpPanel'
import { ImageCard } from '@/components/ImageCard'
import { ImageIcon } from '@/components/icons'
import { GeospatialMapViewer } from '@/components/GeospatialMapViewer'
import { UploadDropzone } from '@/features/upload/UploadDropzone'
import { QueryComposer } from '@/features/analysis/QueryComposer'
import { AnalysisStatusPanel } from '@/features/analysis/AnalysisStatusPanel'
import { AnalysisSummaryPanel } from '@/features/analysis/AnalysisSummaryPanel'
import { useImageUpload } from '@/hooks/useImageUpload'
import { useAnalysis } from '@/hooks/useAnalysis'
import type { StartRole } from '@/pages/Landing'

interface AppProps {
  /** How the visitor entered — picked on the landing page. Optional so App still renders standalone. */
  startRole?: StartRole
  /** Sends the visitor back to the landing page to pick again. */
  onChangeMode?: () => void
}

export function App({ onChangeMode }: AppProps) {
  const { images, addFiles, removeImage, clearImages } = useImageUpload()
  const { result, isAnalyzing, error, runQuery, reset } = useAnalysis()
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const [backendLatency, setBackendLatency] = useState<number | null>(null)
  const [currentPrompt] = useState('')

  const checkConnection = useCallback(async () => {
    const start = performance.now()
    try {
      const status = await apiClient.checkBackendStatus()
      setBackendOnline(status.online)
      setBackendLatency(status.online ? Math.round(performance.now() - start) : null)
    } catch {
      setBackendOnline(false)
      setBackendLatency(null)
    }
  }, [])

  useEffect(() => {
    checkConnection()
    const interval = setInterval(checkConnection, 5000)
    window.addEventListener('focus', checkConnection)
    return () => {
      clearInterval(interval)
      window.removeEventListener('focus', checkConnection)
    }
  }, [checkConnection])

  const readyImages = images.filter((img) => img.stage === 'ready')
  const hasReadyImages = readyImages.length > 0

  function handleSubmitQuery(prompt: string) {
    runQuery(
      prompt,
      readyImages.map((img) => img.id),
    )
  }

  return (
    <Layout
      header={
        <Header
          backendOnline={backendOnline}
          backendLatency={backendLatency}
          onRefreshStatus={checkConnection}
          onChangeMode={onChangeMode}
        />
      }
      main={
        <>
          {/* Imagery Ingestion Panel */}
          <Panel>
            <PanelHeader
              title="Remote Sensing Imagery"
              subtitle="Drop single scenes, bi-temporal epochs, or Optical + SAR pairs"
              action={
                images.length > 0 ? (
                  <button
                    type="button"
                    onClick={clearImages}
                    className="text-xs text-[var(--color-text-muted)] underline decoration-[var(--color-border)] underline-offset-2 hover:text-[var(--color-error)]"
                  >
                    Clear All
                  </button>
                ) : undefined
              }
            />

            <div className="space-y-4 p-4">
              <UploadDropzone onFiles={addFiles} />

              {images.length === 0 ? (
                <EmptyState
                  icon={<ImageIcon width={18} height={18} />}
                  title="Nothing uploaded yet"
                  description="Drop GeoTIFF, optical, multispectral, or SAR scenes above to begin analysis."
                />
              ) : (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {images.map((image) => (
                    <ImageCard key={image.id} image={image} onRemove={removeImage} />
                  ))}
                </div>
              )}
            </div>
          </Panel>

          {/* Natural Language Query Composer (Master Prompt Section 9) */}
          <Panel className="p-4">
            <QueryComposer
              disabled={!hasReadyImages}
              isAnalyzing={isAnalyzing}
              onSubmit={handleSubmitQuery}
              initialPrompt={currentPrompt}
            />
          </Panel>

          {/* Result Hierarchy & Polymorphic Evidence System (Sections 12 - 17) */}
          {result && (
            <AnalysisSummaryPanel
              result={result}
              defaultImageUrl={readyImages[0]?.remotePreviewUrl ?? readyImages[0]?.previewUrl}
              onReset={reset}
            />
          )}
        </>
      }
      sidebar={
        <Sidebar>
          {/* Observable Execution Trace Timeline (Section 11) */}
          <AnalysisStatusPanel
            result={result}
            isAnalyzing={isAnalyzing}
            error={error}
          />

          {/* Spatial Map HUD Layer */}
          <GeospatialMapViewer crs={readyImages[0]?.metadata.crs} />

          {/* Operational Guidance */}
          <HelpPanel />
        </Sidebar>
      }
    />
  )
}

export default App
