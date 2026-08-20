"""
Diagnostic Script - Find Errors in System
Checks all critical components for issues
"""

import sys
import os

print("\n" + "=" * 70)
print("  SYSTEM DIAGNOSTIC - ERROR DETECTION")
print("=" * 70 + "\n")

# Test 1: Python version
print("[1/10] Checking Python version...")
print(f"  Python: {sys.version}")
if sys.version_info < (3, 9):
    print("  ⚠️  WARNING: Python 3.9+ recommended")
else:
    print("  ✅ Python version OK")
print()

# Test 2: Virtual environment
print("[2/10] Checking virtual environment...")
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("  ✅ Virtual environment active")
else:
    print("  ⚠️  WARNING: Not running in virtual environment")
print()

# Test 3: Critical imports
print("[3/10] Testing critical imports...")
critical_imports = [
    "fastapi",
    "uvicorn",
    "dotenv",
    "langchain_groq",
    "langchain_core",
    "chromadb",
    "pytest",
]

for module in critical_imports:
    try:
        __import__(module)
        print(f"  ✅ {module}")
    except ImportError as e:
        print(f"  ❌ {module} - NOT INSTALLED")
        print(f"     Error: {e}")
print()

# Test 4: Environment variables
print("[4/10] Checking environment variables...")
from dotenv import load_dotenv
load_dotenv()

required_vars = [
    "GROQ_API_KEY",
    "JIRA_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
]

for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"  ✅ {var} - Set ({len(value)} chars)")
    else:
        print(f"  ⚠️  {var} - NOT SET")
print()

# Test 5: File existence
print("[5/10] Checking critical files...")
critical_files = [
    "backend/main.py",
    "agents/llm.py",
    "agents/developer_agent/developer_agent.py",
    "agents/qa_agent/qa_agent.py",
    "agents/pr_agent/pr_generator.py",
    "requirements.txt",
    ".env",
]

for filepath in critical_files:
    if os.path.exists(filepath):
        print(f"  ✅ {filepath}")
    else:
        print(f"  ❌ {filepath} - MISSING")
print()

# Test 6: Pytest availability
print("[6/10] Checking pytest...")
try:
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--version"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode == 0:
        print(f"  ✅ Pytest available: {result.stdout.strip()}")
    else:
        print(f"  ❌ Pytest not working")
        print(f"     Error: {result.stderr}")
except Exception as e:
    print(f"  ❌ Pytest check failed: {e}")
print()

# Test 7: LLM module syntax
print("[7/10] Testing LLM module...")
try:
    from agents.llm import call_llm, get_llm
    print("  ✅ LLM module imports successfully")
    
    # Check for rate limit protection
    import agents.llm as llm_module
    if hasattr(llm_module, 'RATE_LIMIT_COOLDOWN'):
        print(f"  ✅ Rate limit protection present (cooldown: {llm_module.RATE_LIMIT_COOLDOWN}s)")
    else:
        print("  ⚠️  Rate limit protection not found")
        
    if hasattr(llm_module, '_last_api_call_time'):
        print("  ✅ Rate limit tracking variable present")
    else:
        print("  ⚠️  Rate limit tracking variable not found")
        
except Exception as e:
    print(f"  ❌ LLM module error: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 8: Developer agent syntax
print("[8/10] Testing Developer Agent...")
try:
    from agents.developer_agent import DeveloperAgent
    print("  ✅ Developer Agent imports successfully")
except Exception as e:
    print(f"  ❌ Developer Agent error: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 9: QA agent syntax
print("[9/10] Testing QA Agent...")
try:
    from agents.qa_agent import QAAgent
    print("  ✅ QA Agent imports successfully")
except Exception as e:
    print(f"  ❌ QA Agent error: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 10: Backend main
print("[10/10] Testing Backend Main...")
try:
    # Don't actually import (would start server), just compile
    with open("backend/main.py", "r", encoding="utf-8") as f:
        code = f.read()
    compile(code, "backend/main.py", "exec")
    print("  ✅ Backend main.py syntax valid")
except Exception as e:
    print(f"  ❌ Backend main.py error: {e}")
    import traceback
    traceback.print_exc()
print()

# Summary
print("=" * 70)
print("  DIAGNOSTIC COMPLETE")
print("=" * 70)
print("\nIf you see any ❌ or ⚠️  above, those are the issues to fix.")
print("\nCommon fixes:")
print("  - Missing imports: pip install -r requirements.txt")
print("  - Missing .env: Copy .env.example to .env and fill values")
print("  - Syntax errors: Check the file mentioned in the error")
print()
