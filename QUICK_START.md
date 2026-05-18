# 🚀 Quick Start Guide - Workflow Orchestration

## ⚡ 5-Minute Setup

### 1. Install Dependencies

```bash
pip install langgraph langchain-core langchain-groq
```

### 2. Set Environment Variables

```bash
# .env file
GROQ_API_KEY=gsk_your_api_key_here
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_KEY=your_jira_api_key
```

### 3. Run Tests

```bash
# Set PYTHONPATH (Windows PowerShell)
$env:PYTHONPATH="D:\Jira-Agentic-Development-System"

# Run all tests
python tests/test_graph.py
python tests/test_workflow_with_retry.py
```

### 4. Execute Workflow

```python
from workflows.orchestrator.graph import execute_workflow

# Execute for a Jira ticket
final_state = execute_workflow(
    ticket_id="SCRUM-1",
    max_retries=2,
    verbose=True
)

print(f"Status: {final_state['pipeline_status']}")
print(f"PR Ready: {final_state['pr_ready']}")
```

---

## 📋 Common Commands

### Run Workflow via Python

```python
from workflows.orchestrator.graph import execute_workflow, get_workflow_status

# Execute workflow
state = execute_workflow("SCRUM-1", max_retries=2, verbose=True)

# Get status
status = get_workflow_status(state)
print(status['progress'])  # {'requirement': '✅', 'developer': '✅', ...}
```

### Run Workflow via REST API

```bash
# Start server
python backend/main.py

# Execute workflow
curl -X POST http://localhost:8000/execute-ticket/SCRUM-1

# Check health
curl http://localhost:8000/health
```

### Run Tests

```bash
# Graph tests
python tests/test_graph.py

# Integration tests
python tests/test_workflow_with_retry.py

# Retry manager tests
python workflows/retry/retry_manager.py

# Graph compilation test
python workflows/orchestrator/graph.py
```

---

## 🎯 Key Features

### ✅ Automatic Retry Logic

```python
# QA fails → Developer retries → QA re-tests
execute_workflow("SCRUM-1", max_retries=2)
```

### ✅ Explainable Logs

```
[ReqNode] 🔍 Starting requirement analysis
[ReqNode] Reason: Analyzing Jira ticket to extract requirements
[DevNode] 💻 Starting code generation
[DevNode] 🔄 RETRY ATTEMPT #1
[QANode] 🧪 Starting test execution
[QANode] ✅ Tests PASSED
[PRNode] 📝 Starting PR generation
```

### ✅ Progress Tracking

```python
status = get_workflow_status(final_state)
print(status['progress'])
# Output: {'requirement': '✅', 'developer': '✅', 'qa': '✅', 'pr': '✅'}
```

---

## 📊 Expected Output

### Successful Workflow

```
======================================================================
  EXECUTING WORKFLOW: SCRUM-1
======================================================================

  [ReqNode] 🔍 Starting requirement analysis — ticket: SCRUM-1
  [ReqNode] ✅ Requirement analysis completed
  [ReqNode] Reason: Extracted 5 functional requirements

  [DevNode] 💻 Starting code generation — ticket: SCRUM-1
  [DevNode] ✅ Code generation completed

  [QANode] 🧪 Starting test execution — ticket: SCRUM-1
  [QANode] ❌ Tests FAILED
  [Conditional] Tests FAILED → RETRY (attempt 1)

  [DevNode] 💻 Starting code generation — ticket: SCRUM-1
  [DevNode] 🔄 RETRY ATTEMPT #1
  [DevNode] ✅ Code generation completed

  [QANode] 🧪 Starting test execution — ticket: SCRUM-1
  [QANode] ✅ Tests PASSED
  [Conditional] Tests PASSED → PR

  [PRNode] 📝 Starting PR generation — ticket: SCRUM-1
  [PRNode] ✅ PR generation completed

  [Executor] ✅ Workflow completed
  [Executor] Retries used: 1
```

---

## 🔧 Configuration

### Workflow Parameters

```python
execute_workflow(
    ticket_id="SCRUM-1",     # Required: Jira ticket ID
    ticket_data=None,        # Optional: Pre-fetched ticket
    max_retries=2,           # Optional: Max retry attempts (default: 2)
    verbose=True             # Optional: Enable logs (default: True)
)
```

### Retry Strategies

- **Attempt 1**: `targeted_fix` - Fix specific failures
- **Attempt 2**: `full_regeneration` - Regenerate all code
- **Attempt 3+**: `conservative_fix` - Minimal changes

---

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Solution: Set PYTHONPATH
$env:PYTHONPATH="D:\Jira-Agentic-Development-System"
```

### Issue: Workflow doesn't retry

```python
# Check max_retries setting
execute_workflow("SCRUM-1", max_retries=2)  # Must be > 0

# Check test_status
print(state.get("test_status"))  # Should be "FAILED" or "PARTIAL"
```

### Issue: Missing logs

```python
# Enable verbose mode
execute_workflow("SCRUM-1", verbose=True)
```

### Issue: Tests fail

```bash
# Check dependencies
pip install langgraph langchain-core langchain-groq

# Verify imports
python -c "from langgraph.graph import StateGraph; print('OK')"
```

---

## 📚 Documentation

- **Comprehensive Guide**: `workflows/README.md`
- **Architecture**: `docs/WORKFLOW_ARCHITECTURE.md`
- **Implementation Details**: `docs/WORKFLOW_IMPLEMENTATION.md`
- **Completion Report**: `WORKFLOW_COMPLETION_REPORT.md`

---

## 🎓 Examples

### Example 1: Basic Execution

```python
from workflows.orchestrator.graph import execute_workflow

state = execute_workflow("SCRUM-1")
print(f"Done! PR Ready: {state['pr_ready']}")
```

### Example 2: Custom Retry Limit

```python
# Allow only 1 retry
state = execute_workflow("SCRUM-1", max_retries=1)
```

### Example 3: Silent Execution

```python
# Disable logs
state = execute_workflow("SCRUM-1", verbose=False)
```

### Example 4: With Pre-fetched Ticket

```python
from backend.jira.ticket_fetcher import fetch_ticket

ticket = fetch_ticket("SCRUM-1")
state = execute_workflow("SCRUM-1", ticket_data=ticket)
```

### Example 5: Check Status

```python
from workflows.orchestrator.graph import get_workflow_status

status = get_workflow_status(state)
print(f"Pipeline: {status['pipeline_status']}")
print(f"Stage: {status['current_stage']}")
print(f"Retries: {status['retry_count']}")
print(f"Progress: {status['progress']}")
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Tests pass: `python tests/test_graph.py`
- [ ] Workflow executes: `execute_workflow("TEST-1")`
- [ ] Logs appear: Check for emoji indicators
- [ ] Retry works: First attempt fails, second passes
- [ ] Status tracking: `get_workflow_status()` returns progress

---

## 🚀 Next Steps

1. ✅ **Phase 1 Complete**: Workflow orchestration
2. 🔜 **Phase 2**: Implement Developer Agent
3. 🔜 **Phase 3**: Implement QA Agent
4. 🔜 **Phase 4**: Implement PR Agent
5. 🔜 **Phase 5**: Build Frontend Dashboard

---

## 📞 Support

- Check `workflows/README.md` for detailed docs
- Run tests to verify setup
- Enable verbose logs for debugging
- Review state for error details

---

**Ready to build! 🎉**
