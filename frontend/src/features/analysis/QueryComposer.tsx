import { useEffect, useState } from 'react'
import { AnalyzeButton } from './AnalyzeButton'

const EXAMPLE_QUERIES = [
  'Describe the land-cover and major objects visible in this image.',
  'Highlight the water body referred to in the query.',
  'What changed between these two dates, and where did the change occur?',
  'Use the optical and SAR images together to identify built-up and water-covered regions.',
  'Has the built-up area increased, decreased, or remained unchanged?',
]

interface QueryComposerProps {
  disabled: boolean
  isAnalyzing: boolean
  onSubmit: (prompt: string) => void
  initialPrompt?: string
}

export function QueryComposer({
  disabled,
  isAnalyzing,
  onSubmit,
  initialPrompt = '',
}: QueryComposerProps) {
  const [prompt, setPrompt] = useState(initialPrompt)

  useEffect(() => {
    if (initialPrompt) {
      setPrompt(initialPrompt)
    }
  }, [initialPrompt])

  function handleSubmit() {
    const trimmed = prompt.trim()
    if (!trimmed || disabled || isAnalyzing) return
    onSubmit(trimmed)
  }

  return (
    <div className="space-y-3">
      <div>
        <label htmlFor="query-input" className="sr-only">
          What do you want to know?
        </label>
        <textarea
          id="query-input"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              e.preventDefault()
              handleSubmit()
            }
          }}
          placeholder="What do you want to know about this satellite imagery?"
          rows={3}
          disabled={disabled}
          className="w-full resize-none rounded-2xl border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-4 py-3 text-[15px] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-accent)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {EXAMPLE_QUERIES.map((example) => (
          <button
            key={example}
            type="button"
            disabled={disabled}
            onClick={() => setPrompt(example)}
            className="rounded-full border border-[var(--color-border)] bg-[var(--color-panel)] px-3 py-1.5 text-[11px] text-[var(--color-text-secondary)] transition-colors hover:border-[var(--color-accent)]/50 hover:text-[var(--color-accent-strong)] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {example}
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] text-[var(--color-text-muted)]">
          {disabled ? 'Upload imagery to begin' : 'Press ⌘/Ctrl + Enter to analyze'}
        </p>
        <AnalyzeButton
          disabled={disabled || !prompt.trim()}
          isAnalyzing={isAnalyzing}
          onClick={handleSubmit}
        />
      </div>
    </div>
  )
}
