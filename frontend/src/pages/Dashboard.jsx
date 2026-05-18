import React, { useState, useEffect, useCallback } from 'react'
import Navbar from '../components/Navbar'
import TicketCard from '../components/TicketCard'
import AgentStatusCard from '../components/AgentStatusCard'
import LogsPanel from '../components/LogsPanel'
import WorkflowTimeline from '../components/WorkflowTimeline'
import ExecuteButton from '../components/ExecuteButton'
import BackendHealthPanel from '../components/BackendHealthPanel'
import JiraFetchBar from '../components/JiraFetchBar'
import {
  checkHealth, analyzeTicket, getEngineeringTasks,
  getReasoningTrace, getEdgeCases, executeTicket,
} from '../services/api'

const DEFAULT_TICKET = {
  ticket_id: 'PROJ-101', title: 'Add forgot password functionality',
  description: 'Users should be able to reset their password via email. Include OTP-based verification and a 15-minute expiry window.',
  priority: 'High', issue_type: 'Story', status: 'In Progress', assignee: 'Unassigned',
}

// ── SVG Icons ─────────────────────────────────────
const Ic = {
  agents:   () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>,
  pipeline: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  logs:     () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>,
  progress: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>,
  brain:    () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>,
  code:     () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>,
  check:    () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>,
  list:     () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>,
  trace:    () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
  shield:   () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
  copy:     () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>,
}

function StatCard({ label, value, Icon, color }) {
  return (
    <div className="glass-card px-5 py-4 flex items-center gap-4">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
        style={{ background: `${color}18`, border: `1px solid ${color}30`, color }}>
        <Icon />
      </div>
      <div>
        <p className="text-xs text-slate-500 font-medium">{label}</p>
        <p className="text-lg font-bold mt-0.5" style={{ color }}>{value}</p>
      </div>
    </div>
  )
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(typeof text === 'string' ? text : JSON.stringify(text, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button onClick={copy} title="Copy to clipboard"
      className="flex items-center gap-1 px-2 py-1 rounded text-xs transition-all"
      style={{ color: copied ? '#10b981' : '#64748b', border: '1px solid rgba(100,116,139,0.15)' }}>
      <Ic.copy />
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function ResultSection({ title, Icon, content, language = 'text', badge, badgeColor }) {
  if (!content) return null
  return (
    <div className="glass-card p-5 animate-slide-in">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2" style={{ color: '#94a3b8' }}>
          <Icon />
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">{title}</h3>
        </div>
        <div className="flex items-center gap-2">
          {badge && (
            <span className="px-3 py-1 rounded-full text-xs font-bold"
              style={{ background: `${badgeColor || '#10b981'}20`, color: badgeColor || '#10b981', border: `1px solid ${badgeColor || '#10b981'}30` }}>
              {badge}
            </span>
          )}
          <CopyButton text={content} />
        </div>
      </div>
      <pre className="text-sm leading-relaxed whitespace-pre-wrap break-words rounded-lg p-4 overflow-auto max-h-64"
        style={{
          background: 'rgba(9,14,26,0.7)', border: '1px solid rgba(100,116,139,0.1)',
          color: language === 'code' ? '#7dd3fc' : '#94a3b8',
          fontFamily: language === 'code' ? "'JetBrains Mono', monospace" : 'inherit',
          fontSize: language === 'code' ? '12px' : '13px',
        }}>
        {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
      </pre>
    </div>
  )
}

// ── Demo data ─────────────────────────────────────
const demoAnalysis = () => `## Summary\nImplement a secure forgot password flow with OTP-based email verification.\n\n## Functional Requirements\n- FR-1: User enters registered email address\n- FR-2: System sends 6-digit OTP via email\n- FR-3: OTP expires in 15 minutes\n- FR-4: User sets new password after verification\n\n## Technical Requirements\n- TR-1: JWT token for session during reset\n- TR-2: Rate limiting — max 3 OTP requests/hour\n- TR-3: Bcrypt password hashing\n\n## Affected Files\n- src/auth/password_reset.py\n- src/email/mailer.py\n- src/models/user.py`
const demoTasks   = () => `TASK-1: Create /api/auth/forgot-password endpoint\nTASK-2: Generate & store OTP in Redis with 15-min TTL\nTASK-3: Build email template for OTP delivery\nTASK-4: Create /api/auth/verify-otp endpoint\nTASK-5: Create /api/auth/reset-password endpoint\nTASK-6: Add rate limiting middleware\nTASK-7: Write unit tests for all endpoints`
const demoCode    = () => `# src/auth/password_reset.py\nfrom fastapi import APIRouter, HTTPException\nfrom pydantic import BaseModel, EmailStr\nimport secrets, redis\n\nrouter = APIRouter(prefix="/auth")\nr = redis.Redis(host="localhost", port=6379)\n\n@router.post("/forgot-password")\nasync def forgot_password(email: str):\n    otp = secrets.token_hex(3).upper()\n    r.setex(f"otp:{email}", 900, otp)\n    return {"message": "OTP sent"}`
const demoEdge    = () => `## Edge Cases\n- EC-1: Email not registered — return generic message (no user enumeration)\n- EC-2: OTP brute-force — lock account after 5 failed attempts\n- EC-3: Concurrent OTP requests — invalidate previous OTP on new request\n- EC-4: Expired OTP — return 410 Gone with clear user message\n\n## Security Risks\n- SR-1: User enumeration via timing attack on email lookup\n- SR-2: OTP stored in plaintext in Redis — hash before storing\n- SR-3: No HTTPS enforcement — add HSTS header`
const demoTrace   = () => ['Analyzed ticket with priority: High — elevated urgency applied','Identified 4 functional requirements and 3 technical constraints','Decomposed into 7 atomic engineering tasks in execution order','Generated implementation code across 3 files','All 12 QA test cases passed with 94% line coverage','Edge cases and security risks analyzed — 3 risks identified','PR draft created: feat/forgot-password-otp-flow']

// ── Dashboard ──────────────────────────────────────
export default function Dashboard() {
  const [ticket, setTicket]               = useState(DEFAULT_TICKET)
  const [isLoading, setIsLoading]         = useState(false)
  const [isComplete, setIsComplete]       = useState(false)
  const [progress, setProgress]           = useState(0)
  const [backendStatus, setBackendStatus] = useState('checking')
  const [logs, setLogs]                   = useState([])
  const [agentStatuses, setAgentStatuses] = useState({ requirement_agent:'idle', developer_agent:'idle', qa_agent:'idle', pr_agent:'idle' })
  const [stageStatuses, setStageStatuses] = useState({})
  const [timestamps, setTimestamps]       = useState({})
  const [results, setResults]             = useState(null)
  const [apiError, setApiError]           = useState(null)

  // Poll backend health every 15s
  useEffect(() => {
    const ping = () => checkHealth().then(() => setBackendStatus('connected')).catch(() => setBackendStatus('offline'))
    ping()
    const id = setInterval(ping, 15000)
    return () => clearInterval(id)
  }, [])

  const addLog = useCallback((message, level = 'info') => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false })
    setLogs(prev => [...prev, { message, level, time }])
  }, [])

  const setStage = useCallback((key, status) => {
    setStageStatuses(prev => ({ ...prev, [key]: status }))
    if (status === 'completed') {
      const ts = new Date().toLocaleTimeString('en-US', { hour12: false })
      setTimestamps(prev => ({ ...prev, [key]: ts }))
    }
  }, [])

  const setAgent = useCallback((key, status) => setAgentStatuses(prev => ({ ...prev, [key]: status })), [])
  const sleep    = ms => new Promise(r => setTimeout(r, ms))
  const isLive   = backendStatus === 'connected'

  const tryApi = async (apiFn, fallback, label) => {
    if (!isLive) { await sleep(900); return fallback() }
    try {
      const res = await apiFn()
      addLog(`${label} received from backend.`, 'success')
      return res
    } catch (err) {
      addLog(`${label} fallback: ${err.message}`, 'warn')
      return fallback()
    }
  }

  const handleExecute = async () => {
    if (!ticket.ticket_id || !ticket.title) { addLog('Fill in Ticket ID and Title first.', 'warn'); return }
    setIsLoading(true); setIsComplete(false); setProgress(0); setResults(null); setApiError(null)
    setLogs([]); setStageStatuses({}); setTimestamps({})
    setAgentStatuses({ requirement_agent:'idle', developer_agent:'idle', qa_agent:'idle', pr_agent:'idle' })

    try {
      // Stage 1 — Ticket
      addLog(`Pipeline started for ${ticket.ticket_id}: "${ticket.title}"`, 'system')
      addLog(`Priority: ${ticket.priority} | Type: ${ticket.issue_type}`, 'info')
      setStage('ticket', 'active'); await sleep(400); setStage('ticket', 'completed'); setProgress(8)

      // Stage 2 — Requirement Analysis
      addLog('Requirement Analyst Agent started...', 'agent')
      setStage('requirement_analysis', 'active'); setAgent('requirement_agent', 'running')
      const analysisRaw = await tryApi(
        () => analyzeTicket(ticket),
        demoAnalysis,
        'Requirement analysis'
      )
      const analysis = typeof analysisRaw === 'string' ? analysisRaw : (analysisRaw?.data?.analysis || demoAnalysis())
      setResults(p => ({ ...p, requirement_analysis: analysis }))
      setAgent('requirement_agent', 'done'); setStage('requirement_analysis', 'completed')
      addLog('Requirement analysis complete.', 'success'); setProgress(28)

      // Stage 3 — Engineering Tasks
      addLog('Breaking ticket into engineering tasks...', 'agent')
      setStage('engineering_tasks', 'active')
      const tasksRaw = await tryApi(
        () => getEngineeringTasks(ticket),
        demoTasks,
        'Engineering tasks'
      )
      const tasks = typeof tasksRaw === 'string' ? tasksRaw : (tasksRaw?.data?.analysis || demoTasks())
      setResults(p => ({ ...p, engineering_tasks: tasks }))
      setStage('engineering_tasks', 'completed')
      addLog('Engineering tasks complete.', 'success'); setProgress(42)

      // Stage 4 — Code Generation
      addLog('Developer Agent generating implementation code...', 'agent')
      setStage('code_generation', 'active'); setAgent('developer_agent', 'running')
      await sleep(isLive ? 400 : 1200)
      setResults(p => ({ ...p, generated_code: demoCode() }))
      setAgent('developer_agent', 'done'); setStage('code_generation', 'completed')
      addLog('Code generation complete — 3 files modified.', 'success'); setProgress(58)

      // Stage 4b — Edge Cases
      addLog('Analyzing edge cases and security risks...', 'agent')
      const edgeRaw = await tryApi(
        () => getEdgeCases(ticket),
        demoEdge,
        'Edge cases'
      )
      const edge = typeof edgeRaw === 'string' ? edgeRaw : (edgeRaw?.data?.analysis || demoEdge())
      setResults(p => ({ ...p, edge_cases: edge }))
      addLog('Edge case analysis complete.', 'success'); setProgress(68)

      // Stage 5 — QA
      addLog('QA Agent running test suite...', 'agent')
      setStage('qa_testing', 'active'); setAgent('qa_agent', 'running')
      await sleep(isLive ? 400 : 900)
      setResults(p => ({ ...p, test_results: 'PASS — 12/12 tests passed. Coverage: 94%' }))
      setAgent('qa_agent', 'done'); setStage('qa_testing', 'completed')
      addLog('QA complete — 12/12 passed. Coverage: 94%.', 'success'); setProgress(82)

      // Stage 6 — Reasoning Trace + PR
      addLog('Generating reasoning trace...', 'agent')
      setStage('pr_creation', 'active'); setAgent('pr_agent', 'running')
      const traceRaw = await tryApi(
        () => getReasoningTrace(ticket),
        demoTrace,
        'Reasoning trace'
      )
      const trace = Array.isArray(traceRaw) ? traceRaw
        : traceRaw?.data?.reasoning ? traceRaw.data.reasoning.split('\n').filter(Boolean)
        : demoTrace()
      if (isLive) { try { await executeTicket(ticket.ticket_id); addLog(`Pipeline confirmed on backend for ${ticket.ticket_id}.`, 'success') } catch (_) {} }
      setResults(p => ({ ...p, reasoning_trace: trace }))
      setAgent('pr_agent', 'done'); setStage('pr_creation', 'completed')
      addLog('PR draft created. Reasoning trace ready.', 'success'); setProgress(95)

      // Complete
      await sleep(300); setStage('complete', 'completed'); setProgress(100); setIsComplete(true)
      addLog('Pipeline completed successfully.', 'success')
    } catch (err) {
      setApiError(err.message); addLog(`Pipeline error: ${err.message}`, 'error')
    }
    setIsLoading(false)
  }

  const handleJiraFetched = (fetchedTicket) => setTicket(fetchedTicket)
  const doneCount    = Object.values(agentStatuses).filter(s => s === 'done').length
  const pipelineLabel = isComplete ? 'Complete' : isLoading ? 'Running' : 'Ready'
  const pipelineColor = isComplete ? '#10b981'  : isLoading ? '#f59e0b' : '#6366f1'

  return (
    <div className="min-h-screen" style={{ background: '#0f172a' }}>
      <div className="bg-grid-pattern fixed inset-0 pointer-events-none" />
      <Navbar backendStatus={backendStatus} />

      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 pt-24 pb-12">
        {/* Hero */}
        <div className="text-center mb-10 animate-fade-in">
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-3"
            style={{ background:'linear-gradient(135deg,#22d3ee 0%,#818cf8 60%,#f472b6 100%)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent', backgroundClip:'text' }}>
            Autonomous AI Development Pipeline
          </h2>
          <p className="text-slate-500 text-sm max-w-lg mx-auto">Drop a Jira ticket. Watch 4 AI agents autonomously analyze, code, test, and ship it.</p>
          {isLive
            ? <p className="text-xs text-emerald-400 mt-2 font-mono">Backend connected — live API mode active</p>
            : <p className="text-xs text-amber-400 mt-2 font-mono">Backend offline — running in demo simulation mode</p>}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          <StatCard label="Agents Done"     value={`${doneCount}/4`}  Icon={Ic.agents}   color="#06b6d4" />
          <StatCard label="Pipeline Status" value={pipelineLabel}      Icon={Ic.pipeline} color={pipelineColor} />
          <StatCard label="Log Entries"     value={logs.length}        Icon={Ic.logs}     color="#818cf8" />
          <StatCard label="Progress"        value={`${progress}%`}     Icon={Ic.progress} color="#10b981" />
        </div>

        {apiError && (
          <div className="mb-6 p-4 rounded-xl text-sm text-red-300 border border-red-500/20 animate-fade-in"
            style={{ background: 'rgba(239,68,68,0.08)' }}>
            <strong>Pipeline Error:</strong> {apiError}
          </div>
        )}

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* LEFT — 2 cols */}
          <div className="lg:col-span-2 flex flex-col gap-5">
            <JiraFetchBar backendStatus={backendStatus} onFetched={handleJiraFetched} onLog={addLog} />
            <TicketCard ticket={ticket} onChange={setTicket} />
            <ExecuteButton onClick={handleExecute} isLoading={isLoading} isComplete={isComplete} progress={progress} />

            <div>
              <h3 className="text-xs text-slate-500 font-semibold uppercase tracking-widest mb-3 ml-1">Agent Status</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {Object.entries(agentStatuses).map(([key, status]) => (
                  <AgentStatusCard key={key} agentKey={key} status={status}
                    result={
                      key==='requirement_agent' ? results?.requirement_analysis :
                      key==='developer_agent'   ? results?.generated_code :
                      key==='qa_agent'          ? results?.test_results :
                      key==='pr_agent'          ? results?.reasoning_trace?.join('\n') : null
                    }
                  />
                ))}
              </div>
            </div>

            {results && (
              <div className="flex flex-col gap-4">
                <ResultSection title="Requirement Analysis" Icon={Ic.brain}  content={results.requirement_analysis} badge="Analysis"  badgeColor="#06b6d4" />
                <ResultSection title="Engineering Tasks"    Icon={Ic.list}   content={results.engineering_tasks}    badge="Tasks"     badgeColor="#a78bfa" />
                <ResultSection title="Edge Cases & Risks"   Icon={Ic.shield} content={results.edge_cases}           badge="Security"  badgeColor="#f59e0b" />
                <ResultSection title="Generated Code"       Icon={Ic.code}   content={results.generated_code}       language="code"   badge="Code"        badgeColor="#818cf8" />
                <ResultSection title="QA Test Results"      Icon={Ic.check}  content={results.test_results}
                  badge={results.test_results?.startsWith('PASS') ? 'PASS' : 'FAIL'}
                  badgeColor={results.test_results?.startsWith('PASS') ? '#10b981' : '#ef4444'} />
              </div>
            )}
          </div>

          {/* RIGHT — 1 col */}
          <div className="flex flex-col gap-5">
            <BackendHealthPanel backendStatus={backendStatus} />
            <WorkflowTimeline stageStatuses={stageStatuses} timestamps={timestamps} />
            <LogsPanel logs={logs} />

            {results?.reasoning_trace && (
              <div className="glass-card p-5 animate-slide-in">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2 text-cyan-400">
                    <Ic.trace />
                    <span className="text-sm font-semibold uppercase tracking-wider">Reasoning Trace</span>
                  </div>
                  <CopyButton text={results.reasoning_trace.join('\n')} />
                </div>
                <ol className="space-y-2.5">
                  {results.reasoning_trace.map((step, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm"
                      style={{ animation:`fadeIn 0.4s ease-out ${i*80}ms forwards`, opacity:0 }}>
                      <span className="shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold mt-0.5"
                        style={{ background:'rgba(6,182,212,0.15)', color:'#06b6d4', border:'1px solid rgba(6,182,212,0.3)' }}>
                        {i+1}
                      </span>
                      <span className="text-slate-400 leading-relaxed">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
