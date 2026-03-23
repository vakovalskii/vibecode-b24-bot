"""Simple echo bot for Bitrix24 via VibeCode API."""

import os
from vibecode import Bot, bb

bot = Bot(
    api_key=os.environ["VIBE_API_KEY"],
    bot_code="echo_bot",
    bot_name="Echo Bot",
)


@bot.on_message
async def echo(msg):
    await msg.typing("thinking")
    await msg.answer(f"Вы написали: {bb.italic(msg.text)}")


@bot.on_command("help")
async def help_cmd(msg, cmd):
    await msg.answer(
        f"{bb.bold('Echo Bot')}\n\n"
        f"Я повторяю всё что вы пишете.\n"
        f"Команды:\n"
        f"/help — эта справка"
    )


bot.run()
