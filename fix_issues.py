"""
fix_issues.py
---------------------------------------------
Diagnostic and Fix Script
Identifies and resolves common issues with the system
"""

import sys
import io
import os
from dotenv import load_dotenv

# Ensure UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Load environment variables
load_dotenv()


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_environment():
    """Check environment configuration"""
    print_header("CHECKING ENVIRONMENT CONFIGURATION")
    
    issues = []
    warnings = []
    
    # Check required variables
    required_vars = {
        "GROQ_API_KEY": "LLM API key for AI agents",
        "JIRA_BASE_URL": "Your Jira instance URL",
        "JIRA_EMAIL": "Your Jira email",
        "JIRA_API_KEY": "Your Jira API token",
        "JIRA_PROJECT_KEY": "Your Jira project key",
    }
    
    print("\n📋 Required Variables:")
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            print(f"   ✅ {var_name}: Set")
        else:
            print(f"   ❌ {var_name}: NOT SET")
            issues.append(f"Missing {var_name} - {description}")
    
    # Check optional variables
    optional_vars = {
        "GITHUB_TOKEN": "For GitHub integration (optional)",
        "OPENAI_API_KEY": "For OpenAI fallback (optional)",
    }
    
    print("\n📋 Optional Variables:")
    for var_name, description in optional_vars.items():
        value = os.getenv(var_name)
        if value:
            print(f"   ✅ {var_name}: Set")
        else:
            print(f"   ⚠️  {var_name}: Not set - {description}")
            warnings.append(f"{var_name} not set - {description}")
    
    return issues, warnings


def check_groq_api():
    """Check Groq API status"""
    print_header("CHECKING GROQ API")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("   ❌ GROQ_API_KEY not set")
        return ["GROQ_API_KEY not configured"]
    
    print(f"   ✅ API Key: {api_key[:15]}...")
    
    # Test API connection
    print("\n   🔍 Testing API connection...")
    try:
        from agents.llm import call_llm
        
        response = call_llm(
            user_prompt="Say 'OK' and nothing else.",
            system_prompt="You are a test assistant.",
            use_fallback=True,
        )
        
        print(f"   ✅ API Response: {response}")
        print(f"   ✅ Groq API is working!")
        return []
        
    except Exception as e:
        error_str = str(e)
        print(f"   ❌ API Error: {error_str}")
        
        if "rate_limit" in error_str.lower() or "429" in error_str:
            print("\n   ⚠️  RATE LIMIT DETECTED")
            print("   Solutions:")
            print("   1. Wait for daily reset (resets every 24 hours)")
            print("   2. Upgrade to Groq Dev Tier")
            print("   3. Add OPENAI_API_KEY to .env for fallback")
            print("   4. Visit: https://console.groq.com/settings/billing")
            return ["Groq API rate limit reached"]
        elif "401" in error_str or "unauthorized" in error_str.lower():
            print("\n   ❌ AUTHENTICATION FAILED")
            print("   Solutions:")
            print("   1. Check your GROQ_API_KEY in .env")
            print("   2. Generate new key at: https://console.groq.com/keys")
            return ["Invalid Groq API key"]
        else:
            return [f"Groq API error: {error_str}"]


def check_jira_connection():
    """Check Jira connection"""
    print_header("CHECKING JIRA CONNECTION")
    
    required = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_KEY", "JIRA_PROJECT_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"   ❌ Missing variables: {', '.join(missing)}")
        return [f"Missing Jira configuration: {', '.join(missing)}"]
    
    print("   ✅ All Jira variables set")
    
    # Test connection
    print("\n   🔍 Testing Jira connection...")
    try:
        from backend.jira.connector import JiraConnector
        
        connector = JiraConnector()
        result = connector.get_open_tickets(max_results=1)
        
        if result.get("success"):
            print(f"   ✅ Connected to: {connector.base_url}")
            print(f"   ✅ Project: {connector.project}")
            print(f"   ✅ Jira connection working!")
            return []
        else:
            error = result.get("error", "Unknown error")
            print(f"   ❌ Connection failed: {error}")
            
            if "401" in error or "Unauthorized" in error:
                print("\n   ❌ AUTHENTICATION FAILED")
                print("   Solutions:")
                print("   1. Check JIRA_EMAIL and JIRA_API_KEY in .env")
                print("   2. Generate new API token at:")
                print("      https://id.atlassian.com/manage-profile/security/api-tokens")
                return ["Invalid Jira credentials"]
            elif "404" in error:
                print("\n   ❌ PROJECT NOT FOUND")
                print("   Solutions:")
                print("   1. Check JIRA_PROJECT_KEY in .env")
                print("   2. Verify project exists in your Jira")
                return ["Jira project not found"]
            else:
                return [f"Jira connection error: {error}"]
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return [f"Jira connection error: {str(e)}"]


def check_dependencies():
    """Check Python dependencies"""
    print_header("CHECKING DEPENDENCIES")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "langchain",
        "langchain_groq",
        "langchain_core",
        "langgraph",
        "requests",
        "python-dotenv",
    ]
    
    missing = []
    print("\n📦 Required Packages:")
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}: NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n   ⚠️  Missing packages: {', '.join(missing)}")
        print(f"   💡 Install with: pip install {' '.join(missing)}")
        return [f"Missing packages: {', '.join(missing)}"]
    
    return []


def suggest_fixes(all_issues):
    """Suggest fixes for identified issues"""
    print_header("SUGGESTED FIXES")
    
    if not all_issues:
        print("\n   ✅ No issues found! System is healthy.")
        return
    
    print("\n🔧 Issues Found:")
    for i, issue in enumerate(all_issues, 1):
        print(f"   {i}. {issue}")
    
    print("\n💡 Quick Fixes:")
    
    # Categorize issues
    has_env_issues = any("Missing" in issue and "GROQ" not in issue and "JIRA" not in issue for issue in all_issues)
    has_groq_issues = any("Groq" in issue or "rate limit" in issue.lower() for issue in all_issues)
    has_jira_issues = any("Jira" in issue for issue in all_issues)
    has_dependency_issues = any("package" in issue.lower() for issue in all_issues)
    
    if has_dependency_issues:
        print("\n   1️⃣  Install Missing Dependencies:")
        print("      pip install -r requirements.txt")
    
    if has_env_issues or has_groq_issues or has_jira_issues:
        print("\n   2️⃣  Update .env File:")
        print("      Edit .env and add missing variables")
        print("      Template:")
        print("      ```")
        print("      GROQ_API_KEY=your_groq_key_here")
        print("      JIRA_BASE_URL=https://your-domain.atlassian.net")
        print("      JIRA_EMAIL=your-email@example.com")
        print("      JIRA_API_KEY=your_jira_api_token")
        print("      JIRA_PROJECT_KEY=YOUR_PROJECT")
        print("      ```")
    
    if has_groq_issues:
        print("\n   3️⃣  Groq API Rate Limit:")
        print("      Option A: Wait for daily reset")
        print("      Option B: Upgrade at https://console.groq.com/settings/billing")
        print("      Option C: Add OpenAI fallback (add OPENAI_API_KEY to .env)")
    
    if has_jira_issues:
        print("\n   4️⃣  Jira Connection Issues:")
        print("      - Verify credentials at: https://id.atlassian.com/manage-profile/security/api-tokens")
        print("      - Check project key in Jira")
        print("      - Ensure API token has correct permissions")


def main():
    """Main diagnostic routine"""
    print("\n" + "=" * 70)
    print("  SYSTEM DIAGNOSTIC & FIX TOOL")
    print("  Checking for common issues...")
    print("=" * 70)
    
    all_issues = []
    all_warnings = []
    
    # Run checks
    issues, warnings = check_environment()
    all_issues.extend(issues)
    all_warnings.extend(warnings)
    
    if not issues:  # Only check APIs if env is configured
        issues = check_groq_api()
        all_issues.extend(issues)
        
        issues = check_jira_connection()
        all_issues.extend(issues)
    
    issues = check_dependencies()
    all_issues.extend(issues)
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    if not all_issues:
        print("\n   ✅ ALL CHECKS PASSED!")
        print("   🎉 Your system is healthy and ready to use!")
        
        if all_warnings:
            print("\n   ℹ️  Optional Improvements:")
            for warning in all_warnings:
                print(f"      • {warning}")
    else:
        print(f"\n   ⚠️  Found {len(all_issues)} issue(s)")
        suggest_fixes(all_issues)
    
    print("\n" + "=" * 70)
    print("  DIAGNOSTIC COMPLETE")
    print("=" * 70 + "\n")
    
    return len(all_issues) == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
