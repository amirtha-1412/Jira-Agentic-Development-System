import React from 'react'

const agentMeta = {
  requirement_agent: {
    label: 'Requirement Analyst',
    color: '#06b6d4',
    desc:  'Parses Jira ticket into structured requirements',
    Icon: () => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/>
        <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/>
      </svg>
    ),
  },
  developer_agent: {
    label: 'Developer Agent',
    color: '#818cf8',
    desc:  'Generates repository-aware implementation code',
    Icon: () => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
      </svg>
    ),
  },
  qa_agent: {
    label: 'QA Agent',
    color: '#10b981',
    desc:  'Writes and validates test cases for the solution',
    Icon: () => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v11m0 0h10m-10 0a2 2 0 0 1-2 2H3m16-2a2 2 0 0 0 2-2V3"/>
        <polyline points="9 11 12 14 22 4"/>
      </svg>
    ),
  },
  pr_agent: {
    label: 'PR Generator',
    color: '#f59e0b',
    desc:  'Drafts pull request with description and diff',
    Icon: () => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>
      </svg>
    ),
  },
}

const statusMeta = {
  idle:    { label: 'Idle',    bg: 'rgba(100,116,139,0.12)', text: '#94a3b8', dot: '#64748b' },
  running: { label: 'Running', bg: 'rgba(245,158,11,0.12)',  text: '#f59e0b', dot: '#f59e0b' },
  done:    { label: 'Done',    bg: 'rgba(16,185,129,0.12)',  text: '#10b981', dot: '#10b981' },
  error:   { label: 'Error',   bg: 'rgba(239,68,68,0.12)',   text: '#ef4444', dot: '#ef4444' },
}

const CheckIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

const SpinnerIcon = ({ color }) => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round"
    style={{ animation: 'spin 1s linear infinite' }}>
    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
  </svg>
)

export default function AgentStatusCard({ agentKey, status = 'idle', result }) {
  const meta   = agentMeta[agentKey] || agentMeta.requirement_agent
  const sColor = statusMeta[status]  || statusMeta.idle
  const { Icon } = meta
  const isRunning = status === 'running'
  const isDone    = status === 'done'

  return (
    <div className="glass-card-hover p-5 relative overflow-hidden transition-all duration-500"
      style={{
        borderColor: (isRunning || isDone) ? `${meta.color}50` : undefined,
        boxShadow:   isRunning ? `0 0 20px ${meta.color}15` : undefined,
      }}>

      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl transition-all duration-700"
        style={{ background: isDone || isRunning ? `linear-gradient(90deg, transparent, ${meta.color}, transparent)` : 'transparent' }} />

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: `${meta.color}18`, border: `1px solid ${meta.color}30`, color: meta.color }}>
            <Icon />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-100">{meta.label}</p>
            <p className="text-xs text-slate-500 mt-0.5">{meta.desc}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold shrink-0"
          style={{ background: sColor.bg, color: sColor.text }}>
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: sColor.dot, animation: isRunning ? 'pulse 1s infinite' : 'none' }} />
          {isRunning && <SpinnerIcon color={sColor.dot} />}
          {isDone    && <CheckIcon />}
          {sColor.label}
        </div>
      </div>

      {/* Running progress bar */}
      {isRunning && (
        <div className="mt-3 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(100,116,139,0.2)' }}>
          <div className="h-full rounded-full"
            style={{ width: '60%', background: `linear-gradient(90deg, ${meta.color}, transparent)`, animation: 'pulse 1.5s ease-in-out infinite' }} />
        </div>
      )}

      {/* Result preview */}
      {isDone && result && (
        <div className="mt-3 p-3 rounded-lg text-xs font-mono text-slate-400 leading-relaxed"
          style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(100,116,139,0.1)', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {typeof result === 'string' ? result.slice(0, 200) + '…' : JSON.stringify(result).slice(0, 200) + '…'}
        </div>
      )}
    </div>
  )
}
