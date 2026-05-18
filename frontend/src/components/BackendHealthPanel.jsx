import React, { useState, useEffect } from 'react'
import { getAnalystHealth, getAgentsStatus } from '../services/api'

const ServerIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
    <line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>
  </svg>
)

const RefreshIcon = ({ spinning }) => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    style={{ animation: spinning ? 'spin 1s linear infinite' : 'none' }}>
    <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
)

const CheckIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

const XIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
)

function HealthRow({ label, ok, value }) {
  return (
    <div className="flex items-center justify-between py-2"
      style={{ borderBottom: '1px solid rgba(100,116,139,0.08)' }}>
      <span className="text-xs text-slate-500">{label}</span>
      <div className="flex items-center gap-1.5">
        {value && <span className="text-xs font-mono text-slate-400">{value}</span>}
        <span className={`w-4 h-4 rounded-full flex items-center justify-center ${ok ? 'text-emerald-400' : 'text-red-400'}`}
          style={{ background: ok ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)' }}>
          {ok ? <CheckIcon /> : <XIcon />}
        </span>
      </div>
    </div>
  )
}

export default function BackendHealthPanel({ backendStatus }) {
  const [health, setHealth]       = useState(null)
  const [agents, setAgents]       = useState(null)
  const [loading, setLoading]     = useState(false)
  const [lastChecked, setLastChecked] = useState(null)
  const [open, setOpen]           = useState(false)

  const isLive = backendStatus === 'connected'

  const refresh = async () => {
    if (!isLive) return
    setLoading(true)
    try {
      const [hRes, aRes] = await Promise.allSettled([getAnalystHealth(), getAgentsStatus()])
      if (hRes.status === 'fulfilled') setHealth(hRes.value.data)
      if (aRes.status === 'fulfilled') setAgents(aRes.value.data)
      setLastChecked(new Date().toLocaleTimeString('en-US', { hour12: false }))
    } catch (_) {}
    setLoading(false)
  }

  // Auto-refresh every 30 seconds when backend is live
  useEffect(() => {
    if (!isLive) return
    refresh()
    const id = setInterval(refresh, 30000)
    return () => clearInterval(id)
  }, [isLive])

  return (
    <div className="glass-card overflow-hidden">
      {/* Header — clickable toggle */}
      <button
        id="health-panel-toggle"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-3.5 transition-colors hover:bg-white/[0.02]"
        style={{ borderBottom: open ? '1px solid rgba(100,116,139,0.12)' : 'none' }}>
        <div className="flex items-center gap-2">
          <span style={{ color: isLive ? '#10b981' : '#64748b' }}><ServerIcon /></span>
          <span className="text-sm font-semibold text-slate-300">Backend Health</span>
        </div>
        <div className="flex items-center gap-3">
          {lastChecked && <span className="text-xs font-mono text-slate-600">checked {lastChecked}</span>}
          <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-400' : 'bg-slate-600'}`}
            style={{ animation: isLive ? 'pulse 2s infinite' : 'none' }} />
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </button>

      {/* Expandable body */}
      {open && (
        <div className="px-5 pb-4 animate-fade-in">
          {!isLive ? (
            <div className="py-6 text-center">
              <p className="text-sm text-slate-500">Backend is offline</p>
              <p className="text-xs text-slate-600 mt-1">Start the FastAPI server on port 8000</p>
              <code className="text-xs font-mono text-amber-400/70 block mt-2">uvicorn backend.main:app --reload</code>
            </div>
          ) : (
            <>
              <div className="mt-3">
                {/* Analyst health */}
                <p className="text-xs text-slate-500 uppercase tracking-widest mb-2 font-semibold">Analyst Agent</p>
                <HealthRow label="Status"          ok={health?.status === 'ready'}   value={health?.status || '—'} />
                <HealthRow label="LLM Model"       ok={!!health?.model}              value={health?.model || '—'} />
                <HealthRow label="Retriever Ready" ok={health?.retriever_ready}      />

                {/* Agent status */}
                {agents && (
                  <>
                    <p className="text-xs text-slate-500 uppercase tracking-widest mb-2 mt-4 font-semibold">Agent Pool</p>
                    {Object.entries(agents).map(([key, val]) => (
                      <HealthRow key={key} label={key.replace('_', ' ')} ok={val !== 'error'} value={val} />
                    ))}
                  </>
                )}

                {/* Endpoints list */}
                {health?.endpoints && (
                  <>
                    <p className="text-xs text-slate-500 uppercase tracking-widest mb-2 mt-4 font-semibold">Active Endpoints</p>
                    <div className="space-y-1">
                      {health.endpoints.map(ep => (
                        <div key={ep} className="text-xs font-mono text-slate-500 px-2 py-1 rounded"
                          style={{ background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.08)' }}>
                          {ep}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>

              <button
                id="health-refresh-btn"
                onClick={refresh}
                disabled={loading}
                className="mt-4 w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium text-slate-400
                  hover:text-cyan-400 transition-colors"
                style={{ border: '1px solid rgba(100,116,139,0.15)' }}>
                <RefreshIcon spinning={loading} />
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            </>
          )}
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .5; } }
      `}</style>
    </div>
  )
}
