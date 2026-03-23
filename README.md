# vibecode-b24-bot

Python SDK for Bitrix24 bots via [VibeCode](https://vibecode.bitrix24.tech) API.

Async bot framework like `aiogram`, but for Bitrix24. Plus CRM/tasks/entities client.

## Install

```bash
pip install vibecode-b24-bot
```

## Quick start — Bot

```python
import os
from vibecode import Bot, bb

bot = Bot(
    api_key=os.environ["VIBE_API_KEY"],
    bot_code="my_bot",
    bot_name="My Bot",
)

@bot.on_message
async def handle(msg):
    await msg.typing("thinking")
    await msg.answer(f"You said: {bb.bold(msg.text)}")

@bot.on_command("help")
async def help_cmd(msg, cmd):
    await msg.answer("I'm a bot!")

bot.run()
```

## Quick start — CRM / Entities

```python
import asyncio, os
from vibecode import VibeCode

async def main():
    async with VibeCode(api_key=os.environ["VIBE_API_KEY"]) as client:
        deals = await client.list_entity("deals", limit=10)
        for d in deals:
            print(d["TITLE"], d["OPPORTUNITY"])

asyncio.run(main())
```

## Features

- **Bot framework** with decorators (`@bot.on_message`, `@bot.on_command`)
- **Async polling** with auto offset tracking, deduplication, exponential backoff
- **35 entities** — deals, contacts, tasks, users, calendar, disk, etc.
- **Batch API** — 50 calls in 1 request
- **BB-code formatting** — `bb.bold()`, `bb.italic()`, `bb.code()`, `bb.link()`
- **Typing indicators** — 11 statuses (thinking, searching, generating...)
- **Chat management** — create chats, manage users, slash-commands
- **File upload/download**
- **Zero config** — just API key and `bot.run()`

## Bot types

```python
Bot(api_key=key, bot_type="bot")         # Standard — responds to @mention and DMs
Bot(api_key=key, bot_type="personal")    # AI assistant — sees ALL messages
Bot(api_key=key, bot_type="supervisor")  # Observer — monitoring, analytics
```

## Formatting (BB-codes)

Bitrix24 chat uses BB-codes, not Markdown:

```python
from vibecode import bb

bb.bold("important")          # [b]important[/b]
bb.italic("note")             # [i]note[/i]
bb.code("x = 1")             # [code]x = 1[/code]
bb.link("https://...", "Go")  # [url=https://...]Go[/url]
bb.strike("old")              # [s]old[/s]
bb.quote("cited text")        # [quote]cited text[/quote]
bb.list(["a", "b", "c"])     # [list][*]a[*]b[*]c[/list]
bb.mention(user_id=42)        # [user=42][/user]
```

## Message object

```python
@bot.on_message
async def handle(msg):
    msg.text          # message text
    msg.dialog_id     # chat/dialog ID
    msg.from_user     # User object (id, name, email)
    msg.message_id    # message ID
    msg.chat          # Chat object (id, name, type)

    await msg.answer("reply")         # send reply
    await msg.typing("thinking")      # show typing
    await msg.react("like")           # add reaction
```

## Low-level client

```python
async with VibeCode(api_key=key) as client:
    # Entity CRUD
    await client.list_entity("deals", limit=50)
    await client.get_entity("deals", 123)
    await client.create_entity("deals", title="New", amount=50000)
    await client.update_entity("deals", 123, stageId="WON")
    await client.delete_entity("deals", 123)
    await client.search_entity("deals", filter={"stageId": "NEW"})

    # Batch
    await client.batch([
        {"method": "crm.status.list"},
        {"method": "crm.deal.fields"},
    ])

    # Direct method call
    await client.call("app.info")

    # Portal info
    await client.me()
```

## Examples

See [`examples/`](examples/) directory:
- `echo_bot.py` — simple echo bot
- `ai_assistant.py` — LLM-powered chat bot (any OpenAI-compatible API)
- `crm_dashboard.py` — fetch CRM deals

## License

MIT
