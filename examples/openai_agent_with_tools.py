"""Bitrix24 bot with OpenAI Agent that can access CRM data.

The agent has tools to look up deals and contacts in Bitrix24 CRM,
so it can answer questions like "how many open deals do we have?"

Requires:
    pip install vibecode-b24-bot openai-agents

Env:
    VIBE_API_KEY    — VibeCode API key
    OPENAI_API_KEY  — OpenAI API key
"""

import os
import json
from agents import Agent, Runner, function_tool
from vibecode_b24_bot import Bot, VibeCode

VIBE_KEY = os.environ["VIBE_API_KEY"]

bot = Bot(
    api_key=VIBE_KEY,
    bot_code="crm_agent",
    bot_name="CRM Agent",
    bot_type="bot",
)


@function_tool
async def get_deals(limit: int = 10) -> str:
    """Fetch recent CRM deals from Bitrix24. Returns JSON with deal list."""
    async with VibeCode(api_key=VIBE_KEY) as client:
        deals = await client.list_entity("deals", limit=limit)
    return json.dumps(deals, ensure_ascii=False, default=str)


@function_tool
async def get_contacts(limit: int = 10) -> str:
    """Fetch contacts from Bitrix24 CRM. Returns JSON with contact list."""
    async with VibeCode(api_key=VIBE_KEY) as client:
        contacts = await client.list_entity("contacts", limit=limit)
    return json.dumps(contacts, ensure_ascii=False, default=str)


@function_tool
async def search_deals(stage: str = "", assigned_to: str = "") -> str:
    """Search deals by stage or assignee. Stage examples: NEW, WON, LOSE."""
    async with VibeCode(api_key=VIBE_KEY) as client:
        filters = {}
        if stage:
            filters["stageId"] = stage
        if assigned_to:
            filters["assignedById"] = assigned_to
        result = await client.search_entity("deals", filter=filters)
    return json.dumps(result, ensure_ascii=False, default=str)


agent = Agent(
    name="CRM Assistant",
    instructions=(
        "You are a CRM assistant in a Bitrix24 corporate chat. "
        "You can look up deals and contacts using the provided tools. "
        "Answer concisely, in the user's language. No Markdown — plain text only. "
        "When listing data, format it as a simple numbered list."
    ),
    tools=[get_deals, get_contacts, search_deals],
)


@bot.on_message
async def handle(msg):
    await msg.typing("searching")
    result = await Runner.run(agent, msg.text)
    await msg.answer(result.final_output)


bot.run()
