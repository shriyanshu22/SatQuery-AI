import type { AnalysisResult } from '@/types/analysis'
import { AnswerCard } from './AnswerCard'
import { ConfidenceCard } from './ConfidenceCard'
import { EvidenceGallery } from './EvidenceGallery'
import { ReportDownload } from './ReportDownload'
import { TechnicalDetailsPanel } from './TechnicalDetailsPanel'
import { WarningPanel } from '@/components/WarningPanel'

interface AnalysisSummaryPanelProps {
  result: AnalysisResult
  defaultImageUrl?: string
  onReset?: () => void
}

export function AnalysisSummaryPanel({
  result,
  defaultImageUrl,
  onReset,
}: AnalysisSummaryPanelProps) {
  if (result.status !== 'succeeded' && result.status !== 'warning') return null

  const answerText =
    result.answer ||
    result.summary ||
    'Analysis completed successfully with grounded evidence.'

  return (
    <div className="space-y-5">
      {/* 1. Visually Dominant Answer Card (Master Prompt Section 12) */}
      <AnswerCard answer={answerText} task={result.task} />

      {/* 2. Structured Confidence Assessment (Master Prompt Section 13) */}
      <ConfidenceCard confidence={result.confidence} />

      {/* Action Strip: Report Download & Reset */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] px-4 py-3">
        <div className="flex items-center gap-3">
          <ReportDownload
            analysisId={result.id}
            filename={result.report?.filename}
            format={result.report?.format}
          />
        </div>

        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="text-xs text-[var(--color-text-muted)] underline decoration-[var(--color-border-strong)] underline-offset-2 transition-colors hover:text-[var(--color-text-primary)]"
          >
            Clear and Start New Query
          </button>
        )}
      </div>

      {/* Warnings & Analytical Limitations (if present) */}
      {result.warnings && result.warnings.length > 0 && (
        <div className="space-y-2">
          {result.warnings.map((warning, idx) => (
            <WarningPanel
              key={idx}
              title="Sensor Limitation Notice"
              description={warning}
            />
          ))}
        </div>
      )}

      {/* 3. Polymorphic Evidence System (Master Prompt Section 14) */}
      <EvidenceGallery
        evidence={result.evidence}
        defaultImageUrl={defaultImageUrl}
      />

      {/* 4. Expandable Technical Provenance (Master Prompt Section 35) */}
      <TechnicalDetailsPanel
        details={result.technicalDetails}
        executionTrace={result.executionTrace}
      />
    </div>
  )
}
