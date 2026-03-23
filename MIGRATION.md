# Migration Guide

## From raw curl / requests

### Before (raw HTTP)

```python
import requests

API_KEY = "vibe_api_xxx"
BASE = "https://vibecode.bitrix24.tech/v1"
headers = {"X-Api-Key": API_KEY}

# List deals
resp = requests.get(f"{BASE}/deals", headers=headers, params={"limit": 50})
data = resp.json()
if not data["success"]:
    raise Exception(data["error"]["message"])
deals = data["data"]

# Create deal
resp = requests.post(f"{BASE}/deals", headers=headers, json={"title": "New", "amount": 50000})
deal = resp.json()["data"]

# Manual retry on 429
import time
for attempt in range(5):
    resp = requests.get(f"{BASE}/deals", headers=headers)
    if resp.status_code == 429:
        time.sleep(2 ** attempt)
        continue
    break
```

### After (SDK)

```python
import asyncio
from vibecode_b24_bot import VibeCode

async def main():
    async with VibeCode(api_key="vibe_api_xxx") as client:
        # List deals (auto-retry, auto-unwrap)
        deals = await client.list_entity("deals", limit=50)

        # Create deal
        deal = await client.create_entity("deals", title="New", amount=50000)

asyncio.run(main())
```

What the SDK handles for you:
- `X-Api-Key` header — set once in constructor
- Response unwrapping — `data["data"]` extraction automatic
- Error handling — raises `APIError` with `.code` and `.message`
- Retry with backoff — 429 and network errors retried automatically (up to 5 times)
- Session management — `async with` handles open/close

### Step by step

1. `pip install vibecode-b24-bot`
2. Replace `import requests` with `from vibecode_b24_bot import VibeCode`
3. Wrap code in `async with VibeCode(api_key=...) as client:`
4. Replace `requests.get(url, headers=..., params=...)` with `client.get("/path", **params)`
5. Replace `requests.post(url, headers=..., json=...)` with `client.post("/path", **body)`
6. Remove manual `.json()["data"]` — SDK returns data directly
7. Remove retry/backoff code — built-in

---

## From Node.js bot (bot.mjs) to Python SDK

### Concept mapping

| Node.js | Python SDK |
|---------|-----------|
| `fetch(url, {headers: {"X-Api-Key": key}})` | `VibeCode(api_key=key)` |
| `setInterval(poll, 5000)` | `bot.run()` (built-in) |
| Manual offset tracking | Automatic |
| Manual message deduplication | Automatic (`_processed` set) |
| `if (event.type === "ONIMBOTV2MESSAGEADD")` | `@bot.on_message` |
| `fetch(POST, /bots/{id}/messages, ...)` | `await msg.answer("text")` |
| `fetch(POST, /bots/{id}/typing, ...)` | `await msg.typing("thinking")` |
| `process.env.VIBE_API_KEY` | `os.environ["VIBE_API_KEY"]` |

### Before (Node.js)

```javascript
// 100+ lines: manual polling, offset, deduplication, fetch calls
const POLL_INTERVAL = 2000;
let lastEventId = 0;
const processed = new Set();

while (true) {
    const res = await fetch(`${BASE}/bots/${botId}/events?offset=${lastEventId}`, opts);
    const data = await res.json();

    for (const event of data.data.events) {
        if (event.type !== "ONIMBOTV2MESSAGEADD") continue;
        const msgId = event.data.message.id;
        if (processed.has(msgId)) continue;
        processed.add(msgId);

        // typing
        await fetch(`${BASE}/bots/${botId}/typing`, {method: "POST", ...});

        // respond
        const reply = await askLLM(event.data.message.text);
        await fetch(`${BASE}/bots/${botId}/messages`, {method: "POST", body: ...});
    }

    lastEventId = data.data.lastEventId;
    await sleep(POLL_INTERVAL);
}
```

### After (Python SDK)

```python
# 15 lines: everything handled by SDK
import os
from vibecode_b24_bot import Bot

bot = Bot(api_key=os.environ["VIBE_API_KEY"], bot_code="my_bot", bot_name="My Bot")

@bot.on_message
async def handle(msg):
    await msg.typing("thinking")
    reply = await ask_llm(msg.text)
    await msg.answer(reply)

bot.run()
```

### Step by step

1. `pip install vibecode-b24-bot`
2. Create `bot.py` with `Bot(api_key=..., bot_code=..., bot_name=...)`
3. Convert each `if (event.type === ...)` block → decorator handler
4. Replace fetch calls: `msg.answer()`, `msg.typing()`, `msg.react()`
5. Delete: polling loop, offset tracking, deduplication, headers — all built-in
6. `VIBE_API_KEY=xxx python bot.py`
7. Docker: replace `node bot.mjs` → `python bot.py` in Dockerfile

---

## From aiogram (Telegram) to vibecode-b24-bot

The SDK is designed with the same patterns. If you know aiogram, you already know 90% of this.

### Concept mapping

| aiogram | vibecode-b24-bot | Notes |
|---------|-----------------|-------|
| `Dispatcher` + `Bot` | `Bot` | Single class |
| `@dp.message()` | `@bot.on_message` | Same pattern |
| `@dp.message(Command("help"))` | `@bot.on_command("help")` | Separate decorator |
| `message.answer("text")` | `msg.answer("text")` | Identical |
| `message.from_user` | `msg.from_user` | Same |
| `message.chat.id` | `msg.chat.id` | Same |
| `bot.send_chat_action(...)` | `msg.typing("thinking")` | 11 statuses |
| Markdown/HTML parse mode | BB-codes (`bb.bold()`) | Key difference |
| `dp.start_polling(bot)` | `bot.run()` | Same idea |

### Key differences

1. **BB-codes, not Markdown** — Bitrix24 chat does not render Markdown

   ```python
   # aiogram
   await message.answer("**bold**", parse_mode="Markdown")

   # vibecode-b24-bot
   from vibecode_b24_bot import bb
   await msg.answer(bb.bold("bold"))
   ```

2. **No filter system** — route manually in handler code

   ```python
   # aiogram: separate handlers via filters
   @dp.message(Command("help"))
   @dp.message(F.text.contains("hello"))

   # vibecode-b24-bot: commands have decorators, rest is manual
   @bot.on_command("help")
   async def help_cmd(msg, cmd): ...

   @bot.on_message
   async def handle(msg):
       if "hello" in msg.text:
           ...
   ```

3. **No FSM** — use a dict keyed by `dialog_id`

   ```python
   states = {}

   @bot.on_message
   async def handle(msg):
       state = states.get(msg.dialog_id, "idle")
       if state == "idle":
           states[msg.dialog_id] = "waiting_name"
           await msg.answer("What's your name?")
       elif state == "waiting_name":
           name = msg.text
           del states[msg.dialog_id]
           await msg.answer(f"Hello, {name}!")
   ```

4. **Bot types** — no Telegram equivalent
   - `bot` — like a regular Telegram bot (responds to mentions/DMs)
   - `personal` — sees ALL messages (like having the bot in every chat)
   - `supervisor` — silent observer for analytics

5. **No middleware** — use plain Python decorators or wrapper functions

### Step by step

1. `pip install vibecode-b24-bot`
2. Replace `from aiogram import ...` → `from vibecode_b24_bot import Bot, bb`
3. Merge `Dispatcher` + `Bot` → single `Bot(api_key=...)`
4. `@dp.message()` → `@bot.on_message`
5. `@dp.message(Command("x"))` → `@bot.on_command("x")`
6. Replace `parse_mode="HTML"` with `bb.bold()`, `bb.italic()`, etc.
7. Replace `await bot.send_chat_action(...)` → `await msg.typing("thinking")`
8. Replace `dp.start_polling(bot)` → `bot.run()`
