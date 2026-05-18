import React, { useState } from 'react'
import { analyzeFromJira } from '../services/api'

const JiraIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="5" width="20" height="14" rx="2"/>
    <path d="M16 2v6M8 2v6M2 10h20"/>
  </svg>
)

const SpinIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"
    style={{ animation: 'spin 0.8s linear infinite' }}>
    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
  </svg>
)

export default function JiraFetchBar({ onFetched, backendStatus, onLog }) {
  const [ticketId, setTicketId] = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [success, setSuccess]   = useState(false)

  const isLive = backendStatus === 'connected'

  const handleFetch = async () => {
    if (!ticketId.trim()) return
    setLoading(true)
    setError(null)
    setSuccess(false)
    onLog?.(`Fetching ticket "${ticketId.trim()}" from Jira...`, 'agent')

    try {
      const res  = await analyzeFromJira(ticketId.trim())
      const data = res.data

      // Build ticket object from response
      const fetched = {
        ticket_id:   data.ticket_id   || ticketId,
        title:       data.title       || data.summary     || `Ticket ${ticketId}`,
        description: data.description || data.raw_response || '',
        priority:    data.priority    || 'Medium',
        issue_type:  data.issue_type  || 'Task',
        status:      data.status      || 'Open',
        assignee:    data.assignee    || 'Unassigned',
      }

      onFetched?.(fetched, data)
      setSuccess(true)
      onLog?.(`Ticket "${ticketId.trim()}" fetched and loaded successfully.`, 'success')
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError(err.message)
      onLog?.(`Jira fetch failed: ${err.message}`, 'error')
    }
    setLoading(false)
  }

  return (
    <div className="glass-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-cyan-400"><JiraIcon /></span>
        <span className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Fetch from Jira</span>
        {!isLive && (
          <span className="ml-auto text-xs text-slate-600 font-mono">Backend offline</span>
        )}
      </div>

      <div className="flex gap-2">
        <input
          id="jira-fetch-input"
          type="text"
          value={ticketId}
          onChange={e => setTicketId(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && isLive && !loading && handleFetch()}
          placeholder="e.g. PROJ-101"
          disabled={!isLive || loading}
          className="flex-1 px-3 py-2 rounded-lg text-sm font-mono focus:outline-none transition-all"
          style={{
            background:  isLive ? 'rgba(30,41,59,0.8)' : 'rgba(15,23,42,0.5)',
            border:      `1px solid ${success ? 'rgba(16,185,129,0.4)' : error ? 'rgba(239,68,68,0.3)' : 'rgba(100,116,139,0.2)'}`,
            color:       '#e2e8f0',
            opacity:     !isLive ? 0.5 : 1,
          }}
        />
        <button
          id="jira-fetch-btn"
          onClick={handleFetch}
          disabled={!isLive || loading || !ticketId.trim()}
          className="px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all"
          style={{
            background: isLive && !loading ? 'linear-gradient(135deg, #06b6d4, #6366f1)' : 'rgba(100,116,139,0.15)',
            color:      isLive && !loading ? '#fff' : '#64748b',
            cursor:     !isLive || loading ? 'not-allowed' : 'pointer',
          }}>
          {loading ? <SpinIcon /> : (
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
          )}
          {loading ? 'Fetching' : 'Fetch'}
        </button>
      </div>

      {error && (
        <p className="mt-2 text-xs text-red-400 font-mono">{error}</p>
      )}
      {success && (
        <p className="mt-2 text-xs text-emerald-400 font-mono animate-fade-in">
          Ticket loaded into form successfully
        </p>
      )}
      {!isLive && (
        <p className="mt-2 text-xs text-slate-600">
          Start the backend to fetch real Jira tickets
        </p>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      `}</style>
    </div>
  )
}
