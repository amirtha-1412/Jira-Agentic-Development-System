import React, { useEffect, useRef } from 'react'

const levelConfig = {
  info:    { color: '#94a3b8', prefix: 'INFO ', icon: '·' },
  success: { color: '#10b981', prefix: 'DONE ', icon: '✔' },
  error:   { color: '#ef4444', prefix: 'ERR  ', icon: '✘' },
  warn:    { color: '#f59e0b', prefix: 'WARN ', icon: '!' },
  agent:   { color: '#06b6d4', prefix: 'AGNT ', icon: '>' },
  system:  { color: '#818cf8', prefix: 'SYS  ', icon: '#' },
}

function LogLine({ log, index }) {
  const lvl = levelConfig[log.level] || levelConfig.info
  return (
    <div
      className="log-line flex items-start gap-3 px-3 py-0.5 rounded hover:bg-white/[0.02] transition-colors"
      style={{ animationDelay: `${index * 20}ms`, animation: 'fadeIn 0.3s ease-out forwards', opacity: 0 }}
    >
      <span className="text-slate-600 select-none shrink-0 font-mono text-[11px] pt-0.5 w-16 text-right">
        {log.time || '--:--:--'}
      </span>
      <span className="shrink-0 text-[11px] font-bold pt-0.5 w-12" style={{ color: lvl.color }}>
        {lvl.prefix}
      </span>
      <span className="shrink-0 pt-0.5">{lvl.icon}</span>
      <span style={{ color: lvl.color }} className="leading-relaxed break-all">
        {log.message}
      </span>
    </div>
  )
}

const TerminalIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>
  </svg>
)

export default function LogsPanel({ logs = [] }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const isEmpty = logs.length === 0

  return (
    <div className="glass-card flex flex-col h-full" style={{ minHeight: '320px' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 shrink-0"
        style={{ borderBottom: '1px solid rgba(100,116,139,0.15)' }}>
        <div className="flex items-center gap-2 text-cyan-400">
          <TerminalIcon />
          <span className="text-sm font-semibold uppercase tracking-wider">Reasoning Logs</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500 font-mono">{logs.length} entries</span>
          {/* Traffic lights */}
          <div className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
            <span className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
          </div>
        </div>
      </div>

      {/* Log body */}
      <div className="flex-1 overflow-y-auto py-3"
        style={{
          background: 'rgba(9,14,26,0.7)',
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          maxHeight: '320px',
        }}>
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full py-12 text-slate-600">
            <div className="w-8 h-8 rounded-lg mb-3 flex items-center justify-center" style={{ border: '1px solid #334155' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
            </div>
            <p className="text-sm font-mono">Waiting for agent execution...</p>
            <p className="text-xs mt-1 text-slate-700">Logs will stream here in real time</p>
          </div>
        ) : (
          <>
            {logs.map((log, i) => (
              <LogLine key={i} log={log} index={i} />
            ))}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Footer cursor blink */}
      <div className="px-5 py-2 shrink-0 flex items-center gap-2"
        style={{ borderTop: '1px solid rgba(100,116,139,0.1)', background: 'rgba(9,14,26,0.5)' }}>
        <span className="text-cyan-400 font-mono text-xs">$</span>
        <span className="w-2 h-4 bg-cyan-400 rounded-sm"
          style={{ animation: 'pulse 1s step-end infinite' }} />
      </div>
    </div>
  )
}
