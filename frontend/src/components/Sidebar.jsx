const NAV = [
  { id: 'chat', label: 'Chat' },
  { id: 'pipeline', label: 'Pipeline' },
]

export default function Sidebar({ view, onNavigate }) {
  return (
    <nav style={{
      width: 160,
      flexShrink: 0,
      background: '#111827',
      borderRight: '1px solid #1E2A3A',
      padding: '24px 0',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{
        fontSize: 10,
        fontWeight: 700,
        color: '#64748B',
        textTransform: 'uppercase',
        letterSpacing: '0.12em',
        padding: '0 16px',
        marginBottom: 16,
        fontFamily: '"JetBrains Mono", monospace',
      }}>
        FP&amp;A Agent
      </div>

      {NAV.map(({ id, label }) => (
        <button
          key={id}
          onClick={() => onNavigate(id)}
          style={{
            background: view === id ? '#1E2A3A' : 'none',
            border: 'none',
            borderLeft: view === id ? '2px solid #3B82F6' : '2px solid transparent',
            color: view === id ? '#E2E8F0' : '#64748B',
            padding: '9px 16px',
            textAlign: 'left',
            fontSize: 14,
            fontWeight: view === id ? 600 : 400,
            cursor: 'pointer',
            fontFamily: 'Inter, sans-serif',
          }}
        >
          {label}
        </button>
      ))}
    </nav>
  )
}
