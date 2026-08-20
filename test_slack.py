"""
test_slack.py
Quick test script for Slack notifications with .env loading
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Import after loading .env
from agents.notification_agent import NotificationAgent

print("\n" + "=" * 70)
print("  SLACK NOTIFICATION TEST")
print("=" * 70)

# Check configuration
slack_url = os.getenv("SLACK_WEBHOOK_URL")
print(f"\n[CONFIG] Slack webhook configured: {bool(slack_url)}")

if slack_url:
    print(f"[CONFIG] Webhook URL: {slack_url[:50]}...")
    
    # Create agent
    agent = NotificationAgent()
    
    # Send test notification
    print("\n[TEST] Sending test notification to Slack...")
    result = agent.send_workflow_notification(
        ticket_id="TEST-1",
        workflow_status="completed",
        pr_url="https://github.com/amirtha-1412/autodevx-demo/pull/1",
        pr_number=1,
        test_status="PASSED",
        tests_passed=12,
        tests_total=12,
        quality_score=90,
        files_modified=["backend/routes/auth.py", "backend/models/user.py"],
        duration_seconds=125,
    )
    
    print(f"\n[RESULT] Success: {result.success}")
    print(f"[RESULT] Platform: {result.platform}")
    print(f"[RESULT] Message: {result.message}")
    
    if result.success:
        print("\n[SUCCESS] Notification sent successfully!")
        print("[INFO] Check your Slack channel for the message!")
    else:
        print(f"\n[FAILED]: {result.error}")
else:
    print("\n[FAILED] SLACK_WEBHOOK_URL not found in .env file")
    print("Make sure your .env file has:")
    print("SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...")

print("\n" + "=" * 70 + "\n")
