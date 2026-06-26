import { useState, useEffect } from 'react'
import { actionColor, ACTION_LABELS, fmtCost, fmtConf, fmtTime } from '../lib/utils'

const HEADERS = ['Case ID', 'Action', 'Driver', 'Confidence', 'Cost', 'Time', 'Status']

export default function PipelineView({ apiBase }) {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(false)
  const [lastFetch, setLastFetch] = useState(null)

  async function fetchRuns() {
    setLoading(true)
    try {
      const res = await fetch(`${apiBase}/runs?limit=20`)
      if (res.ok) { setRuns(await res.json()); setLastFetch(new Date()) }
    } catch (_) {}
    setLoading(false)
  }

  useEffect(() => {
    fetchRuns()
    const id = setInterval(fetchRuns, 30000)
    return () => clearInterval(id)
  }, [])

  return (
    <div style={{ padding: 32 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Recent Runs
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {lastFetch && (
            <span style={{ fontSize: 11, color: '#374151', fontFamily: '"JetBrains Mono", monospace' }}>
              {lastFetch.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          )}
          <button
            onClick={fetchRuns}
            disabled={loading}
            style={{
              background: 'none', border: '1px solid #1E2A3A', color: '#64748B',
              padding: '4px 12px', fontSize: 11, cursor: 'pointer', borderRadius: 3,
              fontFamily: 'Inter, sans-serif',
            }}
          >
            {loading ? '…' : 'Refresh'}
          </button>
        </div>
      </div>

      {runs.length === 0 ? (
        <div style={{ color: '#64748B', fontSize: 13 }}>No runs yet.</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1E2A3A' }}>
                {HEADERS.map(h => (
                  <th key={h} style={{
                    textAlign: 'left', padding: '8px 12px', color: '#64748B',
                    fontWeight: 600, fontSize: 11, textTransform: 'uppercase',
                    letterSpacing: '0.07em', whiteSpace: 'nowrap',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {runs.map((r, i) => {
                const color = actionColor(r.action)
                const reviewed = r.confirmed_action != null
                return (
                  <tr key={r.run_id || i} style={{ borderBottom: '1px solid #1E2A3A' }}>
                    <td style={{ padding: '10px 12px', fontFamily: '"JetBrains Mono", monospace', color: '#94A3B8', fontSize: 12, whiteSpace: 'nowrap' }}>
                      {r.case_id || '—'}
                    </td>
                    <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                      <span style={{
                        color, fontFamily: '"JetBrains Mono", monospace', fontWeight: 700,
                        fontSize: 11, textTransform: 'uppercase',
                        padding: '2px 6px', border: `1px solid ${color}`, borderRadius: 2,
                      }}>
                        {ACTION_LABELS[r.action] || r.action || '—'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#E2E8F0' }}>{r.driver_type || '—'}</td>
                    <td style={{ padding: '10px 12px', fontFamily: '"JetBrains Mono", monospace', color: '#E2E8F0', whiteSpace: 'nowrap' }}>
                      {fmtConf(r.confidence)}
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: '"JetBrains Mono", monospace', color: '#E2E8F0', whiteSpace: 'nowrap' }}>
                      {fmtCost(r.cost_usd)}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#64748B', fontSize: 12, whiteSpace: 'nowrap' }}>
                      {fmtTime(r.created_at)}
                    </td>
                    <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                      <span style={{
                        fontSize: 11, fontWeight: 600,
                        color: reviewed ? '#10B981' : '#64748B',
                        background: reviewed ? '#052e16' : '#1E2A3A',
                        padding: '2px 8px', borderRadius: 3,
                      }}>
                        {reviewed ? 'Reviewed' : 'Pending'}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
