# vibecode-b24-bot

Python SDK for Bitrix24 bots via [VibeCode](https://vibecode.bitrix24.tech) API.

Async bot framework like `aiogram`, but for Bitrix24. Plus CRM/tasks/entities client.

## Install

```bash
pip install vibecode-b24-bot
```

## Getting your API key

1. Go to your Bitrix24 portal (e.g. `https://your-company.bitrix24.ru`)
2. Open **VibeCode** section: `https://your-company.bitrix24.ru/vibe/`
3. Navigate to **API-ключи** (API keys)
4. Click **Создать API-ключ** (Create API key)
5. Select required permissions (at minimum: `imbot` for bots, `crm` for CRM, `tasks` for tasks)
6. Copy the key — it looks like `vibe_api_xxxxxxxxxxxxx`

> **Note:** Your portal needs an active subscription or demo mode for REST API to work. Enable demo for free on the portal's main page.

## Quick start

### 1. Create your bot

```python
# bot.py
import os
from vibecode_b24_bot import Bot, bb

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

### 2. Run it

```bash
export VIBE_API_KEY=vibe_api_your_key_here
python bot.py
```

The bot will:
- Register itself in your Bitrix24 portal
- Start polling for messages
- Appear in the messenger as "My Bot"

Open your Bitrix24 messenger, find the bot, and send a message!

### 3. Run with Docker

```bash
# Copy your bot file
cp examples/echo_bot.py bot.py

# Run with docker-compose
VIBE_API_KEY=vibe_api_xxx docker-compose up -d

# Or with plain docker
docker build -t my-b24-bot .
docker run -d --restart unless-stopped \
  -e VIBE_API_KEY=vibe_api_xxx \
  my-b24-bot
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
# Standard bot — responds to @mention and direct messages
Bot(api_key=key, bot_type="bot")

# Personal AI assistant — sees ALL messages in chats it's in
Bot(api_key=key, bot_type="personal")

# Supervisor/observer — for monitoring, analytics, moderation
Bot(api_key=key, bot_type="supervisor")
```

## Formatting (BB-codes)

Bitrix24 chat uses BB-codes, **not Markdown**:

```python
from vibecode_b24_bot import bb

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
    await msg.typing("thinking")      # show typing indicator
    await msg.react("like")           # add reaction
```

## Typing statuses

```python
await msg.typing("thinking")     # Agent is thinking...
await msg.typing("searching")    # Agent is searching...
await msg.typing("generating")   # Agent is preparing answer...
await msg.typing("analyzing")    # Agent is analyzing...
await msg.typing("processing")   # Agent is processing data...
await msg.typing("translating")  # Agent is translating...
await msg.typing("reading")      # Agent is reading documents...
await msg.typing("composing")    # Agent is composing answer...
```

## Low-level client (CRM, tasks, entities)

```python
import asyncio, os
from vibecode_b24_bot import VibeCode

async def main():
    async with VibeCode(api_key=os.environ["VIBE_API_KEY"]) as client:
        # Entity CRUD (35 entities: deals, contacts, tasks, users, etc.)
        await client.list_entity("deals", limit=50)
        await client.get_entity("deals", 123)
        await client.create_entity("deals", title="New deal", amount=50000)
        await client.update_entity("deals", 123, stageId="WON")
        await client.delete_entity("deals", 123)
        await client.search_entity("deals", filter={"stageId": "NEW"})

        # Batch — 50 calls in 1 request (1 rate-limit unit)
        await client.batch([
            {"method": "crm.status.list"},
            {"method": "crm.deal.fields"},
        ])

        # Direct Bitrix24 method call
        await client.call("app.info")

        # Portal info
        await client.me()

asyncio.run(main())
```

## OpenAI Agents SDK example

Build an AI bot with [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) in under 30 lines:

```bash
pip install vibecode-b24-bot openai-agents
```

```python
# bot.py
import os
from agents import Agent, Runner
from vibecode_b24_bot import Bot

bot = Bot(
    api_key=os.environ["VIBE_API_KEY"],
    bot_code="ai_agent",
    bot_name="AI Agent",
)

agent = Agent(
    name="Bitrix24 Assistant",
    instructions=(
        "You are a helpful assistant in a Bitrix24 corporate chat. "
        "Answer concisely, in the user's language. No Markdown — plain text only."
    ),
)

@bot.on_message
async def handle(msg):
    await msg.typing("thinking")
    result = await Runner.run(agent, msg.text)
    await msg.answer(result.final_output)

bot.run()
```

```bash
export VIBE_API_KEY=vibe_api_xxx
export OPENAI_API_KEY=sk-xxx
python bot.py
```

For a more advanced example with CRM tools (agent can search deals and contacts), see [`examples/openai_agent_with_tools.py`](examples/openai_agent_with_tools.py).

## AI assistant with any LLM

Connect any OpenAI-compatible LLM (Ollama, vLLM, OpenRouter, etc.):

```bash
export VIBE_API_KEY=vibe_api_xxx
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=llama3
python examples/ai_assistant.py
```

See [`examples/`](examples/) for full code.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VIBE_API_KEY` | Yes | VibeCode API key from your Bitrix24 portal |
| `LLM_BASE_URL` | No | OpenAI-compatible API URL (for AI assistant) |
| `LLM_API_KEY` | No | LLM API key |
| `LLM_MODEL` | No | LLM model name |

## Examples

- [`examples/echo_bot.py`](examples/echo_bot.py) — simple echo bot
- [`examples/ai_assistant.py`](examples/ai_assistant.py) — LLM-powered chat bot
- [`examples/crm_dashboard.py`](examples/crm_dashboard.py) — fetch CRM deals
- [`Dockerfile`](Dockerfile) + [`docker-compose.yml`](docker-compose.yml) — containerized deployment

## License

MIT
