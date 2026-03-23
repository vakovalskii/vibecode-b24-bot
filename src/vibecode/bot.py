"""High-level async Bot framework for Bitrix24 via VibeCode API.

Usage::

    from vibecode import Bot

    bot = Bot(api_key="vibe_api_...")

    @bot.on_message
    async def echo(msg):
        await msg.typing("thinking")
        await msg.answer(f"You said: {msg.text}")

    @bot.on_command("help")
    async def help_cmd(msg, command):
        await msg.answer("I'm an AI assistant!")

    bot.run()
"""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Any, Callable, Awaitable

from vibecode.client import VibeCode, APIError
from vibecode.types import Event, Message, MessageData, Chat, User, Command

logger = logging.getLogger("vibecode")

# Typing status code mapping
TYPING_STATUSES = {
    "thinking": "IMBOT_AGENT_ACTION_THINKING",
    "searching": "IMBOT_AGENT_ACTION_SEARCHING",
    "generating": "IMBOT_AGENT_ACTION_GENERATING",
    "analyzing": "IMBOT_AGENT_ACTION_ANALYZING",
    "processing": "IMBOT_AGENT_ACTION_PROCESSING",
    "translating": "IMBOT_AGENT_ACTION_TRANSLATING",
    "connecting": "IMBOT_AGENT_ACTION_CONNECTING",
    "checking": "IMBOT_AGENT_ACTION_CHECKING",
    "calculating": "IMBOT_AGENT_ACTION_CALCULATING",
    "reading": "IMBOT_AGENT_ACTION_READING_DOCS",
    "composing": "IMBOT_AGENT_ACTION_COMPOSING",
}

MessageHandler = Callable[[Message], Awaitable[None]]
CommandHandler = Callable[[Message, Command], Awaitable[None]]
EventHandler = Callable[[Event], Awaitable[None]]


class Bot:
    """Async Bitrix24 bot via VibeCode API.

    Args:
        api_key: VibeCode API key.
        bot_code: Unique bot identifier. Used to register or find existing bot.
        bot_name: Display name in chat.
        bot_type: One of "bot", "personal", "supervisor".
        poll_interval: Seconds between polls when idle.
        poll_fast: Seconds between polls when hasMore=True.
    """

    def __init__(
        self,
        api_key: str,
        bot_code: str = "vibecode_bot",
        bot_name: str = "VibeCode Bot",
        bot_type: str = "bot",
        poll_interval: float = 5.0,
        poll_fast: float = 1.0,
    ):
        self.client = VibeCode(api_key=api_key)
        self.bot_code = bot_code
        self.bot_name = bot_name
        self.bot_type = bot_type
        self.poll_interval = poll_interval
        self.poll_fast = poll_fast

        self.bot_id: int | None = None
        self._running = False

        self._message_handlers: list[MessageHandler] = []
        self._command_handlers: dict[str, CommandHandler] = {}
        self._event_handlers: dict[str, list[EventHandler]] = {}
        self._processed: set[int] = set()

    # --- Decorators ---

    def on_message(self, func: MessageHandler) -> MessageHandler:
        """Register handler for incoming messages.

        ::

            @bot.on_message
            async def handle(msg: Message):
                await msg.answer("Got it!")
        """
        self._message_handlers.append(func)
        return func

    def on_command(self, command: str) -> Callable[[CommandHandler], CommandHandler]:
        """Register handler for slash-command.

        ::

            @bot.on_command("help")
            async def help_cmd(msg: Message, cmd: Command):
                await msg.answer("Help text here")
        """

        def decorator(func: CommandHandler) -> CommandHandler:
            self._command_handlers[command.lstrip("/")] = func
            return func

        return decorator

    def on_event(self, event_type: str) -> Callable[[EventHandler], EventHandler]:
        """Register handler for raw event type.

        ::

            @bot.on_event("ONIMBOTV2JOINCHAT")
            async def joined(event: Event):
                print("Bot joined chat!")
        """

        def decorator(func: EventHandler) -> EventHandler:
            self._event_handlers.setdefault(event_type, []).append(func)
            return func

        return decorator

    # --- Bot API methods ---

    async def send_message(self, dialog_id: str, text: str, **kwargs: Any) -> dict:
        fields = {"message": text, **kwargs}
        return await self.client.post(
            f"/bots/{self.bot_id}/messages",
            dialogId=dialog_id,
            fields=fields,
        )

    async def update_message(self, message_id: int, text: str, **kwargs: Any) -> dict:
        fields = {"message": text, **kwargs}
        return await self.client.patch(
            f"/bots/{self.bot_id}/messages/{message_id}",
            fields=fields,
        )

    async def delete_message(self, message_id: int) -> Any:
        return await self.client.delete(
            f"/bots/{self.bot_id}/messages/{message_id}",
        )

    async def show_typing(self, dialog_id: str, status: str = "thinking", duration: int = 30) -> None:
        code = TYPING_STATUSES.get(status, status)
        await self.client.post(
            f"/bots/{self.bot_id}/typing",
            dialogId=dialog_id,
            statusMessageCode=code,
            duration=duration,
        )

    async def add_reaction(self, message_id: int, reaction: str = "like") -> Any:
        return await self.client.post(
            f"/bots/{self.bot_id}/messages/{message_id}/reactions",
            reaction=reaction,
        )

    async def create_chat(self, title: str, user_ids: list[int] | None = None, **kwargs: Any) -> dict:
        fields: dict[str, Any] = {"title": title, **kwargs}
        if user_ids:
            fields["userIds"] = user_ids
        return await self.client.post(f"/bots/{self.bot_id}/chats", fields=fields)

    async def register_command(self, command: str, title: str | None = None, **kwargs: Any) -> dict:
        return await self.client.post(
            f"/bots/{self.bot_id}/commands",
            command=command,
            **({"title": {"ru": title, "en": title}} if title else {}),
            **kwargs,
        )

    # --- Lifecycle ---

    async def _find_or_register(self) -> int:
        # Try to find existing bot
        try:
            bots = await self.client.get("/bots")
            if isinstance(bots, list):
                for b in bots:
                    if b.get("code") == self.bot_code:
                        bot_id = int(b["botId"])
                        logger.info("Found existing bot %s (ID: %d)", self.bot_code, bot_id)
                        return bot_id
        except APIError:
            pass

        # Register new
        result = await self.client.post(
            "/bots",
            code=self.bot_code,
            name=self.bot_name,
            type=self.bot_type,
        )
        bot_id = int(result.get("botId", result.get("id", 0)))
        logger.info("Registered bot %s (ID: %d)", self.bot_code, bot_id)
        return bot_id

    async def _skip_old_events(self) -> int:
        """Skip existing events on startup, return last offset."""
        try:
            result = await self.client.get(f"/bots/{self.bot_id}/events", offset=0, limit=1000)
            events = result.get("events", [])
            for ev in events:
                msg = ev.get("data", {}).get("message", {})
                if msg_id := msg.get("id"):
                    self._processed.add(int(msg_id))

            last = result.get("lastEventId", result.get("nextOffset", 0))
            logger.info("Skipped %d old events, offset: %s", len(events), last)
            return int(last) if last else 0
        except APIError as e:
            logger.warning("Could not skip old events: %s", e)
            return 0

    def _parse_message_event(self, event: Event) -> Message | None:
        data = event.data
        msg_data = data.get("message", {})
        chat_data = data.get("chat", {})
        user_data = data.get("user", {})

        if not msg_data or not chat_data:
            return None

        # Skip bot's own messages
        if user_data.get("bot"):
            return None

        msg_id = int(msg_data.get("id", 0))
        if msg_id in self._processed:
            return None
        self._processed.add(msg_id)

        # Keep set bounded
        if len(self._processed) > 10000:
            to_remove = sorted(self._processed)[: len(self._processed) - 5000]
            self._processed -= set(to_remove)

        return Message(
            data=MessageData.from_dict(msg_data),
            chat=Chat.from_dict(chat_data),
            user=User.from_dict(user_data),
            bot_id=self.bot_id or 0,
            _bot=self,
        )

    async def _handle_event(self, event: Event) -> None:
        try:
            # Raw event handlers
            for handler in self._event_handlers.get(event.type, []):
                await handler(event)

            if event.type == "ONIMBOTV2MESSAGEADD":
                msg = self._parse_message_event(event)
                if msg:
                    for handler in self._message_handlers:
                        await handler(msg)

            elif event.type == "ONIMBOTV2COMMANDADD":
                cmd_data = event.data.get("command", {})
                cmd_name = cmd_data.get("command", "").lstrip("/")
                handler = self._command_handlers.get(cmd_name)
                if handler:
                    msg = self._parse_message_event(event)
                    if msg:
                        await handler(msg, Command.from_dict(cmd_data))

        except Exception:
            logger.exception("Error handling event %s", event.type)

    async def _poll_loop(self) -> None:
        offset = await self._skip_old_events()
        logger.info("Polling started")

        while self._running:
            try:
                result = await self.client.get(
                    f"/bots/{self.bot_id}/events",
                    offset=offset,
                    limit=100,
                )

                events = result.get("events", [])
                for ev_data in events:
                    event = Event.from_dict(ev_data)
                    await self._handle_event(event)

                new_offset = result.get("lastEventId", result.get("nextOffset"))
                if new_offset is not None:
                    offset = int(new_offset)

                has_more = result.get("hasMore", False)
                await asyncio.sleep(self.poll_fast if has_more else self.poll_interval)

            except APIError as e:
                logger.error("API error: %s", e)
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Unexpected error in poll loop")
                await asyncio.sleep(self.poll_interval)

    async def start(self) -> None:
        """Start the bot (async). Use `run()` for sync entry point."""
        me = await self.client.me()
        portal = me.get("portal", "unknown")
        logger.info("Connected to portal: %s", portal)

        self.bot_id = await self._find_or_register()
        self._running = True

        # Register slash-commands if any
        for cmd_name in self._command_handlers:
            try:
                await self.register_command(cmd_name)
                logger.info("Registered command /%s", cmd_name)
            except APIError:
                pass  # Already registered

        await self._poll_loop()

    async def stop(self) -> None:
        """Stop the bot gracefully."""
        self._running = False
        await self.client.close()
        logger.info("Bot stopped")

    def run(self) -> None:
        """Start the bot (blocking). Sets up signal handlers and runs event loop."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
        )

        async def _main() -> None:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

            try:
                await self.start()
            finally:
                await self.stop()

        asyncio.run(_main())
