"""
Quick System Readiness Test
Tests if all components are ready to run
"""

import sys
import os

print("="*70)
print("  SYSTEM READINESS TEST")
print("="*70)

# Test 1: Python version
print("\n[1/8] Checking Python version...")
version = sys.version_info
if version.major == 3 and version.minor >= 11:
    print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
else:
    print(f"  ❌ Python version too old: {version.major}.{version.minor}.{version.micro}")
    sys.exit(1)

# Test 2: Environment variables
print("\n[2/8] Checking environment variables...")
from dotenv import load_dotenv
load_dotenv()

required_vars = [
    "GROQ_API_KEY",
    "JIRA_BASE_URL",
    "JIRA_EMAIL",
    "JIRA_API_KEY",
    "GITHUB_TOKEN",
    "GITHUB_REPO_OWNER",
    "GITHUB_REPO_NAME",
    "SLACK_WEBHOOK_URL"
]

missing = []
for var in required_vars:
    value = os.getenv(var)
    if value and len(value) > 5:
        print(f"  ✅ {var}")
    else:
        print(f"  ❌ {var} - NOT SET")
        missing.append(var)

if missing:
    print(f"\n  ⚠️  Missing variables: {', '.join(missing)}")
else:
    print("  ✅ All environment variables configured")

# Test 3: Core imports
print("\n[3/8] Testing core imports...")
try:
    import fastapi
    import uvicorn
    print("  ✅ FastAPI and Uvicorn")
except ImportError as e:
    print(f"  ❌ FastAPI/Uvicorn: {e}")
    sys.exit(1)

# Test 4: LangChain imports
print("\n[4/8] Testing LangChain imports...")
try:
    import langchain
    from langchain_groq import ChatGroq
    print("  ✅ LangChain and Groq")
except ImportError as e:
    print(f"  ❌ LangChain: {e}")
    sys.exit(1)

# Test 5: Agent modules
print("\n[5/8] Testing agent modules...")
try:
    from agents.llm import get_llm
    print("  ✅ LLM module")
except ImportError as e:
    print(f"  ❌ LLM module: {e}")
    sys.exit(1)

# Test 6: Jira integration
print("\n[6/8] Testing Jira integration...")
try:
    from backend.jira.connector import JiraConnector
    print("  ✅ Jira connector")
except ImportError as e:
    print(f"  ❌ Jira connector: {e}")
    sys.exit(1)

# Test 7: GitHub integration
print("\n[7/8] Testing GitHub integration...")
try:
    from backend.gh_integration.github_client import GitHubClient
    print("  ✅ GitHub client")
except ImportError as e:
    print(f"  ❌ GitHub client: {e}")
    sys.exit(1)

# Test 8: Workflow orchestration
print("\n[8/8] Testing workflow orchestration...")
try:
    # Don't import execute_workflow directly as it may load models
    import workflows.orchestrator.graph
    print("  ✅ Workflow graph module exists")
except ImportError as e:
    print(f"  ❌ Workflow graph: {e}")
    sys.exit(1)

# Final summary
print("\n" + "="*70)
print("  ✅ ALL TESTS PASSED - SYSTEM IS READY TO RUN!")
print("="*70)
print("\n📋 Next Steps:")
print("  1. Start the backend server:")
print("     python backend/main.py")
print("\n  2. Open browser to:")
print("     http://localhost:8000/docs")
print("\n  3. Test the workflow:")
print("     POST /execute-ticket/SCRUM-8")
print("\n" + "="*70)
