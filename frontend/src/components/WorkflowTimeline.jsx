import React from 'react'

const stages = [
  { key: 'ticket',               label: 'Jira Ticket',           desc: 'Ticket received & parsed',                     color: '#06b6d4' },
  { key: 'requirement_analysis', label: 'Requirement Analysis',  desc: 'AI extracts structured requirements',          color: '#818cf8' },
  { key: 'engineering_tasks',    label: 'Engineering Tasks',     desc: 'Breaks down into atomic TASK-N items',         color: '#a78bfa' },
  { key: 'code_generation',      label: 'Code Generation',       desc: 'Developer agent writes implementation',        color: '#06b6d4' },
  { key: 'qa_testing',           label: 'QA & Testing',          desc: 'Test cases generated and validated',           color: '#10b981' },
  { key: 'pr_creation',          label: 'PR Draft',              desc: 'Pull request created with diff',               color: '#f59e0b' },
  { key: 'complete',             label: 'Pipeline Complete',     desc: 'All agents finished successfully',             color: '#10b981' },
]

const stageStatus = {
  pending:   { dot: '#334155', label: 'Pending',  text: '#475569' },
  active:    { dot: '#f59e0b', label: 'Running',  text: '#f59e0b' },
  completed: { dot: '#10b981', label: 'Complete', text: '#10b981' },
  error:     { dot: '#ef4444', label: 'Failed',   text: '#ef4444' },
}

const stageIcons = {
  ticket:               () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M16 2v6M8 2v6M2 10h20"/></svg>,
  requirement_analysis: () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/></svg>,
  engineering_tasks:    () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>,
  code_generation:      () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>,
  qa_testing:           () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>,
  pr_creation:          () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/></svg>,
  complete:             () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>,
}

function TimelineNode({ stage, status, timestamp, isLast }) {
  const s         = stageStatus[status] || stageStatus.pending
  const isActive  = status === 'active'
  const isDone    = status === 'completed'
  const StageIcon = stageIcons[stage.key] || stageIcons.ticket

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center" style={{ width: '28px', flexShrink: 0 }}>
        <div className="relative flex items-center justify-center w-7 h-7 rounded-full shrink-0"
          style={{
            background:  isDone || isActive ? `${stage.color}20` : 'rgba(30,41,59,0.8)',
            border:      `2px solid ${isDone || isActive ? stage.color : '#1e293b'}`,
            color:       isDone || isActive ? stage.color : '#475569',
            transition:  'all 0.4s ease',
            boxShadow:   isActive ? `0 0 12px ${stage.color}60` : undefined,
          }}>
          {isActive && (
            <span className="absolute inset-0 rounded-full"
              style={{ background: `${stage.color}30`, animation: 'ping 1.2s cubic-bezier(0,0,0.2,1) infinite' }} />
          )}
          <span className="z-10"><StageIcon /></span>
        </div>
        {!isLast && (
          <div className="flex-1 w-0.5 mt-1 rounded-full transition-all duration-700"
            style={{ background: isDone ? `linear-gradient(to bottom, ${stage.color}, #1e293b)` : '#1e293b', minHeight: '24px' }} />
        )}
      </div>

      <div className="pb-5 flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div>
            <p className="text-sm font-semibold" style={{ color: isDone || isActive ? '#e2e8f0' : '#475569', transition: 'color 0.4s' }}>
              {stage.label}
            </p>
            <p className="text-xs mt-0.5 text-slate-600">{stage.desc}</p>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.dot, animation: isActive ? 'pulse 1s infinite' : 'none' }} />
            <span className="text-xs font-medium" style={{ color: s.text }}>{s.label}</span>
            {timestamp && <span className="text-xs font-mono text-slate-600 ml-1">{timestamp}</span>}
          </div>
        </div>
      </div>
    </div>
  )
}

const TimelineIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/>
    <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
    <line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>
    <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
  </svg>
)

export default function WorkflowTimeline({ stageStatuses = {}, timestamps = {} }) {
  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-2 text-cyan-400 mb-6">
        <TimelineIcon />
        <span className="text-sm font-semibold uppercase tracking-wider">Workflow Timeline</span>
      </div>
      <div>
        {stages.map((stage, i) => (
          <TimelineNode
            key={stage.key}
            stage={stage}
            status={stageStatuses[stage.key] || 'pending'}
            timestamp={timestamps[stage.key]}
            isLast={i === stages.length - 1}
          />
        ))}
      </div>
    </div>
  )
}
