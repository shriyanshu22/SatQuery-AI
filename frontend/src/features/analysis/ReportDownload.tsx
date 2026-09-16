import { useState } from 'react'
import { downloadAnalysisReport } from '@/api/results'
import { SpinnerIcon } from '@/components/icons'

interface ReportDownloadProps {
  analysisId: string
  filename?: string
  format?: string
}

export function ReportDownload({
  analysisId,
  filename = 'SatQuery_Analysis_Report.txt',
  format = 'PDF',
}: ReportDownloadProps) {
  const [isDownloading, setIsDownloading] = useState(false)

  async function handleDownload() {
    setIsDownloading(true)
    try {
      const { blob, filename: resolvedName } = await downloadAnalysisReport(analysisId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = resolvedName || filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Report download failed:', err)
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handleDownload}
      disabled={isDownloading}
      className="inline-flex items-center gap-2 rounded-xl border border-[var(--color-accent)]/50 bg-[var(--color-accent-dim)] px-4 py-2 text-xs font-semibold text-[var(--color-accent)] transition-colors hover:bg-[var(--color-accent)] hover:text-[#241207] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] disabled:cursor-not-allowed disabled:opacity-50"
    >
      {isDownloading ? (
        <>
          <SpinnerIcon width={14} height={14} />
          Downloading Artifact…
        </>
      ) : (
        <>
          <span>Download Report ({format.toUpperCase()})</span>
          <span className="text-[10px] opacity-75">↓</span>
        </>
      )}
    </button>
  )
}
