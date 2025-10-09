"""
Additional Slack bot handlers for MergeMind.
"""

import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import asyncio
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)


class MergeMindHandlers:
    """Additional handlers for MergeMind Slack bot."""
    
    def __init__(self, app: App, api_base_url: str):
        """Initialize handlers."""
        self.app = app
        self.api_base_url = api_base_url
        self._register_handlers()
    
    def _register_handlers(self):
        """Register additional handlers."""
        
        @self.app.command("/mergemind-help")
        async def handle_help_command(ack, respond, command):
            """Handle help command."""
            await ack()
            
            help_text = """
*MergeMind Slack Bot Commands:*

• `/mergemind mr <mr_id>` - Get insights about a merge request
• `/mergemind-help` - Show this help message

*Example:*
`/mergemind mr 123`

*Features:*
• Risk analysis and scoring
• AI-generated summaries
• Reviewer suggestions
• Pipeline status and next actions
• Blocking issue identification

*Need help?* Contact the MergeMind team.
            """
            
            await respond(help_text)
        
        @self.app.command("/mergemind-stats")
        async def handle_stats_command(ack, respond, command):
            """Handle stats command."""
            await ack()
            
            try:
                async with aiohttp.ClientSession() as session:
                    # Get MR list stats
                    async with session.get(f"{self.api_base_url}/mrs?limit=10") as response:
                        if response.status == 200:
                            mrs_data = await response.json()
                            mrs = mrs_data.get("items", [])
                        else:
                            await respond("Unable to fetch MR statistics.")
                            return
                    
                    # Get blockers
                    async with session.get(f"{self.api_base_url}/blockers/top?limit=5") as response:
                        if response.status == 200:
                            blockers_data = await response.json()
                            blockers = blockers_data
                        else:
                            blockers = []
                
                # Calculate stats
                total_mrs = len(mrs)
                open_mrs = len([mr for mr in mrs if mr.get("state") == "opened"])
                failed_pipelines = len([mr for mr in mrs if mr.get("pipeline_status") == "failed"])
                high_risk = len([mr for mr in mrs if mr.get("risk_band") == "High"])
                
                stats_text = f"""
*MergeMind Statistics:*

• *Total MRs:* {total_mrs}
• *Open MRs:* {open_mrs}
• *Failed Pipelines:* {failed_pipelines}
• *High Risk MRs:* {high_risk}
• *Blocking MRs:* {len(blockers)}

*Recent Activity:*
"""
                
                if mrs:
                    stats_text += "\n*Recent Merge Requests:*\n"
                    for mr in mrs[:5]:
                        risk_emoji = "🔴" if mr.get("risk_band") == "High" else "🟡" if mr.get("risk_band") == "Medium" else "🟢"
                        stats_text += f"• {risk_emoji} MR #{mr['mr_id']}: {mr['title'][:50]}...\n"
                
                if blockers:
                    stats_text += "\n*Top Blockers:*\n"
                    for blocker in blockers[:3]:
                        stats_text += f"• 🚫 MR #{blocker['mr_id']}: {blocker['blocking_reason']}\n"
                
                await respond(stats_text)
                
            except Exception as e:
                logger.error(f"Error handling stats command: {e}")
                await respond("Sorry, I encountered an error while fetching statistics.")
        
        @self.app.command("/mergemind-blockers")
        async def handle_blockers_command(ack, respond, command):
            """Handle blockers command."""
            await ack()
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.api_base_url}/blockers/top?limit=10") as response:
                        if response.status == 200:
                            blockers = await response.json()
                        else:
                            await respond("Unable to fetch blocking MRs.")
                            return
                
                if not blockers:
                    await respond("🎉 No blocking merge requests found!")
                    return
                
                blockers_text = f"*Top {len(blockers)} Blocking Merge Requests:*\n\n"
                
                for i, blocker in enumerate(blockers, 1):
                    risk_emoji = "🔴" if blocker.get("risk_band") == "High" else "🟡" if blocker.get("risk_band") == "Medium" else "🟢"
                    age = self.format_age(blocker.get("age_hours", 0))
                    
                    blockers_text += f"{i}. {risk_emoji} *MR #{blocker['mr_id']}*\n"
                    blockers_text += f"   • *Title:* {blocker['title']}\n"
                    blockers_text += f"   • *Author:* {blocker['author']}\n"
                    blockers_text += f"   • *Age:* {age}\n"
                    blockers_text += f"   • *Blocking Reason:* {blocker['blocking_reason']}\n"
                    blockers_text += f"   • *Risk:* {blocker['risk_band']} ({blocker['risk_score']})\n\n"
                
                await respond(blockers_text)
                
            except Exception as e:
                logger.error(f"Error handling blockers command: {e}")
                await respond("Sorry, I encountered an error while fetching blockers.")
        
        @self.app.event("app_home_opened")
        async def handle_app_home_opened(event, client):
            """Handle app home opened event."""
            try:
                # Publish home view
                await client.views_publish(
                    user_id=event["user"],
                    view={
                        "type": "home",
                        "blocks": [
                            {
                                "type": "header",
                                "text": {
                                    "type": "plain_text",
                                    "text": "MergeMind - AI-Powered Merge Request Analysis"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "Welcome to MergeMind! Get AI-powered insights about your GitLab merge requests."
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Available Commands:*\n• `/mergemind mr <mr_id>` - Get MR insights\n• `/mergemind-stats` - View statistics\n• `/mergemind-blockers` - List blocking MRs\n• `/mergemind-help` - Show help"
                                }
                            },
                            {
                                "type": "context",
                                "elements": [
                                    {
                                        "type": "mrkdwn",
                                        "text": f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                    }
                                ]
                            }
                        ]
                    }
                )
            except Exception as e:
                logger.error(f"Error handling app home opened: {e}")
    
    def format_age(self, hours: float) -> str:
        """Format age in hours to human-readable format."""
        if hours < 24:
            return f"{int(hours)}h"
        else:
            return f"{int(hours / 24)}d"
