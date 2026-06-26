export const ACTION_COLORS = {
  flag: '#F59E0B',
  escalate: '#EF4444',
  do_nothing: '#10B981',
}

export const ACTION_LABELS = {
  flag: 'FLAG',
  escalate: 'ESCALATE',
  do_nothing: 'DO NOTHING',
}

export const actionColor = (a) => ACTION_COLORS[a] || '#64748B'

export const fmtCost = (v) => v == null ? '—' : '$' + Number(v).toFixed(4)
export const fmtConf = (v) => v == null ? '—' : Number(v).toFixed(2)
export const fmtMag = (v) =>
  v == null ? '—' : '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
export const fmtTime = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
