# AutoDevX — Frontend Dashboard

A professional React dashboard that visualizes the full autonomous AI development pipeline for the Jira Agentic Development System. It connects to a FastAPI backend and shows how AI agents move from a Jira ticket all the way through requirement analysis, code generation, QA testing, and pull request creation.

---

## What This Is

AutoDevX is the frontend layer of a multi-agent AI system. The idea is straightforward: you give it a Jira ticket, and four specialized AI agents handle the entire development workflow on their own. This dashboard makes that process visible in real time — you can watch each agent pick up its task, see the reasoning behind decisions, and review the outputs as they come in.

It was built for hackathon demonstration purposes, so the emphasis is on clarity and visual impact. The interface is dark-themed, responsive, and designed to make a complex backend pipeline feel approachable.

---

## Tech Stack

- **React 18** with Vite 5 for the build toolchain
- **Tailwind CSS 3** for styling
- **Axios** for all HTTP communication with the backend
- **Google Fonts** — Inter for UI text, JetBrains Mono for code and log output

---

## Project Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css
    ├── services/
    │   └── api.js              # All Axios calls to the FastAPI backend
    ├── components/
    │   ├── Navbar.jsx          # Top navigation with backend status indicator
    │   ├── TicketCard.jsx      # Jira ticket input form
    │   ├── AgentStatusCard.jsx # Per-agent status with live state transitions
    │   ├── LogsPanel.jsx       # Terminal-style real-time log viewer
    │   ├── WorkflowTimeline.jsx# Seven-stage pipeline timeline
    │   ├── ExecuteButton.jsx   # Main CTA with animated progress bar
    │   ├── BackendHealthPanel.jsx # Collapsible backend diagnostics panel
    │   └── JiraFetchBar.jsx    # Fetches real tickets from Jira via backend
    └── pages/
        └── Dashboard.jsx       # Main page — assembles all components
```

---

## Getting Started

Make sure you have Node.js 18 or later installed.

**Install dependencies**

```bash
cd frontend
npm install
```

**Start the development server**

```bash
npm run dev
```

Open your browser at `http://localhost:5173`.

**Build for production**

```bash
npm run build
```

---

## Backend Connection

The frontend expects the FastAPI backend to be running at `http://127.0.0.1:8000`. CORS is already configured on the backend to allow requests from `localhost:5173`.

If the backend is not running, the dashboard switches automatically to a demo simulation mode. You will see a status banner at the top indicating which mode is active. Every 15 seconds the frontend pings the backend health endpoint and updates the connection state without requiring a page refresh.

To start the backend:

```bash
# From the project root
uvicorn backend.main:app --reload --port 8000
```

---

## API Endpoints Used

| Action | Method | Path |
|---|---|---|
| Health check | GET | `/health` |
| Analyst health + model info | GET | `/analyst/health` |
| Agent pool status | GET | `/agents/status` |
| Full requirement analysis | POST | `/analyst/analyze` |
| Fetch ticket from Jira | POST | `/analyst/analyze-ticket` |
| Engineering task breakdown | POST | `/analyst/engineering-tasks` |
| Edge cases and security risks | POST | `/analyst/edge-cases` |
| Reasoning trace | POST | `/analyst/reasoning` |
| Execute full pipeline | POST | `/execute-ticket/{ticket_id}` |

---

## Dashboard Features

**Jira Fetch Bar**
Enter a ticket ID and pull the full ticket data directly from your Jira instance. The form auto-populates with the returned values. Requires the backend to be connected.

**Ticket Form**
Editable form for ticket ID, title, description, priority, type, and status. You can fill this manually or load it from Jira.

**Agent Status Cards**
Four cards — one per agent — show the current state of each agent (idle, running, done, or error). When an agent completes, a preview of its output appears inline.

**Workflow Timeline**
A seven-stage vertical timeline tracks the pipeline from ticket intake through to the final PR draft. Each stage animates in as it completes, with timestamps.

**Reasoning Logs**
A terminal-style panel with timestamped, color-coded log entries streamed as the pipeline runs. Entries are color-coded by type: system messages, agent activity, warnings, and results.

**Result Sections**
After the pipeline completes, the following outputs appear with copy-to-clipboard support:
- Requirement analysis (seven structured sections)
- Engineering task list
- Edge cases and security risks
- Generated implementation code
- QA test results with pass/fail badge

**Reasoning Trace**
A numbered chain-of-thought trace explaining why each decision was made during the pipeline.

**Backend Health Panel**
A collapsible diagnostics panel showing the LLM model in use, retriever readiness, active API endpoints, and the status of each agent in the pool. Refreshes every 30 seconds when the backend is live.

---

## Running Without the Backend

If you just want to see the UI and pipeline animation without a running backend, start the dev server and click Execute AI Pipeline. The dashboard will run a full demo simulation using sample data, going through all seven stages with realistic timing. Everything looks and behaves the same as the live version.

---

## Development Notes

- All components are written as functional React components with hooks.
- No external UI component libraries are used — everything is built with Tailwind and vanilla CSS.
- The `tryApi` helper in `Dashboard.jsx` wraps every API call with automatic fallback to demo data if the backend returns an error or is unreachable.
- The API service layer in `src/services/api.js` is the single source of truth for all backend URLs. If you change the backend port, update `BASE_URL` in that file.
- Hot module replacement is enabled via Vite, so component changes reflect instantly in the browser.

---

## Environment

No `.env` file is required for the frontend. The backend URL is hardcoded to `http://127.0.0.1:8000` in `src/services/api.js`. If you need to point this at a different host (for example, a deployed backend), update that constant.

---

## License

This project was built as part of a hackathon submission. Feel free to extend it.
