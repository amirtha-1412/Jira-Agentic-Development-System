"""
backend/jira/connector.py
─────────────────────────────────────────────
Jira Connector Module
Fetches ticket data from Jira REST API v3.
Uses auth headers from auth.py.
"""

import os
import requests
from dotenv import load_dotenv
from backend.jira.auth import get_auth_headers, get_jira_config

# ─── Load environment variables ─────────────
load_dotenv()


# ─────────────────────────────────────────────
# Jira Connector Class
# ─────────────────────────────────────────────

class JiraConnector:
    """
    Connects to Jira REST API and fetches ticket/issue data.
    """

    def __init__(self):
        config          = get_jira_config()
        self.base_url   = config["base_url"]
        self.project    = config["project"]
        self.headers    = get_auth_headers()

    # ─────────────────────────────────────────
    # Fetch Single Ticket
    # ─────────────────────────────────────────

    def get_ticket(self, ticket_id: str) -> dict:
        """
        Fetches full details of a Jira issue by ticket ID.
        Example: get_ticket("PROJ-101")

        Returns:
            dict with ticket fields or error info
        """
        url = f"{self.base_url}/rest/api/3/issue/{ticket_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection failed. Check JIRA_BASE_URL or internet."}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out. Jira server unreachable."}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

        if response.status_code == 200:
            data   = response.json()
            fields = data.get("fields", {})
            return {
                "success":     True,
                "ticket_id":   data.get("key"),
                "summary":     fields.get("summary", "No summary"),
                "description": self._extract_description(fields.get("description")),
                "status":      (fields.get("status") or {}).get("name", "Unknown"),
                "priority":    (fields.get("priority") or {}).get("name", "None"),
                "assignee":    self._extract_assignee(fields.get("assignee")),
                "reporter":    self._extract_assignee(fields.get("reporter")),
                "issue_type":  (fields.get("issuetype") or {}).get("name", "Task"),
                "labels":      fields.get("labels", []),
                "created":     fields.get("created", ""),
                "updated":     fields.get("updated", ""),
            }
        elif response.status_code == 404:
            return {"success": False, "error": f"Ticket '{ticket_id}' not found."}
        elif response.status_code == 401:
            return {"success": False, "error": "Unauthorized. Check JIRA_EMAIL and JIRA_API_KEY."}
        else:
            return {
                "success": False,
                "error":   f"HTTP {response.status_code}: {response.text}",
            }

    # ─────────────────────────────────────────
    # Fetch All Open Tickets in Project
    # ─────────────────────────────────────────

    def get_open_tickets(self, max_results: int = 10) -> dict:
        """
        Fetches all open (To Do / In Progress) tickets from the project.

        Returns:
            dict with list of ticket summaries
        """
        url    = f"{self.base_url}/rest/api/3/search/jql"
        params = {
            "jql":        f"project={self.project} AND statusCategory != Done ORDER BY created DESC",
            "maxResults": max_results,
            "fields":     "summary,status,priority,assignee,issuetype",
        }
        response = requests.get(url, headers=self.headers, params=params, timeout=10)

        if response.status_code == 200:
            data   = response.json()
            issues = data.get("issues", [])
            return {
                "success": True,
                "total":   data.get("total", 0),
                "tickets": [
                    {
                        "ticket_id":  issue["key"],
                        "summary":    issue["fields"].get("summary", ""),
                        "status":     (issue["fields"].get("status") or {}).get("name", ""),
                        "priority":   (issue["fields"].get("priority") or {}).get("name", "None"),
                        "issue_type": (issue["fields"].get("issuetype") or {}).get("name", "Task"),
                    }
                    for issue in issues
                ],
            }
        elif response.status_code == 401:
            return {"success": False, "error": "Unauthorized. Check your credentials."}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}

    # ─────────────────────────────────────────
    # Internal Helpers
    # ─────────────────────────────────────────

    def _extract_description(self, desc_field) -> str:
        """Extracts plain text from Jira's Atlassian Document Format (ADF)."""
        if not desc_field:
            return "No description provided."
        try:
            # ADF format: { "content": [{ "content": [{ "text": "..." }] }] }
            texts = []
            for block in desc_field.get("content", []):
                for item in block.get("content", []):
                    if item.get("type") == "text":
                        texts.append(item.get("text", ""))
            return " ".join(texts).strip() or "No description provided."
        except Exception:
            return str(desc_field)

    def _extract_assignee(self, person_field) -> str:
        """Safely extracts displayName from assignee/reporter field."""
        if not person_field:
            return "Unassigned"
        return person_field.get("displayName", "Unknown")


# ─────────────────────────────────────────────
# Connection Test
# ─────────────────────────────────────────────

def test_jira_connector():
    """
    Runs a full connection test:
    1. Validates environment config
    2. Fetches open tickets from the project
    """
    print("\n" + "=" * 50)
    print("  JIRA CONNECTOR — CONNECTION TEST")
    print("=" * 50)

    try:
        connector = JiraConnector()
        print(f"✅ Config loaded  → Project: {connector.project}")
        print(f"✅ Base URL       → {connector.base_url}")

        print("\n📋 Fetching open tickets...")
        result = connector.get_open_tickets(max_results=5)

        if result["success"]:
            print(f"✅ Connected! Total open tickets: {result['total']}")
            print("-" * 40)
            for t in result["tickets"]:
                print(f"  [{t['ticket_id']}] {t['summary']}")
                print(f"    Status: {t['status']} | Priority: {t['priority']} | Type: {t['issue_type']}")
        else:
            print(f"❌ Failed: {result['error']}")

    except EnvironmentError as e:
        print(f"❌ Config error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("=" * 50 + "\n")


if __name__ == "__main__":
    test_jira_connector()
