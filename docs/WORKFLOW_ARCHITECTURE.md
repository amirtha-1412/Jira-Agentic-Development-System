# Workflow Architecture Diagram

## 🏗️ Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    JIRA AGENTIC DEVELOPMENT SYSTEM                   │
│                     Multi-Agent Workflow Pipeline                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          INPUT LAYER                                 │
└─────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  Jira Ticket │  ← User creates ticket
    │   SCRUM-1    │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Ticket       │  ← Fetch & parse ticket
    │ Fetcher      │  → Normalize fields
    └──────┬───────┘  → Extract metadata
           │
           ▼
    ┌──────────────┐
    │ Workflow     │  ← Initialize state
    │ Executor     │  → Set max_retries
    └──────┬───────┘  → Start pipeline
           │
           ▼

┌─────────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH WORKFLOW                              │
└─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │  NODE 1: REQUIREMENT ANALYST                                 │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │ 🔍 Analyzes Jira ticket                                 │ │
    │  │ • Extracts functional requirements                      │ │
    │  │ • Identifies technical requirements                     │ │
    │  │ • Lists affected files                                  │ │
    │  │ • Defines implementation steps                          │ │
    │  │ • Assesses risk level                                   │ │
    │  │ • Generates reasoning trace                             │ │
    │  │ • Analyzes edge cases                                   │ │
    │  └────────────────────────────────────────────────────────┘ │
    │  Input:  ticket_id, ticket_data                             │
    │  Output: requirements, summary, functional_reqs,            │
    │          technical_reqs, implementation_steps,              │
    │          affected_files, risk_level, reasoning_trace        │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  NODE 2: DEVELOPER AGENT                                     │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │ 💻 Generates code implementation                        │ │
    │  │ • Reads implementation steps                            │ │
    │  │ • Generates code for affected files                     │ │
    │  │ • Creates unified diffs                                 │ │
    │  │ • Applies QA feedback on retry                          │ │
    │  │ • Increments retry_count                                │ │
    │  └────────────────────────────────────────────────────────┘ │
    │  Input:  functional_reqs, implementation_steps,             │
    │          affected_files, qa_notes (on retry)                │
    │  Output: generated_code, code_diff, code_ready,             │
    │          retry_count                                        │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  NODE 3: QA AGENT                                            │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │ 🧪 Validates code quality                               │ │
    │  │ • Generates test cases                                  │ │
    │  │ • Executes tests                                        │ │
    │  │ • Analyzes results                                      │ │
    │  │ • Detects failures                                      │ │
    │  │ • Generates feedback for developer                      │ │
    │  └────────────────────────────────────────────────────────┘ │
    │  Input:  generated_code, functional_reqs, edge_cases        │
    │  Output: test_cases, test_results, test_status, qa_notes   │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  CONDITIONAL EDGE: should_retry_development()                │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │ Decision Logic:                                         │ │
    │  │                                                         │ │
    │  │ IF test_status == "PASSED":                            │ │
    │  │     → Route to PR Node                                 │ │
    │  │                                                         │ │
    │  │ ELIF test_status in ["FAILED", "PARTIAL"]:            │ │
    │  │     IF retry_count < max_retries:                      │ │
    │  │         → Route to Developer Node (RETRY)              │ │
    │  │     ELSE:                                               │ │
    │  │         → Route to PR Node (with warnings)             │ │
    │  │                                                         │ │
    │  │ ELIF "CRITICAL" in errors:                             │ │
    │  │     → Route to END (abort)                             │ │
    │  └────────────────────────────────────────────────────────┘ │
    └──────────────┬────────────────────────┬─────────────────────┘
                   │                        │
         Tests FAILED                  Tests PASSED
         retry < max                        │
                   │                        │
                   │                        ▼
                   │         ┌─────────────────────────────────────┐
                   │         │  NODE 4: PR AGENT                    │
                   │         │  ┌────────────────────────────────┐ │
                   │         │  │ 📝 Generates pull request      │ │
                   │         │  │ • Creates PR title             │ │
                   │         │  │ • Generates PR description     │ │
                   │         │  │ • Includes test results        │ │
                   │         │  │ • Adds QA notes                │ │
                   │         │  │ • Marks PR as ready/not ready  │ │
                   │         │  └────────────────────────────────┘ │
                   │         │  Input:  summary, requirements,     │
                   │         │          test_status, qa_notes      │
                   │         │  Output: pr_title, pr_description,  │
                   │         │          pr_ready                   │
                   │         └──────────────┬──────────────────────┘
                   │                        │
                   │                        ▼
                   │                      ┌───┐
                   │                      │END│
                   │                      └───┘
                   │
                   └──────────────────────┐
                                          │
                   ┌──────────────────────┘
                   │
                   │  RETRY LOOP
                   │
                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  RETRY MANAGER                                               │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │ 🔄 Manages retry logic                                  │ │
    │  │ • Increments retry_count                                │ │
    │  │ • Generates retry reason                                │ │
    │  │ • Selects retry strategy:                               │ │
    │  │   - Attempt 1: targeted_fix                             │ │
    │  │   - Attempt 2: full_regeneration                        │ │
    │  │   - Attempt 3+: conservative_fix                        │ │
    │  │ • Generates developer feedback                          │ │
    │  │ • Tracks retry history                                  │ │
    │  │ • Detects failure patterns                              │ │
    │  └────────────────────────────────────────────────────────┘ │
    └──────────────────────────┬──────────────────────────────────┘
                               │
                               │ Feedback Loop
                               │
                               ▼
                    Back to Developer Node
                    (with QA feedback)

┌─────────────────────────────────────────────────────────────────────┐
│                         STATE MANAGEMENT                             │
└─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │  WorkflowState (TypedDict)                                   │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │ Shared memory across all nodes:                        │ │
    │  │                                                         │ │
    │  │ • ticket_id, ticket_data                               │ │
    │  │ • requirements, summary, functional_reqs               │ │
    │  │ • technical_reqs, implementation_steps                 │ │
    │  │ • affected_files, risk_level                           │ │
    │  │ • reasoning_trace, edge_cases                          │ │
    │  │ • generated_code, code_diff, code_ready                │ │
    │  │ • test_cases, test_results, test_status                │ │
    │  │ • qa_notes                                              │ │
    │  │ • pr_title, pr_description, pr_ready                   │ │
    │  │ • current_stage, completed_stages                      │ │
    │  │ • errors, pipeline_status                              │ │
    │  │ • retry_count, max_retries                             │ │
    │  └────────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         OUTPUT LAYER                                 │
└─────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │ Final State  │  ← Complete workflow state
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Status       │  ← Progress indicators
    │ Summary      │  → Retry count
    └──────┬───────┘  → Test results
           │
           ▼
    ┌──────────────┐
    │ REST API     │  ← JSON response
    │ Response     │  → /execute-ticket/{id}
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Frontend     │  ← Display results
    │ Dashboard    │  → Show progress
    └──────────────┘  → Monitor agents

┌─────────────────────────────────────────────────────────────────────┐
│                      EXECUTION FLOW EXAMPLE                          │
└─────────────────────────────────────────────────────────────────────┘

Ticket: SCRUM-1 "Add password reset"

Step 1: Requirement Analysis
  [ReqNode] 🔍 Starting requirement analysis
  [ReqNode] Reason: Analyzing Jira ticket to extract requirements
  [ReqNode] ✅ Extracted 4 functional requirements
  [ReqNode] Risk Level: HIGH

Step 2: Code Generation (Attempt 1)
  [DevNode] 💻 Starting code generation
  [DevNode] Reason: Generating initial code implementation
  [DevNode] ✅ Generated code for 5 implementation steps

Step 3: QA Testing (Attempt 1)
  [QANode] 🧪 Starting test execution
  [QANode] Reason: Running initial test suite validation
  [QANode] ❌ Tests FAILED
  [QANode] Reason: Core implementation missing

Step 4: Conditional Routing
  [Conditional] Tests FAILED → RETRY (attempt 1)

Step 5: Code Generation (Retry)
  [DevNode] 💻 Starting code generation
  [DevNode] 🔄 RETRY ATTEMPT #1
  [DevNode] Reason: QA tests failed, regenerating code with fixes
  [DevNode] QA Feedback: Missing implementation detected
  [DevNode] ✅ Code regenerated with fixes

Step 6: QA Testing (Retry)
  [QANode] 🧪 Starting test execution
  [QANode] 🔄 RETRY VALIDATION (attempt #1)
  [QANode] Reason: Re-testing code after developer fixes
  [QANode] ✅ Tests PASSED
  [QANode] Reason: All 6 test cases passed

Step 7: PR Generation
  [PRNode] 📝 Starting PR generation
  [PRNode] Reason: Creating pull request with test results
  [PRNode] ✅ PR generated successfully
  [PRNode] PR Ready: True

Result:
  ✅ Pipeline Status: completed
  ✅ Test Status: PASSED
  ✅ Retry Count: 1
  ✅ PR Ready: True

┌─────────────────────────────────────────────────────────────────────┐
│                      KEY DESIGN PATTERNS                             │
└─────────────────────────────────────────────────────────────────────┘

1. STATE MACHINE PATTERN
   • Each node reads from shared state
   • Each node returns partial state updates
   • LangGraph merges updates automatically

2. FEEDBACK LOOP PATTERN
   • QA provides feedback to Developer
   • Developer uses feedback to improve code
   • Loop continues until success or max retries

3. STRATEGY PATTERN
   • Different retry strategies for different attempts
   • Strategy selection based on context
   • Adaptive behavior based on failure patterns

4. OBSERVER PATTERN
   • Transparent logging at every step
   • Explainable reasoning for all decisions
   • Progress tracking and status updates

5. CIRCUIT BREAKER PATTERN
   • Max retries limit prevents infinite loops
   • Critical errors abort immediately
   • Graceful degradation on failure

┌─────────────────────────────────────────────────────────────────────┐
│                      TECHNOLOGY STACK                                │
└─────────────────────────────────────────────────────────────────────┘

• LangGraph: Workflow orchestration
• LangChain: LLM integration
• Groq: Fast LLM inference
• FastAPI: REST API server
• ChromaDB: Vector store (for code retrieval)
• Python 3.10+: Core language
• TypedDict: Type-safe state management

┌─────────────────────────────────────────────────────────────────────┐
│                      SCALABILITY & PERFORMANCE                       │
└─────────────────────────────────────────────────────────────────────┘

Current:
  • Sequential node execution
  • Single ticket processing
  • ~5-10 seconds per workflow

Future Optimizations:
  • Parallel agent execution
  • Batch ticket processing
  • Caching and memoization
  • Async/await patterns
  • Distributed execution

┌─────────────────────────────────────────────────────────────────────┐
│                      MONITORING & OBSERVABILITY                      │
└─────────────────────────────────────────────────────────────────────┘

Implemented:
  ✅ Explainable logs with reasoning
  ✅ Progress indicators (✅ ⏳ ❌)
  ✅ Retry count tracking
  ✅ Error collection
  ✅ Status summaries

Future:
  • Metrics dashboard
  • Performance tracking
  • Error rate monitoring
  • Agent health checks
  • Workflow visualization

```

## 🎯 Summary

This architecture provides:

1. **Modularity**: Each node is independent and testable
2. **Reliability**: Automatic retry with feedback loops
3. **Transparency**: Explainable logs at every step
4. **Scalability**: Ready for parallel execution
5. **Maintainability**: Clear separation of concerns
6. **Extensibility**: Easy to add new nodes or modify behavior

**Status**: ✅ Production-ready foundation for Phase 2
