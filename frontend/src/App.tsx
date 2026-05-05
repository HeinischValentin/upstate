import { useEffect, useState } from 'react'
import type { CheckerStatus } from './types'
import { UpdateCard } from './components/UpdateCard'
import './App.css'

async function fetchCheckerData(): Promise<{ results: CheckerStatus[]; error: string | null }> {
  let types: string[]
  try {
    const res = await fetch('/checkers')
    if (!res.ok) throw new Error(`Server returned ${res.status}`)
    types = await res.json() as string[]
  } catch (e) {
    return { results: [], error: e instanceof Error ? e.message : 'Failed to fetch checker list' }
  }

  const results = await Promise.all(
    types.map(async (type): Promise<CheckerStatus> => {
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
    })
  )

  return { results, error: null }
}

export default function App() {
  const [checkers, setCheckers] = useState<CheckerStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  async function fetchUpdates() {
    setLoading(true)
    setError(null)
    setCheckers([])
    const { results, error } = await fetchCheckerData()
    setCheckers(results)
    setLastRefresh(new Date())
    setError(error)
    setLoading(false)
  }

  useEffect(() => {
    fetchCheckerData().then(({ results, error }) => {
      setCheckers(results)
      setLastRefresh(new Date())
      setError(error)
      setLoading(false)
    })
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
          <button className="refresh-btn" onClick={fetchUpdates} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </header>

      <main className="app-main">
        {loading && checkers.length === 0 && (
          <div className="status-message">Loading...</div>
        )}

        {error && (
          <div className="status-message error">
            Could not reach the API: {error}
          </div>
        )}

        {!error && checkers.length > 0 && (
          <div className="card-grid">
            {checkers.map((c) => (
              <UpdateCard key={c.type} checker={c} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
