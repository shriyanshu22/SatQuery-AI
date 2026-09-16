import { useState } from 'react'
import { SatelliteIcon, SettingsIcon, RefreshIcon } from './icons'
import { StatusBadge } from './StatusBadge'
import { getApiBaseUrl, setApiBaseUrl, resetApiBaseUrl } from '@/api/config'
import { realClient } from '@/api/real/realClient'

export function Header({
  backendOnline,
  backendLatency,
  onRefreshStatus,
  onChangeMode,
}: {
  backendOnline: boolean | null
  backendLatency?: number | null
  onRefreshStatus?: () => void
  onChangeMode?: () => void
}) {
  const [showConfig, setShowConfig] = useState(false)
  const [inputUrl, setInputUrl] = useState(getApiBaseUrl())
  const [testResult, setTestResult] = useState<{
    status: 'idle' | 'testing' | 'success' | 'error'
    message?: string
  }>({ status: 'idle' })

  async function handleTestConnection() {
    setTestResult({ status: 'testing' })
    const start = performance.now()
    try {
      // Temporarily test with the input URL
      const current = getApiBaseUrl()
      setApiBaseUrl(inputUrl)
      const res = await realClient.checkBackendStatus()
      const elapsed = Math.round(performance.now() - start)
      if (res.online) {
        setTestResult({
          status: 'success',
          message: `Connected successfully in ${elapsed}ms`,
        })
        onRefreshStatus?.()
      } else {
        setApiBaseUrl(current)
        setTestResult({
          status: 'error',
          message: `Endpoint unreachable at ${inputUrl}. Make sure backend is running.`,
        })
      }
    } catch (e: any) {
      setTestResult({
        status: 'error',
        message: e?.message || 'Connection failed.',
      })
    }
  }

  function handleSave() {
    setApiBaseUrl(inputUrl)
    setShowConfig(false)
    onRefreshStatus?.()
  }

  function handleReset() {
    resetApiBaseUrl()
    const def = getApiBaseUrl()
    setInputUrl(def)
    onRefreshStatus?.()
  }

  return (
    <>
      <header className="relative z-10 border-b border-[var(--color-border)] bg-[var(--color-panel)]/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--color-accent)]/30 bg-[var(--color-accent-dim)] text-[var(--color-accent)]">
              <SatelliteIcon width={18} height={18} />
            </div>
            <div>
              <div className="flex items-baseline gap-2">
                <h1 className="text-[15px] font-semibold tracking-tight text-[var(--color-text-primary)]">
                  GeoLens
                </h1>
                <span className="hidden text-xs text-[var(--color-text-muted)] sm:inline">
                  SIH26167
                </span>
              </div>
              <p className="text-xs text-[var(--color-text-secondary)]">
                Evidence-first analysis for satellite imagery
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Dynamic Pipeline Mode Badge */}
            <StatusBadge
              kind="neutral"
              label={backendOnline ? 'Live Pipeline' : 'Offline Simulation'}
            />

            {/* Live Backend Connection Indicator (Interactive) */}
            <button
              type="button"
              onClick={() => {
                setInputUrl(getApiBaseUrl())
                setTestResult({ status: 'idle' })
                setShowConfig(true)
              }}
              title="Click to configure backend URL & test connection"
              className="group flex items-center gap-1.5 rounded-full transition-opacity hover:opacity-85 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
            >
              {backendOnline === null ? (
                <StatusBadge kind="pending" label="Checking backend" />
              ) : backendOnline ? (
                <StatusBadge
                  kind="success"
                  label={backendLatency ? `Backend connected (${backendLatency}ms)` : 'Backend connected'}
                />
              ) : (
                <StatusBadge kind="error" label="Backend unreachable" />
              )}
            </button>

            {/* Settings trigger */}
            <button
              type="button"
              onClick={() => {
                setInputUrl(getApiBaseUrl())
                setTestResult({ status: 'idle' })
                setShowConfig(true)
              }}
              aria-label="Backend Connection Settings"
              title="Backend Connection Settings"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] text-[var(--color-text-muted)] transition-colors hover:border-[var(--color-accent)]/40 hover:text-[var(--color-text-primary)]"
            >
              <SettingsIcon width={14} height={14} />
            </button>

            {onChangeMode && (
              <button
                type="button"
                onClick={onChangeMode}
                className="text-xs text-[var(--color-text-muted)] underline decoration-[var(--color-border-strong)] underline-offset-2 hover:text-[var(--color-text-secondary)]"
              >
                Home
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Backend Settings Dialog */}
      {showConfig && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-[var(--color-border)] bg-[var(--color-panel)] p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
                Backend Connection Settings
              </h2>
              <button
                type="button"
                onClick={() => setShowConfig(false)}
                className="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
              >
                ✕
              </button>
            </div>

            <p className="mt-2 text-xs leading-relaxed text-[var(--color-text-secondary)]">
              GeoLens dynamically routes requests to your live FastAPI backend when available. If unreachable, it falls back to local simulation.
            </p>

            <div className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-[var(--color-text-muted)]">
                  Backend Base URL
                </label>
                <input
                  type="text"
                  value={inputUrl}
                  onChange={(e) => setInputUrl(e.target.value)}
                  placeholder="http://localhost:8000"
                  className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-3 py-2 font-mono text-xs text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
                />
              </div>

              {testResult.status !== 'idle' && (
                <div
                  className={`rounded-lg p-2.5 text-xs ${
                    testResult.status === 'testing'
                      ? 'bg-[var(--color-panel-raised)] text-[var(--color-text-secondary)]'
                      : testResult.status === 'success'
                        ? 'bg-[var(--color-success-dim)] text-[var(--color-success)]'
                        : 'bg-[var(--color-error-dim)] text-[var(--color-error)]'
                  }`}
                >
                  {testResult.status === 'testing' ? 'Testing connection...' : testResult.message}
                </div>
              )}

              <div className="flex items-center justify-between gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testResult.status === 'testing'}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-3 py-1.5 text-xs font-medium text-[var(--color-text-primary)] transition-colors hover:border-[var(--color-accent)]/50"
                >
                  <RefreshIcon width={12} height={12} />
                  <span>Test Connection</span>
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleReset}
                    className="text-xs text-[var(--color-text-muted)] underline hover:text-[var(--color-text-primary)]"
                  >
                    Reset
                  </button>
                  <button
                    type="button"
                    onClick={handleSave}
                    className="rounded-lg bg-[var(--color-accent)] px-3 py-1.5 text-xs font-medium text-[var(--color-panel)] transition-opacity hover:opacity-90"
                  >
                    Save & Apply
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

