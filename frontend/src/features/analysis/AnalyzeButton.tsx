import { SendIcon, SpinnerIcon } from '@/components/icons'

export function AnalyzeButton({
  disabled,
  isAnalyzing,
  onClick,
}: {
  disabled: boolean
  isAnalyzing: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || isAnalyzing}
      className="inline-flex shrink-0 items-center gap-2 rounded-full bg-[var(--color-accent)] px-5 py-2.5 text-sm font-semibold text-[#241207] shadow-sm transition-colors hover:bg-[var(--color-accent-strong)] disabled:cursor-not-allowed disabled:bg-[var(--color-border-strong)] disabled:text-[var(--color-text-muted)] disabled:shadow-none"
    >
      {isAnalyzing ? (
        <>
          <SpinnerIcon width={15} height={15} />
          Analyzing
        </>
      ) : (
        <>
          Analyze
          <SendIcon width={14} height={14} />
        </>
      )}
    </button>
  )
}
