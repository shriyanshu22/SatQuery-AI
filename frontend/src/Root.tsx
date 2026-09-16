import { useState } from 'react'
import { Landing, type StartRole } from '@/pages/Landing'
import App from '@/App'

export default function Root() {
  const [role, setRole] = useState<StartRole | null>(null)

  if (!role) {
    return <Landing onSelectRole={setRole} />
  }

  return <App startRole={role} onChangeMode={() => setRole(null)} />
}
