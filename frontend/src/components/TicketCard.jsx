import React from 'react'

const priorityConfig = {
  Critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: '🔴 Critical' },
  High:     { color: '#f97316', bg: 'rgba(249,115,22,0.12)', label: '🟠 High' },
  Medium:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: '🟡 Medium' },
  Low:      { color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  label: '🟢 Low' },
}

const typeConfig = {
  Bug:   { icon: '🐛', color: '#ef4444' },
  Story: { icon: '📖', color: '#6366f1' },
  Task:  { icon: '✅', color: '#06b6d4' },
  Epic:  { icon: '⚡', color: '#f59e0b' },
}

const TicketIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="5" width="20" height="14" rx="2"/>
    <path d="M16 2v6M8 2v6M2 10h20"/>
  </svg>
)

export default function TicketCard({ ticket, onChange }) {
  const priority = priorityConfig[ticket.priority] || priorityConfig.Medium
  const type     = typeConfig[ticket.issue_type]   || typeConfig.Task

  const handleChange = (field, value) => {
    if (onChange) onChange({ ...ticket, [field]: value })
  }

  return (
    <div className="glass-card p-6 animate-slide-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2 text-cyan-400">
          <TicketIcon />
          <span className="text-sm font-semibold uppercase tracking-wider">Jira Ticket</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-lg text-xs font-bold"
            style={{ background: priority.bg, color: priority.color }}>
            {priority.label}
          </span>
          <span className="text-lg" title={ticket.issue_type}>{type.icon}</span>
        </div>
      </div>

      {/* Ticket ID + Title row */}
      <div className="grid grid-cols-5 gap-3 mb-4">
        <div className="col-span-1">
          <label className="block text-xs text-slate-500 mb-1.5 font-medium">Ticket ID</label>
          <input
            id="ticket-id-input"
            type="text"
            value={ticket.ticket_id || ''}
            onChange={e => handleChange('ticket_id', e.target.value)}
            placeholder="PROJ-101"
            className="w-full px-3 py-2.5 rounded-lg text-sm font-mono font-bold text-cyan-300
              focus:outline-none focus:ring-2 transition-all"
            style={{
              background: 'rgba(6,182,212,0.06)',
              border: '1px solid rgba(6,182,212,0.2)',
            }}
          />
        </div>
        <div className="col-span-4">
          <label className="block text-xs text-slate-500 mb-1.5 font-medium">Title</label>
          <input
            id="ticket-title-input"
            type="text"
            value={ticket.title || ''}
            onChange={e => handleChange('title', e.target.value)}
            placeholder="Add forgot password functionality"
            className="w-full px-3 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all"
            style={{
              background: 'rgba(30,41,59,0.6)',
              border: '1px solid rgba(100,116,139,0.2)',
              color: '#e2e8f0',
            }}
          />
        </div>
      </div>

      {/* Description */}
      <div className="mb-4">
        <label className="block text-xs text-slate-500 mb-1.5 font-medium">Description</label>
        <textarea
          id="ticket-description-input"
          value={ticket.description || ''}
          onChange={e => handleChange('description', e.target.value)}
          placeholder="Describe the requirement in detail..."
          rows={3}
          className="w-full px-3 py-2.5 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 transition-all"
          style={{
            background: 'rgba(30,41,59,0.6)',
            border: '1px solid rgba(100,116,139,0.2)',
            color: '#e2e8f0',
          }}
        />
      </div>

      {/* Meta Row */}
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs text-slate-500 mb-1.5 font-medium">Priority</label>
          <select
            id="ticket-priority-select"
            value={ticket.priority || 'Medium'}
            onChange={e => handleChange('priority', e.target.value)}
            className="w-full px-3 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all cursor-pointer"
            style={{
              background: 'rgba(30,41,59,0.8)',
              border: '1px solid rgba(100,116,139,0.2)',
              color: '#e2e8f0',
            }}
          >
            {Object.keys(priorityConfig).map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1.5 font-medium">Type</label>
          <select
            id="ticket-type-select"
            value={ticket.issue_type || 'Task'}
            onChange={e => handleChange('issue_type', e.target.value)}
            className="w-full px-3 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all cursor-pointer"
            style={{
              background: 'rgba(30,41,59,0.8)',
              border: '1px solid rgba(100,116,139,0.2)',
              color: '#e2e8f0',
            }}
          >
            {Object.keys(typeConfig).map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1.5 font-medium">Status</label>
          <input
            id="ticket-status-input"
            type="text"
            value={ticket.status || ''}
            onChange={e => handleChange('status', e.target.value)}
            placeholder="In Progress"
            className="w-full px-3 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all"
            style={{
              background: 'rgba(30,41,59,0.6)',
              border: '1px solid rgba(100,116,139,0.2)',
              color: '#e2e8f0',
            }}
          />
        </div>
      </div>
    </div>
  )
}
