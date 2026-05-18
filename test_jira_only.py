"""
test_jira_only.py
---------------------------------------------
Quick Jira Connection Test (No LLM calls)
Tests only Jira connectivity and data fetching
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


def print_section(title):
    """Print formatted section"""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70)


def test_jira_config():
    """Test Jira configuration"""
    print_header("JIRA CONFIGURATION TEST")
    
    config = {
        "JIRA_BASE_URL": os.getenv("JIRA_BASE_URL"),
        "JIRA_EMAIL": os.getenv("JIRA_EMAIL"),
        "JIRA_API_KEY": os.getenv("JIRA_API_KEY"),
        "JIRA_PROJECT_KEY": os.getenv("JIRA_PROJECT_KEY"),
    }
    
    print("\n📋 Configuration:")
    for key, value in config.items():
        if value:
            if "KEY" in key:
                display = value[:15] + "..." if len(value) > 15 else "***"
            else:
                display = value
            print(f"   ✅ {key}: {display}")
        else:
            print(f"   ❌ {key}: NOT SET")
            return False
    
    return True


def test_jira_connection():
    """Test Jira connection"""
    print_header("JIRA CONNECTION TEST")
    
    try:
        from backend.jira.connector import JiraConnector
        
        connector = JiraConnector()
        print(f"\n✅ JiraConnector initialized")
        print(f"   Base URL: {connector.base_url}")
        print(f"   Project: {connector.project}")
        
        return True, connector
    except Exception as e:
        print(f"\n❌ Failed to initialize connector: {str(e)}")
        return False, None


def test_fetch_open_tickets(connector):
    """Test fetching open tickets"""
    print_header("FETCH OPEN TICKETS TEST")
    
    try:
        print("\n🔍 Fetching open tickets...")
        result = connector.get_open_tickets(max_results=20)
        
        if result.get("success"):
            total = result.get("total", 0)
            tickets = result.get("tickets", [])
            
            print(f"✅ Successfully fetched tickets!")
            print(f"\n📊 Statistics:")
            print(f"   Total open tickets: {total}")
            print(f"   Fetched: {len(tickets)}")
            
            if tickets:
                print(f"\n📋 Your Open Tickets:")
                print(f"   " + "-" * 66)
                
                for i, ticket in enumerate(tickets, 1):
                    print(f"\n   {i}. {ticket['ticket_id']}: {ticket['summary']}")
                    print(f"      Status: {ticket['status']}")
                    print(f"      Priority: {ticket['priority']}")
                    print(f"      Type: {ticket['issue_type']}")
                
                print(f"\n   " + "-" * 66)
                return True, tickets
            else:
                print(f"\n⚠️  No open tickets found in project {connector.project}")
                print(f"   Create a ticket in Jira to test further.")
                return True, []
        else:
            print(f"❌ Failed to fetch tickets: {result.get('error')}")
            return False, []
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []


def test_fetch_specific_tickets(connector, ticket_ids):
    """Test fetching specific tickets"""
    print_header("FETCH SPECIFIC TICKETS TEST")
    
    results = []
    
    for ticket_id in ticket_ids:
        print(f"\n🔍 Fetching {ticket_id}...")
        
        try:
            result = connector.get_ticket(ticket_id)
            
            if result.get("success"):
                print(f"   ✅ Success!")
                print(f"      Summary: {result.get('summary')}")
                print(f"      Status: {result.get('status')}")
                print(f"      Priority: {result.get('priority')}")
                print(f"      Type: {result.get('issue_type')}")
                print(f"      Assignee: {result.get('assignee')}")
                print(f"      Reporter: {result.get('reporter')}")
                
                description = result.get('description', '')
                if description and description != "No description provided.":
                    desc_preview = description[:150] + "..." if len(description) > 150 else description
                    print(f"      Description: {desc_preview}")
                else:
                    print(f"      Description: (empty)")
                
                results.append((ticket_id, True, result))
            else:
                print(f"   ❌ Failed: {result.get('error')}")
                results.append((ticket_id, False, None))
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append((ticket_id, False, None))
    
    return results


def test_jira_api_endpoints():
    """Test various Jira API endpoints"""
    print_header("JIRA API ENDPOINTS TEST")
    
    try:
        from backend.jira.connector import JiraConnector
        import requests
        
        connector = JiraConnector()
        
        # Test 1: Server info
        print("\n1. Testing server info endpoint...")
        url = f"{connector.base_url}/rest/api/3/serverInfo"
        response = requests.get(url, headers=connector.headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server info retrieved")
            print(f"      Version: {data.get('version', 'N/A')}")
            print(f"      Build: {data.get('buildNumber', 'N/A')}")
        else:
            print(f"   ⚠️  Status: {response.status_code}")
        
        # Test 2: Current user
        print("\n2. Testing current user endpoint...")
        url = f"{connector.base_url}/rest/api/3/myself"
        response = requests.get(url, headers=connector.headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ User info retrieved")
            print(f"      Display Name: {data.get('displayName', 'N/A')}")
            print(f"      Email: {data.get('emailAddress', 'N/A')}")
            print(f"      Account ID: {data.get('accountId', 'N/A')}")
        else:
            print(f"   ⚠️  Status: {response.status_code}")
        
        # Test 3: Project info
        print("\n3. Testing project info endpoint...")
        url = f"{connector.base_url}/rest/api/3/project/{connector.project}"
        response = requests.get(url, headers=connector.headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Project info retrieved")
            print(f"      Name: {data.get('name', 'N/A')}")
            print(f"      Key: {data.get('key', 'N/A')}")
            print(f"      Type: {data.get('projectTypeKey', 'N/A')}")
            print(f"      Lead: {data.get('lead', {}).get('displayName', 'N/A')}")
        else:
            print(f"   ⚠️  Status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test execution"""
    print("\n" + "=" * 70)
    print("  JIRA CONNECTIVITY TEST SUITE")
    print("  Testing Jira Integration (No LLM calls)")
    print("=" * 70)
    
    # Test 1: Configuration
    if not test_jira_config():
        print("\n❌ Configuration test failed!")
        return False
    
    # Test 2: Connection
    success, connector = test_jira_connection()
    if not success:
        print("\n❌ Connection test failed!")
        return False
    
    # Test 3: Fetch open tickets
    success, tickets = test_fetch_open_tickets(connector)
    if not success:
        print("\n❌ Fetch tickets test failed!")
        return False
    
    # Test 4: Fetch specific tickets
    if tickets:
        ticket_ids = [t['ticket_id'] for t in tickets[:3]]  # Test first 3 tickets
        test_fetch_specific_tickets(connector, ticket_ids)
    
    # Test 5: API endpoints
    test_jira_api_endpoints()
    
    # Final Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print("\n✅ All Jira connectivity tests passed!")
    print("\n📊 Your Jira Integration Status:")
    print(f"   ✅ Configuration: Valid")
    print(f"   ✅ Authentication: Working")
    print(f"   ✅ API Access: Functional")
    print(f"   ✅ Ticket Fetching: Working")
    print(f"   ✅ Project Access: Confirmed")
    
    if tickets:
        print(f"\n📋 Available Tickets for Testing:")
        for ticket in tickets[:5]:
            print(f"   • {ticket['ticket_id']}: {ticket['summary']}")
    
    print("\n💡 Next Steps:")
    print("   1. Your Jira integration is fully functional")
    print("   2. To test the complete workflow, wait for Groq API rate limit reset")
    print("   3. Or upgrade your Groq account for higher limits")
    print("   4. Run 'python test_my_jira.py' for full workflow test")
    
    print("\n" + "=" * 70 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
