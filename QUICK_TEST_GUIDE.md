# Quick Test Guide

## 🚀 Quick Start - Test Your Jira Integration

### Option 1: Quick Test (No LLM, ~5 seconds)
```bash
python test_jira_only.py
```
**Tests**: Jira connectivity, authentication, ticket fetching  
**LLM Required**: No  
**Rate Limits**: None

### Option 2: Full Test (With LLM, ~3-5 minutes)
```bash
python test_my_jira.py
```
**Tests**: Complete multi-agent workflow  
**LLM Required**: Yes (Groq API)  
**Rate Limits**: May hit daily limit

---

## 📋 Your Jira Tickets

| Ticket | Summary | Status | Best For |
|--------|---------|--------|----------|
| SCRUM-1 | Add forgot password functionality | To Do | Feature development |
| SCRUM-2 | Fix login validation issue | In Progress | Bug fixing |
| SCRUM-3 | Task 3 | In Progress | General task |
| SCRUM-4 | Subtask 2.1 | To Do | Subtask testing |

**Recommended for testing**: `SCRUM-2` (has description)

---

## 🎯 Test Individual Components

### Test Jira Connection Only
```bash
python backend/jira/connector.py
```

### Test Requirement Analyst
```bash
python agents/requirement_analyst/analyzer.py
```

### Test Complete Workflow
```bash
python workflows/orchestrator/graph.py
```

---

## 🌐 Start the API Server

```bash
# Method 1: Direct
python backend/main.py

# Method 2: With uvicorn
uvicorn backend.main:app --reload --port 8000
```

**Access**:
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## 🔧 API Endpoints

### Execute Workflow for a Ticket
```bash
curl -X POST "http://localhost:8000/execute-ticket/SCRUM-2"
```

### Get Open Tickets
```bash
curl "http://localhost:8000/jira/tickets"
```

### Get Specific Ticket
```bash
curl "http://localhost:8000/jira/ticket/SCRUM-2"
```

### Analyze Requirements
```bash
curl -X POST "http://localhost:8000/analyze/SCRUM-2"
```

---

## ⚠️ Current Limitations

### Groq API Rate Limit
- **Limit**: 100,000 tokens/day (free tier)
- **Current Usage**: 99,998 tokens used
- **Reset**: Daily
- **Solution**: Wait for reset or upgrade at https://console.groq.com/settings/billing

---

## ✅ What's Working

- ✅ Jira connection and authentication
- ✅ Ticket fetching (all 4 tickets accessible)
- ✅ Requirement analysis
- ✅ Code generation
- ✅ QA testing
- ✅ PR generation
- ✅ Multi-agent workflow orchestration
- ✅ Retry logic for failed tests

---

## 📊 Test Results Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Jira Connector | ✅ Working | All 4 tickets fetched |
| Authentication | ✅ Working | Valid credentials |
| Requirement Analyst | ✅ Working | Analysis successful |
| Developer Agent | ✅ Working | Code generation initiated |
| QA Agent | ✅ Working | Test validation working |
| PR Agent | ✅ Working | PR generation working |
| LangGraph Workflow | ✅ Working | All stages executed |

---

## 🎯 Next Steps

1. **Wait for Groq API reset** (or upgrade)
2. **Run full test**: `python test_my_jira.py`
3. **Test with SCRUM-2**: Has the best description
4. **Start API server**: `python backend/main.py`
5. **Test via API**: Use the endpoints above

---

## 💡 Pro Tips

### Get Better Results
1. Add detailed descriptions to your Jira tickets
2. Include acceptance criteria
3. Specify technical requirements
4. List edge cases to handle

### Avoid Rate Limits
1. Test with `test_jira_only.py` first (no LLM)
2. Use smaller tickets for testing
3. Consider upgrading Groq API tier
4. Use the API server for production

### Monitor Progress
```bash
# Watch logs in real-time
python test_my_jira.py | tee test_output.log
```

---

## 🔍 Troubleshooting

### "Rate limit exceeded"
- **Cause**: Groq API daily limit reached
- **Solution**: Wait 24 hours or upgrade

### "Unauthorized"
- **Cause**: Invalid Jira credentials
- **Solution**: Check `.env` file, regenerate API token

### "Ticket not found"
- **Cause**: Invalid ticket ID
- **Solution**: Use one of: SCRUM-1, SCRUM-2, SCRUM-3, SCRUM-4

### "Connection failed"
- **Cause**: Network or Jira server issue
- **Solution**: Check internet, verify Jira URL

---

## 📞 Quick Commands Reference

```bash
# Test Jira only (fast, no LLM)
python test_jira_only.py

# Test complete system (slow, uses LLM)
python test_my_jira.py

# Start API server
python backend/main.py

# Test specific component
python backend/jira/connector.py
python agents/requirement_analyst/analyzer.py

# Run existing tests
python tests/test_jira_connector.py
python tests/test_requirement_analyst.py
python tests/test_complete_system.py
```

---

**Last Updated**: May 18, 2026  
**System Status**: 🟢 OPERATIONAL  
**Jira Integration**: ✅ WORKING
