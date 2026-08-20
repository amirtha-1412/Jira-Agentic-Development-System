"""
agents/notification_agent/notification_agent.py
---------------------------------------------
Notification Agent - Slack & Teams Integration
Sends notifications when workflows complete.

Features:
  - Slack webhook integration
  - Microsoft Teams webhook integration
  - Rich message formatting
  - Status indicators ([OK] [FAIL] [WARN])
  - PR links and details
  - Test results summary
  - Quality metrics
"""

import requests
from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime
import os


# ─────────────────────────────────────────────
# Notification Result
# ─────────────────────────────────────────────

@dataclass
class NotificationResult:
    """Result of notification sending."""
    success: bool
    platform: str  # slack, teams, both
    message: str
    error: str = ""
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "platform": self.platform,
            "message": self.message,
            "error": self.error,
        }


# ─────────────────────────────────────────────
# Notification Agent
# ─────────────────────────────────────────────

class NotificationAgent:
    """
    Sends notifications to Slack and Microsoft Teams.
    Notifies team when workflows complete.
    """
    
    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        teams_webhook_url: Optional[str] = None,
    ):
        """
        Initialize notification agent.
        
        Args:
            slack_webhook_url: Slack webhook URL (or from env SLACK_WEBHOOK_URL)
            teams_webhook_url: Teams webhook URL (or from env TEAMS_WEBHOOK_URL)
        """
        self.slack_webhook_url = slack_webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.teams_webhook_url = teams_webhook_url or os.getenv("TEAMS_WEBHOOK_URL")
    
    def is_configured(self) -> Dict[str, bool]:
        """Check which platforms are configured."""
        return {
            "slack": bool(self.slack_webhook_url),
            "teams": bool(self.teams_webhook_url),
        }
    
    # ─────────────────────────────────────────
    # Main Notification Method
    # ─────────────────────────────────────────
    
    def send_workflow_notification(
        self,
        ticket_id: str,
        workflow_status: str,
        pr_url: Optional[str] = None,
        pr_number: Optional[int] = None,
        test_status: str = "UNKNOWN",
        tests_passed: int = 0,
        tests_total: int = 0,
        quality_score: int = 0,
        files_modified: List[str] = None,
        duration_seconds: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> NotificationResult:
        """
        Send workflow completion notification.
        
        Args:
            ticket_id: Jira ticket ID
            workflow_status: completed, failed, partial
            pr_url: GitHub PR URL
            pr_number: GitHub PR number
            test_status: PASSED, FAILED, PARTIAL
            tests_passed: Number of tests passed
            tests_total: Total number of tests
            quality_score: Code quality score (0-100)
            files_modified: List of modified files
            duration_seconds: Workflow duration
            error_message: Error message if failed
        
        Returns:
            NotificationResult with send status
        """
        files_modified = files_modified or []
        
        print(f"\n  [NotificationAgent] Sending notifications for {ticket_id}...")
        
        # Determine which platforms to notify
        config = self.is_configured()
        platforms = []
        
        if config["slack"]:
            platforms.append("slack")
        if config["teams"]:
            platforms.append("teams")
        
        if not platforms:
            print(f"  [NotificationAgent] [WARN] No notification platforms configured")
            return NotificationResult(
                success=False,
                platform="none",
                message="No notification platforms configured",
                error="Set SLACK_WEBHOOK_URL or TEAMS_WEBHOOK_URL in .env",
            )
        
        # Send to each platform
        results = []
        
        if "slack" in platforms:
            slack_result = self._send_slack_notification(
                ticket_id=ticket_id,
                workflow_status=workflow_status,
                pr_url=pr_url,
                pr_number=pr_number,
                test_status=test_status,
                tests_passed=tests_passed,
                tests_total=tests_total,
                quality_score=quality_score,
                files_modified=files_modified,
                duration_seconds=duration_seconds,
                error_message=error_message,
            )
            results.append(slack_result)
        
        if "teams" in platforms:
            teams_result = self._send_teams_notification(
                ticket_id=ticket_id,
                workflow_status=workflow_status,
                pr_url=pr_url,
                pr_number=pr_number,
                test_status=test_status,
                tests_passed=tests_passed,
                tests_total=tests_total,
                quality_score=quality_score,
                files_modified=files_modified,
                duration_seconds=duration_seconds,
                error_message=error_message,
            )
            results.append(teams_result)
        
        # Aggregate results
        all_success = all(r.success for r in results)
        platform_str = " & ".join(platforms)
        
        if all_success:
            print(f"  [NotificationAgent] [OK] Notifications sent to {platform_str}")
        else:
            print(f"  [NotificationAgent] [WARN] Some notifications failed")
        
        return NotificationResult(
            success=all_success,
            platform=platform_str,
            message=f"Sent to {platform_str}",
            error="" if all_success else "Some notifications failed",
        )
    
    # ─────────────────────────────────────────
    # Slack Integration
    # ─────────────────────────────────────────
    
    def _send_slack_notification(
        self,
        ticket_id: str,
        workflow_status: str,
        pr_url: Optional[str],
        pr_number: Optional[int],
        test_status: str,
        tests_passed: int,
        tests_total: int,
        quality_score: int,
        files_modified: List[str],
        duration_seconds: Optional[int],
        error_message: Optional[str],
    ) -> NotificationResult:
        """Send notification to Slack."""
        
        try:
            # Build Slack message
            message = self._build_slack_message(
                ticket_id=ticket_id,
                workflow_status=workflow_status,
                pr_url=pr_url,
                pr_number=pr_number,
                test_status=test_status,
                tests_passed=tests_passed,
                tests_total=tests_total,
                quality_score=quality_score,
                files_modified=files_modified,
                duration_seconds=duration_seconds,
                error_message=error_message,
            )
            
            # Send to Slack
            response = requests.post(
                self.slack_webhook_url,
                json=message,
                timeout=10,
            )
            
            if response.status_code == 200:
                print(f"  [NotificationAgent] [OK] Slack notification sent")
                return NotificationResult(
                    success=True,
                    platform="slack",
                    message="Slack notification sent",
                )
            else:
                print(f"  [NotificationAgent] [FAIL] Slack error: {response.status_code}")
                return NotificationResult(
                    success=False,
                    platform="slack",
                    message="Slack notification failed",
                    error=f"HTTP {response.status_code}: {response.text}",
                )
        
        except Exception as e:
            print(f"  [NotificationAgent] [ERROR] Slack exception: {e}")
            return NotificationResult(
                success=False,
                platform="slack",
                message="Slack notification failed",
                error=str(e),
            )
    
    def _build_slack_message(
        self,
        ticket_id: str,
        workflow_status: str,
        pr_url: Optional[str],
        pr_number: Optional[int],
        test_status: str,
        tests_passed: int,
        tests_total: int,
        quality_score: int,
        files_modified: List[str],
        duration_seconds: Optional[int],
        error_message: Optional[str],
    ) -> dict:
        """Build Slack message payload."""
        
        # Status emoji and color based on workflow and test status
        if workflow_status == "completed":
            if test_status == "PASSED":
                status_emoji = "✅"
                color = "good"
                status_text = "Workflow Completed Successfully"
            elif test_status == "VALIDATED":
                status_emoji = "✅"
                color = "good"
                status_text = "Workflow Completed (Validation Mode)"
            elif test_status == "PARTIAL":
                status_emoji = "⚠️"
                color = "warning"
                status_text = "Workflow Completed with Warnings"
            else:
                status_emoji = "❌"
                color = "danger"
                status_text = "Workflow Completed (Tests Failed)"
        else:
            status_emoji = "❌"
            color = "danger"
            status_text = "Workflow Failed"
        
        # Build message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} {status_text}",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Ticket:*\n{ticket_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{workflow_status.upper()}"
                    }
                ]
            }
        ]
        
        # PR information
        if pr_url and pr_number:
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*PR:*\n<{pr_url}|#{pr_number}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Files:*\n{len(files_modified)} modified"
                    }
                ]
            })
        
        # Test results - handle VALIDATED status specially
        if test_status == "VALIDATED":
            test_emoji = "✅"
            test_display = f"{test_emoji} Validated (no tests executed)"
        elif test_status == "PASSED":
            test_emoji = "✅"
            test_display = f"{test_emoji} {tests_passed}/{tests_total} passed"
        elif test_status == "FAILED":
            test_emoji = "❌"
            test_display = f"{test_emoji} {tests_passed}/{tests_total} passed"
        else:  # PARTIAL
            test_emoji = "⚠️"
            test_display = f"{test_emoji} {tests_passed}/{tests_total} passed"
        
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Tests:*\n{test_display}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Quality:*\n{quality_score}/100"
                }
            ]
        })
        
        # Duration
        if duration_seconds:
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Duration:* {minutes}m {seconds}s"
                }
            })
        
        # Error message
        if error_message:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{error_message[:200]}```"
                }
            })
        
        # Action buttons
        if pr_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View PR",
                            "emoji": True
                        },
                        "url": pr_url,
                        "style": "primary"
                    }
                ]
            })
        
        # Divider
        blocks.append({"type": "divider"})
        
        # Footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"[BOT] Jira Agentic Dev System • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        return {
            "blocks": blocks,
            "attachments": [
                {
                    "color": color,
                    "fallback": f"{status_text}: {ticket_id}"
                }
            ]
        }
    
    # ─────────────────────────────────────────
    # Microsoft Teams Integration
    # ─────────────────────────────────────────
    
    def _send_teams_notification(
        self,
        ticket_id: str,
        workflow_status: str,
        pr_url: Optional[str],
        pr_number: Optional[int],
        test_status: str,
        tests_passed: int,
        tests_total: int,
        quality_score: int,
        files_modified: List[str],
        duration_seconds: Optional[int],
        error_message: Optional[str],
    ) -> NotificationResult:
        """Send notification to Microsoft Teams."""
        
        try:
            # Build Teams message
            message = self._build_teams_message(
                ticket_id=ticket_id,
                workflow_status=workflow_status,
                pr_url=pr_url,
                pr_number=pr_number,
                test_status=test_status,
                tests_passed=tests_passed,
                tests_total=tests_total,
                quality_score=quality_score,
                files_modified=files_modified,
                duration_seconds=duration_seconds,
                error_message=error_message,
            )
            
            # Send to Teams
            response = requests.post(
                self.teams_webhook_url,
                json=message,
                timeout=10,
            )
            
            if response.status_code == 200:
                print(f"  [NotificationAgent] [OK] Teams notification sent")
                return NotificationResult(
                    success=True,
                    platform="teams",
                    message="Teams notification sent",
                )
            else:
                print(f"  [NotificationAgent] [FAIL] Teams error: {response.status_code}")
                return NotificationResult(
                    success=False,
                    platform="teams",
                    message="Teams notification failed",
                    error=f"HTTP {response.status_code}: {response.text}",
                )
        
        except Exception as e:
            print(f"  [NotificationAgent] [ERROR] Teams exception: {e}")
            return NotificationResult(
                success=False,
                platform="teams",
                message="Teams notification failed",
                error=str(e),
            )
    
    def _build_teams_message(
        self,
        ticket_id: str,
        workflow_status: str,
        pr_url: Optional[str],
        pr_number: Optional[int],
        test_status: str,
        tests_passed: int,
        tests_total: int,
        quality_score: int,
        files_modified: List[str],
        duration_seconds: Optional[int],
        error_message: Optional[str],
    ) -> dict:
        """Build Microsoft Teams message payload (Adaptive Card)."""
        
        # Status emoji, color, and text based on workflow and test status
        if workflow_status == "completed":
            if test_status == "PASSED":
                status_emoji = "✅"
                theme_color = "00FF00"  # Green
                status_text = "Workflow Completed Successfully"
            elif test_status == "VALIDATED":
                status_emoji = "✅"
                theme_color = "00FF00"  # Green
                status_text = "Workflow Completed (Validation Mode)"
            elif test_status == "PARTIAL":
                status_emoji = "⚠️"
                theme_color = "FFA500"  # Orange
                status_text = "Workflow Completed with Warnings"
            else:
                status_emoji = "❌"
                theme_color = "FF0000"  # Red
                status_text = "Workflow Completed (Tests Failed)"
        else:
            status_emoji = "[FAIL]"
            theme_color = "FF0000"  # Red
            status_text = "Workflow Failed"
        
        # Build facts
        facts = [
            {"name": "Ticket", "value": ticket_id},
            {"name": "Status", "value": workflow_status.upper()},
        ]
        
        if pr_url and pr_number:
            facts.append({"name": "PR", "value": f"#{pr_number}"})
            facts.append({"name": "Files Modified", "value": str(len(files_modified))})
        
        # Test results - handle VALIDATED status specially
        if test_status == "VALIDATED":
            test_display = "✅ Validated (no tests executed)"
        elif test_status == "PASSED":
            test_display = f"✅ {tests_passed}/{tests_total} passed"
        elif test_status == "FAILED":
            test_display = f"❌ {tests_passed}/{tests_total} passed"
        else:  # PARTIAL
            test_display = f"⚠️ {tests_passed}/{tests_total} passed"
        
        facts.append({"name": "Tests", "value": test_display})
        facts.append({"name": "Quality Score", "value": f"{quality_score}/100"})
        
        if duration_seconds:
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            facts.append({"name": "Duration", "value": f"{minutes}m {seconds}s"})
        
        # Build sections
        sections = [
            {
                "activityTitle": f"{status_emoji} {status_text}",
                "activitySubtitle": f"Jira Agentic Dev System • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "facts": facts,
            }
        ]
        
        # Add error section if present
        if error_message:
            sections.append({
                "activityTitle": "[FAIL] Error Details",
                "text": f"```\n{error_message[:200]}\n```"
            })
        
        # Build potential actions
        potential_actions = []
        if pr_url:
            potential_actions.append({
                "@type": "OpenUri",
                "name": "View PR",
                "targets": [
                    {"os": "default", "uri": pr_url}
                ]
            })
        
        # Build message card
        message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"{status_text}: {ticket_id}",
            "themeColor": theme_color,
            "sections": sections,
        }
        
        if potential_actions:
            message["potentialAction"] = potential_actions
        
        return message


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    
    print("\n" + "=" * 70)
    print("  NOTIFICATION AGENT - TEST RUN")
    print("=" * 70)
    
    # Create agent
    agent = NotificationAgent()
    
    # Check configuration
    config = agent.is_configured()
    print(f"\n[CONFIG] Slack configured: {config['slack']}")
    print(f"[CONFIG] Teams configured: {config['teams']}")
    
    if not any(config.values()):
        print("\n[INFO] No webhooks configured. Set SLACK_WEBHOOK_URL or TEAMS_WEBHOOK_URL in .env")
        print("[INFO] Example:")
        print("  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
        print("  TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/WEBHOOK/URL")
    else:
        # Send test notification
        print("\n[TEST] Sending test notification...")
        result = agent.send_workflow_notification(
            ticket_id="TEST-1",
            workflow_status="completed",
            pr_url="https://github.com/user/repo/pull/1",
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
        if result.error:
            print(f"[RESULT] Error: {result.error}")
    
    print("\n" + "=" * 70)
    print("  [DONE] Notification agent test complete")
    print("=" * 70 + "\n")
