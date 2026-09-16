import { SatelliteIcon, ScanIcon } from '@/components/icons'

export type StartRole = 'researcher'

interface LandingProps {
  /** Called when the visitor picks how they want to proceed. */
  onSelectRole: (role: StartRole) => void
}

const roles: {
  id: StartRole
  title: string
  description: string
  icon: (props: { width?: number; height?: number }) => React.ReactElement
}[] = [
  {
    id: 'researcher',
    title: 'Start Analysis',
    description:
      'Upload your own imagery and run full evidence-backed analysis, with execution traces and technical detail exposed.',
    icon: ScanIcon,
  },
]

export function Landing({ onSelectRole }: LandingProps) {
  return (
    <div className="relative z-0 min-h-screen overflow-hidden">
      <div className="relative z-10 mx-auto flex min-h-screen max-w-[760px] flex-col px-6 py-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--color-accent)]/30 bg-[var(--color-accent-dim)] text-[var(--color-accent)]">
              <SatelliteIcon width={16} height={16} />
            </div>
            <span className="text-[15px] font-semibold tracking-tight text-[var(--color-text-primary)]">
              GeoLens
            </span>
          </div>
          <span className="font-mono-tabular text-xs text-[var(--color-text-muted)]">
            SIH26167
          </span>
        </div>

        <div className="flex flex-1 flex-col justify-center py-16">
          <h1 className="max-w-[15ch] text-4xl font-semibold leading-[1.15] tracking-tight text-[var(--color-text-primary)] sm:text-[2.75rem]">
            Read the ground truth, straight from orbit.
          </h1>
          <p className="mt-4 max-w-[46ch] text-[15px] leading-relaxed text-[var(--color-text-secondary)]">
            GeoLens turns satellite imagery into evidence — grounded
            findings you can trace back to the pixels, not guesses.
          </p>

          <OrbitGraphic />

          <div className="mt-10">
            <p className="text-sm text-[var(--color-text-secondary)]">
              Ready to analyze satellite imagery?
            </p>
            <div className="mt-4 max-w-lg">
              {roles.map((role) => (
                <button
                  key={role.id}
                  type="button"
                  onClick={() => onSelectRole(role.id)}
                  className="group flex w-full flex-col items-start gap-2.5 rounded-2xl border border-[var(--color-border)] bg-[var(--color-panel)] p-5 text-left transition-colors hover:border-[var(--color-accent)]/50 hover:bg-[var(--color-panel-raised)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border-strong)] bg-[var(--color-panel-raised)] text-[var(--color-accent)] transition-colors group-hover:border-[var(--color-accent)]/40">
                    <role.icon width={16} height={16} />
                  </span>
                  <span className="text-[15px] font-medium text-[var(--color-text-primary)]">
                    {role.title}
                  </span>
                  <span className="text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
                    {role.description}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="pb-2 text-xs text-[var(--color-text-muted)]">
          Evidence-first analysis for satellite imagery.
        </p>
      </div>
    </div>
  )
}

function OrbitGraphic() {
  return (
    <div className="pointer-events-none mt-12 h-[120px] w-full max-w-[520px]" aria-hidden="true">
      <style>{`
        @keyframes geolens-orbit {
          from { offset-distance: 0%; }
          to { offset-distance: 100%; }
        }
        .geolens-sat {
          offset-path: path('M4 92 C 160 8, 360 8, 516 92');
          animation: geolens-orbit 9s linear infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .geolens-sat { animation: none; offset-distance: 45%; }
        }
      `}</style>
      <svg viewBox="0 0 520 120" width="100%" height="120" fill="none">
        <path
          d="M4 92 C 160 8, 360 8, 516 92"
          stroke="var(--color-border-strong)"
          strokeWidth="1"
          strokeDasharray="2 5"
        />
        <path
          d="M0 116 C 140 96, 380 96, 520 116"
          stroke="var(--color-border)"
          strokeWidth="1"
        />
        <circle className="geolens-sat" r="4" fill="var(--color-accent)" />
      </svg>
    </div>
  )
}
