import axios from 'axios'

const BASE_URL = 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,   // 120s — LLM calls take ~20s
  headers: { 'Content-Type': 'application/json' },
})

// ── Response interceptor — normalize errors ───────
api.interceptors.response.use(
  res => res,
  err => {
    const msg = err.response?.data?.detail || err.message || 'Unknown error'
    return Promise.reject(new Error(msg))
  }
)

// ── Health ────────────────────────────────────────
export const checkHealth       = ()     => api.get('/health')
export const getAnalystHealth  = ()     => api.get('/analyst/health')

// ── Agent Status ──────────────────────────────────
export const getAgentsStatus   = ()     => api.get('/agents/status')

// ── Jira — fetch raw ticket data ──────────────────
export const fetchJiraTicket   = (id)   => api.get(`/jira/ticket/${id}`)

// ── Execute Full Ticket Pipeline ──────────────────
export const executeTicket     = (id)   => api.post(`/execute-ticket/${id}`)

// ── Requirement Analysis (full 7-section) ─────────
export const analyzeTicket = (data) => api.post('/analyst/analyze', {
  ticket_id:   data.ticket_id   || '',
  title:       data.title       || '',
  description: data.description || '',
  status:      data.status      || 'TODO',
  priority:    data.priority    || 'MEDIUM',
  issue_type:  data.issue_type  || 'Task',
  assignee:    data.assignee    || 'Unassigned',
})

// ── Fetch from real Jira by ticket ID ─────────────
export const analyzeFromJira = (id) => api.post('/analyst/analyze-ticket', { ticket_id: id })

// ── Engineering Tasks Breakdown ───────────────────
export const getEngineeringTasks = (data) => api.post('/analyst/engineering-tasks', {
  ticket_id:   data.ticket_id   || '',
  title:       data.title       || '',
  description: data.description || '',
  status:      data.status      || 'TODO',
  priority:    data.priority    || 'MEDIUM',
  issue_type:  data.issue_type  || 'Task',
  assignee:    data.assignee    || 'Unassigned',
})

// ── Edge Cases + Security Risks ───────────────────
export const getEdgeCases = (data) => api.post('/analyst/edge-cases', {
  ticket_id:   data.ticket_id   || '',
  title:       data.title       || '',
  description: data.description || '',
  status:      data.status      || 'TODO',
  priority:    data.priority    || 'MEDIUM',
  issue_type:  data.issue_type  || 'Task',
  assignee:    data.assignee    || 'Unassigned',
})

// ── Explainable Reasoning Trace ───────────────────
export const getReasoningTrace = (data) => api.post('/analyst/reasoning', {
  ticket_id:   data.ticket_id   || '',
  title:       data.title       || '',
  description: data.description || '',
  status:      data.status      || 'TODO',
  priority:    data.priority    || 'MEDIUM',
  issue_type:  data.issue_type  || 'Task',
  assignee:    data.assignee    || 'Unassigned',
})

// ── Vector Store Stats ────────────────────────────
export const getVectorStats = () => api.get('/retrieval/stats')

export default api
