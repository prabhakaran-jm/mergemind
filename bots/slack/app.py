"""
Slack bot application for MergeMind.
Handles slash commands and provides merge request insights.
"""

import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import asyncio
import aiohttp
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# API base URL
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080/api/v1")


class MergeMindSlackBot:
    """Slack bot for MergeMind integration."""
    
    def __init__(self):
        """Initialize the bot."""
        self.api_base_url = API_BASE_URL
        
    async def fetch_mr_data(self, mr_id: int) -> dict:
        """Fetch MR data from API."""
        try:
            async with aiohttp.ClientSession() as session:
                # Get MR context
                async with session.get(f"{self.api_base_url}/mr/{mr_id}/context") as response:
                    if response.status == 200:
                        context = await response.json()
                    else:
                        return None
                
                # Get summary
                async with session.post(f"{self.api_base_url}/mr/{mr_id}/summary") as response:
                    if response.status == 200:
                        summary = await response.json()
                    else:
                        summary = {"summary": ["Summary unavailable"], "risks": [], "tests": []}
                
                # Get reviewers
                async with session.get(f"{self.api_base_url}/mr/{mr_id}/reviewers") as response:
                    if response.status == 200:
                        reviewers_data = await response.json()
                        reviewers = reviewers_data.get("reviewers", [])
                    else:
                        reviewers = []
                
                return {
                    "context": context,
                    "summary": summary,
                    "reviewers": reviewers
                }
                
        except Exception as e:
            logger.error(f"Failed to fetch MR data: {e}")
            return None
    
    def format_mr_response(self, mr_data: dict) -> list:
        """Format MR data into Slack blocks."""
        context = mr_data["context"]
        summary = mr_data["summary"]
        reviewers = mr_data["reviewers"]
        
        blocks = []
        
        # Header block
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Merge Request #{context['mr_id']}: {context['title']}"
            }
        })
        
        # Context block
        context_text = f"*Author:* {context['author']['name']}\n"
        context_text += f"*Age:* {self.format_age(context['age_hours'])}\n"
        context_text += f"*State:* {context['state']}\n"
        context_text += f"*Pipeline:* {context['last_pipeline']['status']}\n"
        context_text += f"*Approvals Left:* {context['approvals_left']}\n"
        context_text += f"*Changes:* +{context['size']['additions']} / -{context['size']['deletions']}"
        
        if context.get('web_url'):
            context_text += f"\n*Link:* <{context['web_url']}|View MR>"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": context_text
            }
        })
        
        # Risk block
        risk = context["risk"]
        risk_color = self.get_risk_color(risk["band"])
        risk_text = f"*Risk Level:* {risk['band']} ({risk['score']}/100)\n"
        if risk["reasons"]:
            risk_text += "*Reasons:*\n" + "\n".join([f"• {reason}" for reason in risk["reasons"]])
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": risk_text
            }
        })
        
        # Summary block
        if summary["summary"]:
            summary_text = "*AI Summary:*\n" + "\n".join([f"• {item}" for item in summary["summary"]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": summary_text
                }
            })
        
        # Risks block
        if summary["risks"]:
            risks_text = "*Potential Risks:*\n" + "\n".join([f"⚠️ {risk}" for risk in summary["risks"]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": risks_text
                }
            })
        
        # Reviewers block
        if reviewers:
            reviewers_text = "*Suggested Reviewers:*\n"
            for reviewer in reviewers[:3]:  # Limit to 3 reviewers
                reviewers_text += f"• *{reviewer['name']}* - {reviewer['reason']}\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": reviewers_text
                }
            })
        
        # Next actions block
        next_actions = self.get_next_actions(context, summary)
        if next_actions:
            actions_text = "*Suggested Next Actions:*\n" + "\n".join([f"• {action}" for action in next_actions])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": actions_text
                }
            })
        
        # Footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Generated by MergeMind at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        return blocks
    
    def format_age(self, hours: float) -> str:
        """Format age in hours to human-readable format."""
        if hours < 24:
            return f"{int(hours)}h"
        else:
            return f"{int(hours / 24)}d"
    
    def get_risk_color(self, band: str) -> str:
        """Get color for risk band."""
        colors = {
            "Low": "good",
            "Medium": "warning", 
            "High": "danger"
        }
        return colors.get(band, "good")
    
    def get_next_actions(self, context: dict, summary: dict) -> list:
        """Get suggested next actions based on MR context."""
        actions = []
        
        if context["last_pipeline"]["status"] == "failed":
            actions.append("Rerun the failed pipeline")
        
        if context["approvals_left"] > 0:
            actions.append(f"Request approval from {context['approvals_left']} reviewer(s)")
        
        if context["risk"]["band"] == "High":
            actions.append("Review high-risk changes carefully")
        
        if summary["risks"]:
            actions.append("Address identified risks before merging")
        
        if not actions:
            actions.append("Review changes and merge when ready")
        
        return actions


# Initialize bot
bot = MergeMindSlackBot()


@app.command("/mergemind")
async def handle_mergemind_command(ack, respond, command):
    """Handle /mergemind slash command."""
    await ack()
    
    try:
        # Parse command text
        text = command.get("text", "").strip()
        
        if not text:
            await respond("Usage: `/mergemind mr <mr_id>`")
            return
        
        parts = text.split()
        if len(parts) != 2 or parts[0] != "mr":
            await respond("Usage: `/mergemind mr <mr_id>`")
            return
        
        try:
            mr_id = int(parts[1])
        except ValueError:
            await respond("Invalid MR ID. Please provide a number.")
            return
        
        # Fetch MR data
        mr_data = await bot.fetch_mr_data(mr_id)
        
        if not mr_data:
            await respond(f"Merge request #{mr_id} not found or unable to fetch data.")
            return
        
        # Format and send response
        blocks = bot.format_mr_response(mr_data)
        await respond(blocks=blocks)
        
    except Exception as e:
        logger.error(f"Error handling mergemind command: {e}")
        await respond("Sorry, I encountered an error while processing your request.")


@app.event("app_mention")
async def handle_app_mention(event, say):
    """Handle app mentions."""
    await say("Hi! Use `/mergemind mr <mr_id>` to get insights about a merge request.")


@app.event("message")
async def handle_message_events(body, logger):
    """Handle message events."""
    logger.info(body)


# Error handlers
@app.error
async def global_error_handler(error, body, logger):
    """Global error handler."""
    logger.error(f"Error: {error}")
    logger.error(f"Body: {body}")


def main():
    """Main function to run the bot."""
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()


if __name__ == "__main__":
    main()
