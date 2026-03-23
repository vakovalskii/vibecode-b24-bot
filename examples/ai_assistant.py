"""AI assistant bot — connects any OpenAI-compatible LLM to Bitrix24 chat."""

import os
import aiohttp
from vibecode import Bot

bot = Bot(
    api_key=os.environ["VIBE_API_KEY"],
    bot_code="ai_assistant",
    bot_name="AI Ассистент",
    bot_type="bot",
)

LLM_BASE = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama3")

histories: dict[str, list] = {}


async def ask_llm(dialog_id: str, text: str) -> str:
    history = histories.setdefault(dialog_id, [])
    history.append({"role": "user", "content": text})
    if len(history) > 20:
        del history[: len(history) - 20]

    messages = [
        {
            "role": "system",
            "content": (
                "Ты AI-ассистент в корпоративном чате Битрикс24. "
                "Отвечай кратко и по делу. Без Markdown — пиши простым текстом."
            ),
        },
        *history,
    ]

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{LLM_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_KEY}"},
            json={"model": LLM_MODEL, "messages": messages, "max_tokens": 1024},
        ) as resp:
            data = await resp.json()

    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "Ошибка LLM")
    history.append({"role": "assistant", "content": reply})
    return reply


@bot.on_message
async def handle(msg):
    await msg.typing("thinking")
    reply = await ask_llm(msg.dialog_id, msg.text)
    await msg.answer(reply)


@bot.on_command("clear")
async def clear_cmd(msg, cmd):
    histories.pop(msg.dialog_id, None)
    await msg.answer("История диалога очищена.")


bot.run()
