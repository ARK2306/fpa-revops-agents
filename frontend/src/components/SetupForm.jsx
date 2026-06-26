import { useState, useRef } from 'react'

const REQUIRED_FIELDS = ['transaction_id', 'account_id', 'period', 'date', 'amount', 'description']
const OPTIONAL_FIELDS = new Set(['period'])
const FIELD_LABELS = {
  transaction_id: 'Transaction ID',
  account_id: 'Account ID',
  period: 'Period',
  date: 'Date',
  amount: 'Amount',
  description: 'Description',
}

function getSample(column, rows) {
  for (const row of rows) {
    const val = row[column]
    if (val !== undefined && val !== null && val !== '') return String(val)
  }
  return null
}

function fmtSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const inputStyle = {
  width: '100%',
  background: '#0A0F1E',
  border: '1px solid #1E2A3A',
  color: '#E2E8F0',
  padding: '8px 12px',
  fontSize: 14,
  borderRadius: 4,
  fontFamily: 'Inter, sans-serif',
}

function FieldLabel({ children }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
      {children}
    </div>
  )
}

export default function SetupForm({ onStart }) {
  const [accountId, setAccountId] = useState('')
  const [period, setPeriod] = useState('')
  const [budget, setBudget] = useState('')
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [csvHeaders, setCsvHeaders] = useState([])
  const [csvRows, setCsvRows] = useState([])
  const [mapping, setMapping] = useState(Object.fromEntries(REQUIRED_FIELDS.map(f => [f, ''])))
  const fileInputRef = useRef(null)

  function processFile(f) {
    setFile(f)
    window.Papa.parse(f, {
      header: true,
      preview: 5,
      complete: ({ meta, data }) => {
        const headers = meta.fields || []
        setCsvHeaders(headers)
        setCsvRows(data)
        const auto = {}
        REQUIRED_FIELDS.forEach(field => {
          const match = headers.find(h => h.toLowerCase() === field.toLowerCase())
          if (match) auto[field] = match
        })
        setMapping(m => ({ ...m, ...auto }))
      },
    })
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f && f.name.toLowerCase().endsWith('.csv')) processFile(f)
  }

  function removeFile(e) {
    e.stopPropagation()
    setFile(null)
    setCsvHeaders([])
    setCsvRows([])
    setMapping(Object.fromEntries(REQUIRED_FIELDS.map(f => [f, ''])))
    fileInputRef.current.value = ''
  }

  const canSubmit =
    accountId.trim() && period.trim() && budget !== '' && file !== null &&
    REQUIRED_FIELDS.every(f => OPTIONAL_FIELDS.has(f) || mapping[f] !== '')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      <div>
        <FieldLabel>Account ID</FieldLabel>
        <input style={inputStyle} type="text" placeholder="e.g. ACC-001"
          value={accountId} onChange={e => setAccountId(e.target.value)} />
      </div>
      <div>
        <FieldLabel>Period</FieldLabel>
        <input style={inputStyle} type="text" placeholder="2024-01"
          value={period} onChange={e => setPeriod(e.target.value)} />
      </div>
      <div>
        <FieldLabel>Budget ($)</FieldLabel>
        <input style={{ ...inputStyle, fontFamily: '"JetBrains Mono", monospace' }} type="number" placeholder="e.g. 50000"
          value={budget} onChange={e => setBudget(e.target.value)} />
      </div>

      {/* Drag-and-drop zone */}
      <div>
        <FieldLabel>GL Export CSV</FieldLabel>
        <div
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => !file && fileInputRef.current.click()}
          style={{
            border: `2px dashed ${dragging ? '#3B82F6' : '#1E2A3A'}`,
            borderRadius: 8,
            padding: '28px 20px',
            textAlign: 'center',
            cursor: file ? 'default' : 'pointer',
            background: dragging ? 'rgba(59,130,246,0.04)' : 'transparent',
          }}
        >
          {file ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
              <span style={{ fontSize: 13, color: '#E2E8F0', fontFamily: '"JetBrains Mono", monospace' }}>
                {file.name}
              </span>
              <span style={{ fontSize: 12, color: '#64748B', fontFamily: '"JetBrains Mono", monospace' }}>
                {fmtSize(file.size)}
              </span>
              <button
                onClick={removeFile}
                title="Remove"
                style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', fontSize: 18, lineHeight: 1, padding: '0 2px' }}
              >
                ×
              </button>
            </div>
          ) : (
            <span style={{ fontSize: 13, color: '#64748B' }}>
              Drop your GL export CSV here, or click to browse
            </span>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            style={{ display: 'none' }}
            onChange={e => { const f = e.target.files[0]; if (f) processFile(f) }}
          />
        </div>
      </div>

      {/* Column mapping — rendered inline once headers are parsed */}
      {csvHeaders.length > 0 && (
        <div>
          <div style={{ fontSize: 10, fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 14 }}>
            Map Your Columns
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {REQUIRED_FIELDS.map(field => {
              const selected = mapping[field]
              const sample = selected ? getSample(selected, csvRows) : null
              return (
                <div key={field} style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                  <div style={{ width: 128, flexShrink: 0, paddingTop: 9, fontSize: 13, color: '#94A3B8' }}>
                    {FIELD_LABELS[field]}
                  </div>
                  <div style={{ flex: 1 }}>
                    <select
                      value={selected}
                      onChange={e => setMapping(m => ({ ...m, [field]: e.target.value }))}
                      style={{ ...inputStyle, cursor: 'pointer' }}
                    >
                      <option value="">— select column —</option>
                      {csvHeaders.map(h => <option key={h} value={h}>{h}</option>)}
                    </select>
                    {sample && (
                      <div style={{
                        fontSize: 11, color: '#64748B', marginTop: 3,
                        fontFamily: '"JetBrains Mono", monospace',
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>
                        {sample}
                      </div>
                    )}
                    {OPTIONAL_FIELDS.has(field) && (
                      <div style={{ fontSize: 11, color: '#475569', marginTop: 3, fontStyle: 'italic' }}>
                        Leave blank to auto-derive from date column
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      <button
        disabled={!canSubmit}
        onClick={() => {
          const filteredMapping = Object.fromEntries(
            Object.entries(mapping).filter(([k, v]) => !OPTIONAL_FIELDS.has(k) || v !== '')
          )
          onStart({ accountId, period, budget }, file, filteredMapping)
        }}
        style={{
          width: '100%',
          marginTop: 4,
          background: canSubmit ? '#1D4ED8' : '#1E2A3A',
          border: 'none',
          color: canSubmit ? '#E2E8F0' : '#64748B',
          padding: '10px 24px',
          fontSize: 13,
          fontWeight: 600,
          cursor: canSubmit ? 'pointer' : 'not-allowed',
          borderRadius: 4,
          fontFamily: 'Inter, sans-serif',
        }}
      >
        Start Analysis
      </button>
    </div>
  )
}
