# Workflow Orchestration System

Multi-agent LangGraph workflow for automated software development from Jira tickets.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKFLOW PIPELINE                         │
└─────────────────────────────────────────────────────────────┘

    START
      │
      ▼
┌──────────────────┐
│ Requirement Node │  ← Analyzes Jira ticket
│   (Analyst AI)   │  → Extracts requirements
└────────┬─────────┘  → Identifies affected files
         │            → Assesses risks
         ▼
┌──────────────────┐
│ Developer Node   │  ← Generates code
│  (Developer AI)  │  → Creates diffs
└────────┬─────────┘  → Implements features
         │
         ▼
┌──────────────────┐
│   QA Node        │  ← Generates tests
│    (QA AI)       │  → Runs validation
└────────┬─────────┘  → Reports results
         │
         ▼
    ┌────────────┐
    │ Tests Pass?│
    └─────┬──────┘
          │
    ┌─────┴─────┐
    │           │
   YES         NO
    │           │
    │      ┌────▼────────┐
    │      │ Retry Count │
    │      │ < Max?      │
    │      └────┬────────┘
    │           │
    │      ┌────┴────┐
    │      │         │
    │     YES       NO
    │      │         │
    │      │         │
    │      ▼         │
    │  ┌─────────┐  │
    │  │Developer│  │
    │  │ Retry   │  │
    │  └────┬────┘  │
    │       │       │
    │       └───────┘
    │           │
    ▼           ▼
┌──────────────────┐
│    PR Node       │  ← Generates PR
│   (PR AI)        │  → Creates description
└────────┬─────────┘  → Includes test results
         │
         ▼
       END
```

## 📁 Structure

```
workflows/
├── state.py                    # Shared state schema
├── nodes.py                    # Agent node implementations
├── orchestrator/
│   ├── __init__.py
│   └── graph.py               # LangGraph workflow builder
└── retry/
    ├── __init__.py
    └── retry_manager.py       # Retry logic & strategies
```

## 🚀 Quick Start

### Execute a Workflow

```python
from workflows.orchestrator.graph import execute_workflow

# Execute full pipeline for a Jira ticket
final_state = execute_workflow(
    ticket_id="SCRUM-1",
    max_retries=2,
    verbose=True
)

print(f"Status: {final_state['pipeline_status']}")
print(f"Test Status: {final_state['test_status']}")
print(f"PR Ready: {final_state['pr_ready']}")
```

### Get Workflow Status

```python
from workflows.orchestrator.graph import get_workflow_status

status = get_workflow_status(final_state)
print(status['progress'])  # {'requirement': '✅', 'developer': '✅', ...}
```

### Build Custom Workflow

```python
from workflows.orchestrator.graph import build_workflow_graph, compile_workflow
from workflows.state import create_initial_state

# Build and compile
graph = build_workflow_graph()
workflow = graph.compile()

# Execute with custom state
initial_state = create_initial_state("TICKET-1")
result = workflow.invoke(initial_state)
```

## 🔄 Retry Logic

The workflow includes **automatic retry** when QA tests fail:

### How It Works

1. **QA Node** runs tests on generated code
2. If tests **FAIL**:
   - Check retry count < max_retries
   - Route back to **Developer Node**
   - Developer regenerates code with QA feedback
   - QA re-tests the updated code
3. If tests **PASS** or max retries exceeded:
   - Proceed to **PR Node**

### Configuration

```python
execute_workflow(
    ticket_id="SCRUM-1",
    max_retries=2,  # Default: 2 attempts
    verbose=True
)
```

### Retry Strategies

The retry manager selects strategies based on attempt count:

- **Attempt 1**: `targeted_fix` - Fix specific failures
- **Attempt 2**: `full_regeneration` - Regenerate all code
- **Attempt 3+**: `conservative_fix` - Minimal safe changes

## 📊 State Management

### WorkflowState Schema

```python
{
    # Input
    "ticket_id": str,
    "ticket_data": dict,
    
    # Requirement Analyst Output
    "requirements": dict,
    "summary": str,
    "functional_reqs": list[str],
    "technical_reqs": list[str],
    "implementation_steps": list[str],
    "affected_files": list[str],
    "risk_level": str,
    "reasoning_trace": str,
    "edge_cases": str,
    
    # Developer Output
    "generated_code": dict[str, str],
    "code_diff": str,
    "code_ready": bool,
    
    # QA Output
    "test_cases": list[str],
    "test_results": dict,
    "test_status": str,
    "qa_notes": str,
    
    # PR Output
    "pr_title": str,
    "pr_description": str,
    "pr_ready": bool,
    
    # Pipeline Metadata
    "current_stage": str,
    "completed_stages": list[str],
    "errors": list[str],
    "pipeline_status": str,
    "retry_count": int,
    "max_retries": int,
}
```

## 🧪 Testing

### Run All Tests

```bash
# Graph compilation & connectivity
python tests/test_graph.py

# Integration tests with retry
python tests/test_workflow_with_retry.py

# Retry manager tests
python workflows/retry/retry_manager.py
```

### Expected Output

```
✅ PASS | Graph Compilation
✅ PASS | Node Connectivity
✅ PASS | Conditional Logic
✅ PASS | State Transitions
✅ PASS | Workflow Execution
✅ PASS | Workflow with Retry
✅ PASS | Max Retries Exceeded

Total: 7/7 tests passed
```

## 📝 Explainable Logs

All nodes generate **transparent execution logs**:

```
[ReqNode] 🔍 Starting requirement analysis — ticket: SCRUM-1
[ReqNode] Reason: Analyzing Jira ticket to extract structured requirements
[ReqNode] ✅ Requirement analysis completed
[ReqNode] Reason: Extracted 5 functional requirements
[ReqNode] Risk Level: HIGH
[ReqNode] Implementation Steps: 7

[DevNode] 💻 Starting code generation — ticket: SCRUM-1
[DevNode] Reason: Generating initial code implementation
[DevNode] ✅ Code generation completed
[DevNode] Reason: Generated code for 7 implementation steps

[QANode] 🧪 Starting test execution — ticket: SCRUM-1
[QANode] Reason: Running initial test suite validation
[QANode] ❌ Tests FAILED
[QANode] Reason: Core implementation missing, triggering retry

[DevNode] 💻 Starting code generation — ticket: SCRUM-1
[DevNode] 🔄 RETRY ATTEMPT #1
[DevNode] Reason: QA tests failed, regenerating code with fixes

[QANode] 🧪 Starting test execution — ticket: SCRUM-1
[QANode] 🔄 RETRY VALIDATION (attempt #1)
[QANode] Reason: Re-testing code after developer fixes
[QANode] ✅ Tests PASSED
[QANode] Reason: All 8 test cases passed validation

[PRNode] 📝 Starting PR generation — ticket: SCRUM-1
[PRNode] Reason: Creating pull request with code changes and test results
[PRNode] ✅ PR generation completed
```

## 🎯 Features

### ✅ Implemented

- [x] LangGraph workflow construction
- [x] 4-node pipeline (Requirement → Developer → QA → PR)
- [x] Automatic QA retry logic
- [x] Conditional routing based on test results
- [x] State persistence across nodes
- [x] Explainable execution logs
- [x] Retry strategy selection
- [x] Failure pattern detection
- [x] Comprehensive test suite

### 🚧 Coming Soon

- [ ] Parallel agent execution
- [ ] Human-in-the-loop approval gates
- [ ] Workflow visualization dashboard
- [ ] Custom node injection
- [ ] Workflow templates
- [ ] Performance metrics tracking

## 🔧 Configuration

### Environment Variables

```bash
# .env
GROQ_API_KEY=gsk_...           # Required for LLM calls
JIRA_BASE_URL=https://...      # Required for ticket fetching
JIRA_EMAIL=user@example.com
JIRA_API_KEY=...
```

### Workflow Parameters

```python
execute_workflow(
    ticket_id="SCRUM-1",        # Required: Jira ticket ID
    ticket_data=None,           # Optional: Pre-fetched ticket data
    max_retries=2,              # Optional: Max QA retry attempts
    verbose=True,               # Optional: Print execution logs
)
```

## 📚 API Reference

### Core Functions

#### `execute_workflow(ticket_id, ticket_data=None, max_retries=2, verbose=True)`

Executes the full multi-agent workflow.

**Returns**: `WorkflowState` - Final state after completion

#### `get_workflow_status(state)`

Returns human-readable status summary.

**Returns**: `dict` with progress indicators and metadata

#### `build_workflow_graph()`

Constructs the LangGraph workflow.

**Returns**: `StateGraph` - Uncompiled graph

#### `compile_workflow()`

Builds and compiles the workflow.

**Returns**: `CompiledStateGraph` - Ready for execution

### Retry Functions

#### `should_retry(state)`

Determines if retry should be triggered.

**Returns**: `bool`

#### `get_retry_reason(state)`

Generates human-readable retry reason.

**Returns**: `str`

#### `generate_retry_feedback(state)`

Creates detailed feedback for developer agent.

**Returns**: `str` - Structured feedback

## 🐛 Troubleshooting

### Workflow Fails to Compile

```python
# Check LangGraph installation
pip install langgraph langchain-core

# Verify imports
from langgraph.graph import StateGraph, END
```

### Retry Loop Not Triggering

```python
# Check max_retries setting
execute_workflow(ticket_id="...", max_retries=2)

# Verify test_status in state
print(state.get("test_status"))  # Should be "FAILED" or "PARTIAL"
```

### Missing Logs

```python
# Enable verbose mode
execute_workflow(ticket_id="...", verbose=True)
```

## 📖 Examples

See `tests/test_workflow_with_retry.py` for complete examples.

## 🤝 Contributing

When adding new nodes:

1. Define node function in `workflows/nodes.py`
2. Add node to graph in `workflows/orchestrator/graph.py`
3. Update `WorkflowState` schema in `workflows/state.py`
4. Add tests in `tests/`

## 📄 License

Part of the Jira Agentic Development System.
