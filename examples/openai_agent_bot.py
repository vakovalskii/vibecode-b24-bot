"""Bitrix24 bot powered by OpenAI Agents SDK.

Requires:
    pip install vibecode-b24-bot openai-agents

Env:
    VIBE_API_KEY    — VibeCode API key
    OPENAI_API_KEY  — OpenAI API key
"""

import os
from agents import Agent, Runner
from vibecode_b24_bot import Bot

bot = Bot(
    api_key=os.environ["VIBE_API_KEY"],
    bot_code="openai_agent",
    bot_name="AI Agent",
    bot_type="bot",
)

agent = Agent(
    name="Bitrix24 Assistant",
    instructions=(
        "You are a helpful assistant in a Bitrix24 corporate chat. "
        "Answer concisely and in the same language as the user. "
        "Do NOT use Markdown formatting — write plain text only."
    ),
)


@bot.on_message
async def handle(msg):
    await msg.typing("thinking")
    result = await Runner.run(agent, msg.text)
    await msg.answer(result.final_output)


@bot.on_command("help")
async def help_cmd(msg, cmd):
    await msg.answer(
        "AI Agent bot powered by OpenAI Agents SDK.\n\n"
        "Just write me any question — I'll answer!\n"
        "/help — this help message"
    )


bot.run()
