import pytest
from unittest.mock import AsyncMock, patch
from aioresponses import aioresponses

from vibecode_b24_bot.bot import Bot, TYPING_STATUSES
from vibecode_b24_bot.types import Event, Message, Command

BASE = "https://vibecode.bitrix24.tech/v1"


def test_on_message_registers_handler(bot):
    @bot.on_message
    async def handler(msg):
        pass

    assert len(bot._message_handlers) == 1
    assert bot._message_handlers[0] is handler


def test_on_command_registers_handler(bot):
    @bot.on_command("help")
    async def handler(msg, cmd):
        pass

    assert "help" in bot._command_handlers


def test_on_command_strips_slash(bot):
    @bot.on_command("/start")
    async def handler(msg, cmd):
        pass

    assert "start" in bot._command_handlers


def test_on_event_registers_handler(bot):
    @bot.on_event("ONIMBOTV2JOINCHAT")
    async def handler(event):
        pass

    assert "ONIMBOTV2JOINCHAT" in bot._event_handlers
    assert len(bot._event_handlers["ONIMBOTV2JOINCHAT"]) == 1


def test_parse_message_event(bot, message_event):
    event = Event.from_dict(message_event)
    msg = bot._parse_message_event(event)
    assert msg is not None
    assert msg.text == "hello"
    assert msg.dialog_id == "chat10"
    assert msg.from_user.name == "Alice"
    assert msg._bot is bot


def test_parse_message_event_skips_bot(bot, bot_event):
    event = Event.from_dict(bot_event)
    msg = bot._parse_message_event(event)
    assert msg is None


def test_parse_message_event_skips_duplicate(bot, message_event):
    event = Event.from_dict(message_event)
    msg1 = bot._parse_message_event(event)
    msg2 = bot._parse_message_event(event)
    assert msg1 is not None
    assert msg2 is None


def test_processed_set_pruning(bot):
    for i in range(10500):
        bot._processed.add(i)
    # Trigger pruning via _parse_message_event
    event = Event.from_dict({
        "eventId": 999, "type": "ONIMBOTV2MESSAGEADD",
        "data": {
            "message": {"id": 99999, "chatId": 10, "authorId": 42, "text": "x"},
            "chat": {"id": 10, "dialogId": "1", "owner": 1},
            "user": {"id": 42, "name": "Test", "bot": False},
        },
    })
    bot._parse_message_event(event)
    assert len(bot._processed) <= 5001


async def test_handle_event_calls_message_handler(bot, message_event):
    received = []

    @bot.on_message
    async def handler(msg):
        received.append(msg.text)

    event = Event.from_dict(message_event)
    await bot._handle_event(event)
    assert received == ["hello"]


async def test_handle_event_calls_command_handler(bot, command_event):
    received = []

    @bot.on_command("help")
    async def handler(msg, cmd):
        received.append(cmd.command)

    event = Event.from_dict(command_event)
    await bot._handle_event(event)
    assert received == ["/help"]


async def test_handle_event_calls_raw_handler(bot, message_event):
    received = []

    @bot.on_event("ONIMBOTV2MESSAGEADD")
    async def handler(event):
        received.append(event.type)

    event = Event.from_dict(message_event)
    await bot._handle_event(event)
    assert received == ["ONIMBOTV2MESSAGEADD"]


async def test_handle_event_exception_doesnt_crash(bot, message_event):
    @bot.on_message
    async def handler(msg):
        raise ValueError("oops")

    event = Event.from_dict(message_event)
    await bot._handle_event(event)  # should not raise


async def test_send_message(bot):
    with aioresponses() as m:
        m.post(f"{BASE}/bots/1/messages", payload={"success": True, "data": {"id": 10}})
        result = await bot.send_message("chat10", "hello")
        assert result["id"] == 10


async def test_show_typing_maps_status(bot):
    with aioresponses() as m:
        m.post(f"{BASE}/bots/1/typing", payload={"success": True, "data": {"result": True}})
        await bot.show_typing("chat10", "thinking")


def test_typing_status_mapping():
    assert TYPING_STATUSES["thinking"] == "IMBOT_AGENT_ACTION_THINKING"
    assert TYPING_STATUSES["searching"] == "IMBOT_AGENT_ACTION_SEARCHING"
    assert TYPING_STATUSES["generating"] == "IMBOT_AGENT_ACTION_GENERATING"
    assert len(TYPING_STATUSES) == 11


async def test_find_or_register_finds_existing(bot):
    with aioresponses() as m:
        m.get(f"{BASE}/bots", payload={"success": True, "data": [
            {"botId": 5, "code": "test_bot"},
        ]})
        bot_id = await bot._find_or_register()
        assert bot_id == 5


async def test_find_or_register_creates_new(bot):
    with aioresponses() as m:
        m.get(f"{BASE}/bots", payload={"success": True, "data": []})
        m.post(f"{BASE}/bots", payload={"success": True, "data": {"botId": 7}})
        bot_id = await bot._find_or_register()
        assert bot_id == 7


async def test_add_reaction(bot):
    with aioresponses() as m:
        m.post(f"{BASE}/bots/1/messages/10/reactions", payload={"success": True, "data": {"result": True}})
        await bot.add_reaction(10, "like")
