import type { ReactNode } from 'react'

export function Sidebar({ children }: { children: ReactNode }) {
  return <aside className="flex flex-col gap-4">{children}</aside>
}
