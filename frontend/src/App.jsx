// CORS: FastAPI must allow http://localhost:3000

import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatView from './components/ChatView'
import PipelineView from './components/PipelineView'

const API_BASE = 'https://fpa-api-182571398865.us-central1.run.app'

export default function App() {
  const [view, setView] = useState('chat')

  // Chat session state — lives here so navigation never resets it
  const [sessionId] = useState(() => crypto.randomUUID())
  const [messages, setMessages] = useState([])
  const [phase, setPhase] = useState('setup')   // 'setup' | 'loading' | 'chatting'
  const [sending, setSending] = useState(false)
  const [input, setInput] = useState('')
  const [deepDive, setDeepDive] = useState(false)

  async function handleStart(formData, file, mapping) {
    setPhase('loading')
    const fd = new FormData()
    fd.append('session_id', sessionId)
    fd.append('message', 'start')
    fd.append('account_id', formData.accountId)
    fd.append('period', formData.period)
    fd.append('budget', String(formData.budget))
    fd.append('file', file)
    fd.append('column_mapping', JSON.stringify(mapping))

    try {
      const res = await fetch(`${API_BASE}/chat`, { method: 'POST', body: fd })
      const data = await res.json()
      console.log('chat /start response:', data)
      if (!res.ok) throw new Error(data.detail || `Error ${res.status}`)
      setMessages([{ role: 'assistant', type: data.type, data: data.data }])
    } catch (err) {
      setMessages([{ role: 'assistant', type: 'error', content: err.message }])
    }
    setPhase('chatting')
  }

  async function handleSend() {
    if (!input.trim() || sending) return
    const text = input.trim()
    setInput('')
    setSending(true)
    setMessages(m => [...m, { role: 'user', type: 'text', content: text }])

    const fd = new FormData()
    fd.append('session_id', sessionId)
    fd.append('message', text)
    fd.append('deep_dive', deepDive ? 'true' : 'false')

    try {
      const res = await fetch(`${API_BASE}/chat`, { method: 'POST', body: fd })
      const data = await res.json()
      console.log('chat /followup response:', data)
      if (!res.ok) throw new Error(data.detail || `Error ${res.status}`)
      setMessages(m => [...m, { role: 'assistant', type: data.type, data: data.data }])
    } catch (err) {
      setMessages(m => [...m, { role: 'assistant', type: 'error', content: err.message }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar view={view} onNavigate={setView} />
      <main style={{ flex: 1, overflow: 'auto' }}>
        {/* Both panels stay mounted; only one is visible at a time */}
        <div style={{ display: view === 'chat' ? 'block' : 'none', height: '100%' }}>
          <ChatView
            phase={phase}
            messages={messages}
            input={input}
            sending={sending}
            onStart={handleStart}
            onSend={handleSend}
            onInputChange={setInput}
            deepDive={deepDive}
            onDeepDiveChange={setDeepDive}
          />
        </div>
        <div style={{ display: view === 'pipeline' ? 'block' : 'none', height: '100%' }}>
          <PipelineView apiBase={API_BASE} />
        </div>
      </main>
    </div>
  )
}
