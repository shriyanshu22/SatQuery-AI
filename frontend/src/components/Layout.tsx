import type { ReactNode } from 'react'

export function Layout({
  header,
  main,
  sidebar,
}: {
  header: ReactNode
  main: ReactNode
  sidebar: ReactNode
}) {
  return (
    <div className="relative z-0 min-h-screen">
      {header}
      <main className="mx-auto max-w-[1400px] px-6 py-6">
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_380px]">
          <div className="min-w-0 space-y-5">{main}</div>
          <div className="min-w-0">{sidebar}</div>
        </div>
      </main>
    </div>
  )
}
