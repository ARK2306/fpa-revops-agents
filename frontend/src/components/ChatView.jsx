import { useRef, useEffect, createContext, useContext } from 'react'
import ReactMarkdown from 'react-markdown'
import SetupForm from './SetupForm'
import ResultCard from './ResultCard'

// Lets the code component know it's inside a <pre> (block code, not inline)
const InPre = createContext(false)

const mdComponents = {
  p:          ({ children }) => <p style={{ margin: '0 0 0.75rem 0', lineHeight: 1.6 }}>{children}</p>,
  strong:     ({ children }) => <strong style={{ color: '#E2E8F0', fontWeight: 600 }}>{children}</strong>,
  em:         ({ children }) => <em style={{ color: '#94A3B8' }}>{children}</em>,
  h1:         ({ children }) => <h1 style={{ color: '#E2E8F0', fontSize: 16, fontWeight: 700, margin: '1rem 0 0.4rem' }}>{children}</h1>,
  h2:         ({ children }) => <h2 style={{ color: '#E2E8F0', fontSize: 15, fontWeight: 700, margin: '1rem 0 0.4rem' }}>{children}</h2>,
  h3:         ({ children }) => <h3 style={{ color: '#E2E8F0', fontSize: 14, fontWeight: 600, margin: '1rem 0 0.4rem' }}>{children}</h3>,
  h4:         ({ children }) => <h4 style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 600, margin: '1rem 0 0.4rem' }}>{children}</h4>,
  ul:         ({ children }) => <ul style={{ paddingLeft: 20, margin: '0 0 0.75rem 0' }}>{children}</ul>,
  ol:         ({ children }) => <ol style={{ paddingLeft: 20, margin: '0 0 0.75rem 0' }}>{children}</ol>,
  li:         ({ children }) => <li style={{ color: '#E2E8F0', marginBottom: 3, lineHeight: 1.5 }}>{children}</li>,
  blockquote: ({ children }) => <blockquote style={{ borderLeft: '3px solid #1E2A3A', paddingLeft: 12, margin: '0 0 0.75rem 0', color: '#64748B' }}>{children}</blockquote>,
  hr:         ()             => <hr style={{ border: 'none', borderTop: '1px solid #1E2A3A', margin: '0.75rem 0' }} />,
  a:          ({ href, children }) => <a href={href} style={{ color: '#60A5FA', textDecoration: 'underline' }} target="_blank" rel="noopener noreferrer">{children}</a>,
  pre:        ({ children }) => (
    <InPre.Provider value={true}>
      <pre style={{ background: '#1E2A3A', padding: '10px 14px', borderRadius: 4, overflow: 'auto', margin: '0 0 0.75rem 0', lineHeight: 1.5 }}>
        {children}
      </pre>
    </InPre.Provider>
  ),
  code: ({ children, className }) => {
    const inPre = useContext(InPre)
    return (
      <code className={className} style={{
        fontFamily: '"JetBrains Mono", monospace',
        fontSize: 12,
        color: '#E2E8F0',
        ...(inPre ? {} : { background: '#1E2A3A', padding: '2px 5px', borderRadius: 3 }),
      }}>
        {children}
      </code>
    )
  },
  table:  ({ children }) => <table style={{ width: '100%', borderCollapse: 'collapse', margin: '0 0 0.75rem 0', fontSize: 13 }}>{children}</table>,
  thead:  ({ children }) => <thead style={{ background: '#1a2235' }}>{children}</thead>,
  tr:     ({ children }) => <tr>{children}</tr>,
  th:     ({ children }) => <th style={{ border: '1px solid #1E2A3A', padding: '6px 10px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{children}</th>,
  td:     ({ children }) => <td style={{ border: '1px solid #1E2A3A', padding: '6px 10px', fontFamily: '"JetBrains Mono", monospace', color: '#E2E8F0' }}>{children}</td>,
}

function Bubble({ children, user }) {
  return (
    <div style={{
      background: user ? '#3B4FBF' : '#111827',
      border: user ? 'none' : '1px solid #1E2A3A',
      borderRadius: 6,
      padding: '12px 16px',
      fontSize: 14,
      color: '#E2E8F0',
      lineHeight: 1.6,
    }}>
      {children}
    </div>
  )
}

function LoadingBubble({ text }) {
  return (
    <div style={{ alignSelf: 'flex-start' }}>
      <Bubble>
        <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 13, color: '#64748B' }}>
          {text}
          <span style={{ animation: 'pulse-dot 1.2s ease-in-out infinite' }}>...</span>
        </span>
      </Bubble>
    </div>
  )
}

// Presentational — all state and handlers come from App.jsx
export default function ChatView({ phase, messages, input, sending, onStart, onSend, onInputChange, deepDive, onDeepDiveChange }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, phase])

  if (phase === 'setup') {
    return (
      <div style={{ padding: 40, maxWidth: 520 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 24 }}>
          New Analysis
        </div>
        <SetupForm onStart={onStart} />
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {messages.map((msg, i) => {
          if (msg.role === 'user') {
            return (
              <div key={i} style={{ alignSelf: 'flex-end', maxWidth: '60%' }}>
                <Bubble user>{msg.content}</Bubble>
              </div>
            )
          }
          if (msg.type === 'agent_output') {
            return (
              <div key={i} style={{ alignSelf: 'flex-start', maxWidth: '85%' }}>
                <Bubble><ResultCard data={msg.data} /></Bubble>
              </div>
            )
          }
          if (msg.type === 'chat_reply') {
            const text = msg.data?.message || msg.data?.content || msg.content || ''
            return (
              <div key={i} style={{ alignSelf: 'flex-start', maxWidth: '70%' }}>
                <Bubble>
                  <ReactMarkdown components={mdComponents}>{text}</ReactMarkdown>
                </Bubble>
              </div>
            )
          }
          if (msg.type === 'error') {
            return (
              <div key={i} style={{ alignSelf: 'flex-start', maxWidth: '70%' }}>
                <div style={{ padding: '10px 14px', background: '#1A0A0A', border: '1px solid #7F1D1D', borderRadius: 6, color: '#FCA5A5', fontSize: 13 }}>
                  {msg.content}
                </div>
              </div>
            )
          }
          return null
        })}

        {phase === 'loading' && <LoadingBubble text="Analyzing" />}
        {sending && <LoadingBubble text="Thinking" />}
        <div ref={bottomRef} />
      </div>

      {phase === 'chatting' && (
        <div style={{ padding: '14px 32px', borderTop: '1px solid #1E2A3A' }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              value={input}
              onChange={e => onInputChange(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSend() } }}
              placeholder="Ask a follow-up question…"
              style={{
                flex: 1,
                background: '#111827',
                border: '1px solid #1E2A3A',
                color: '#E2E8F0',
                padding: '10px 14px',
                fontSize: 14,
                borderRadius: 4,
                fontFamily: 'Inter, sans-serif',
              }}
            />
            <button
              onClick={onSend}
              disabled={sending || !input.trim()}
              style={{
                background: sending || !input.trim() ? '#1E2A3A' : '#1D4ED8',
                border: 'none',
                color: sending || !input.trim() ? '#64748B' : '#E2E8F0',
                padding: '10px 20px',
                fontSize: 13,
                fontWeight: 600,
                cursor: sending || !input.trim() ? 'not-allowed' : 'pointer',
                borderRadius: 4,
                fontFamily: 'Inter, sans-serif',
              }}
            >
              Send
            </button>
          </div>
          <div
            onClick={() => onDeepDiveChange(!deepDive)}
            style={{ display: 'flex', alignItems: 'center', gap: 7, marginTop: 10, cursor: 'pointer', userSelect: 'none', width: 'fit-content' }}
          >
            <div style={{
              width: 13, height: 13, flexShrink: 0, borderRadius: 2,
              border: `1.5px solid ${deepDive ? '#3B4FBF' : '#1E2A3A'}`,
              background: deepDive ? '#3B4FBF' : 'transparent',
              boxShadow: deepDive ? '0 0 7px rgba(59,79,191,0.55)' : 'none',
            }} />
            <span style={{ fontSize: 12, color: '#64748B', fontFamily: 'Inter, sans-serif' }}>Deep Dive</span>
            <span style={{ fontSize: 11, color: '#475569', fontFamily: 'Inter, sans-serif' }}>query live data</span>
          </div>
        </div>
      )}
    </div>
  )
}
