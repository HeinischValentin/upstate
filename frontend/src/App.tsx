import { useEffect, useState } from 'react'
import type { CheckerStatus } from './types'
import { UpdateCard } from './components/UpdateCard'
import './App.css'

const EXAMPLE_CHECKERS: CheckerStatus[] = [
  {
    type: 'Docker',
    update_available: true,
    updates: [
      { name: 'nginx', current_version: '1.25.3', new_version: '1.27.0' },
      { name: 'postgres', current_version: 'sha256:83f2ad12681a', new_version: 'sha256:8cb20d16e01a' },
    ],
    error: null,
  },
  {
    type: 'Home Assistant',
    update_available: false,
    updates: [],
    error: null,
  },
]

type CheckerItem = {
  type: string
  status: CheckerStatus | null
}

async function fetchCheckerTypes(): Promise<string[]> {
  const res = await fetch('/checkers')
  if (!res.ok) throw new Error(`Server returned ${res.status}`)
  return await res.json() as string[]
}

async function fetchChecker(type: string): Promise<CheckerStatus> {
  try {
    const res = await fetch(`/checkers/${encodeURIComponent(type)}`)
    if (res.ok) return await res.json() as CheckerStatus
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch { /* ignore */ }
    return { type, update_available: false, updates: [], error: detail }
  } catch (e) {
    return {
      type,
      update_available: false,
      updates: [],
      error: e instanceof Error ? e.message : 'Failed to fetch',
    }
  }
}

export default function App() {
  const [checkers, setCheckers] = useState<CheckerItem[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [refreshing, setRefreshing] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  async function loadCheckers() {
    setLoadingList(true)
    setRefreshing(true)
    setError(null)
    setCheckers([])

    let types: string[]
    try {
      types = await fetchCheckerTypes()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch checker list')
      setLoadingList(false)
      setRefreshing(false)
      return
    }

    setCheckers(types.map((type) => ({ type, status: null })))
    setLoadingList(false)

    const fetches = types.map((type) =>
      fetchChecker(type).then((status) => {
        setCheckers((prev) =>
          prev.map((c) => (c.type === type ? { ...c, status } : c))
        )
      })
    )
    Promise.all(fetches).then(() => {
      setLastRefresh(new Date())
      setRefreshing(false)
    })
  }

  useEffect(() => {
    (async () => {
      await loadCheckers()
    })()
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-title">
          <img src="/favicon.svg" alt="Upstate logo" className="header-logo" />
          <h1>Upstate</h1>
        </div>
        <div className="header-right">
          {lastRefresh && (
            <span className="last-refresh">
              Last refreshed: {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button className="refresh-btn" onClick={loadCheckers} disabled={refreshing}>
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </header>

      <main className="app-main">
        {loadingList && checkers.length === 0 && !error && (
          <div className="status-message">Loading...</div>
        )}

        {error && (
          <>
            <div className="status-message error">
              Could not reach the API: {error}
            </div>
            <div className="status-message example-notice">
              Showing example data.
            </div>
            <div className="card-grid">
              {EXAMPLE_CHECKERS.map((c) => (
                <UpdateCard key={c.type} type={c.type} checker={c} />
              ))}
            </div>
          </>
        )}

        {!error && checkers.length > 0 && (
          <div className="card-grid">
            {checkers.map((c) => (
              <UpdateCard key={c.type} type={c.type} checker={c.status} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
