import { actionColor, ACTION_LABELS, fmtCost, fmtConf, fmtMag } from '../lib/utils'

export default function ResultCard({ data }) {
  const color = actionColor(data.action)
  const txIds = data.grounding?.transaction_ids
  const txStr = Array.isArray(txIds) && txIds.length > 0 ? txIds.join(', ') : 'none cited'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{
        fontFamily: '"JetBrains Mono", monospace',
        fontSize: 56,
        fontWeight: 700,
        textTransform: 'uppercase',
        lineHeight: 1,
        padding: '10px 18px',
        display: 'inline-block',
        border: `2px solid ${color}`,
        borderRadius: 0,
        color,
      }}>
        {ACTION_LABELS[data.action] || (data.action && data.action.toUpperCase()) || '—'}
      </div>

      <Row label="Driver" value={data.driver_type} />
      <Row label="Confidence" value={fmtConf(data.confidence)} mono />
      <Row label="Magnitude" value={fmtMag(data.magnitude)} mono />
      <div>
        <FieldLabel>Description</FieldLabel>
        <div style={{ fontSize: 14, color: '#E2E8F0', lineHeight: 1.6, marginTop: 3 }}>
          {data.description || '—'}
        </div>
      </div>
      <Row label="Grounding IDs" value={txStr} mono />
      <div style={{ display: 'flex', gap: 32 }}>
        <Row label="Cost" value={fmtCost(data.cost_usd)} mono />
        <Row label="LLM Calls" value={data.llm_calls ?? '—'} mono />
      </div>
      <Row label="Run ID" value={data.run_id || '—'} mono muted />
    </div>
  )
}

function FieldLabel({ children }) {
  return (
    <div style={{ fontSize: 10, fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
      {children}
    </div>
  )
}

function Row({ label, value, mono, muted }) {
  return (
    <div>
      <FieldLabel>{label}</FieldLabel>
      <div style={{
        marginTop: 3,
        fontSize: mono ? 13 : 14,
        fontFamily: mono ? '"JetBrains Mono", monospace' : 'Inter, sans-serif',
        color: muted ? '#64748B' : '#E2E8F0',
      }}>
        {value ?? '—'}
      </div>
    </div>
  )
}
