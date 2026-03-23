import pytest
from aioresponses import aioresponses

from vibecode_b24_bot.client import VibeCode
from vibecode_b24_bot.bot import Bot

BASE = "https://vibecode.bitrix24.tech/v1"


@pytest.fixture
def mock_api():
    with aioresponses() as m:
        yield m


@pytest.fixture
async def client():
    c = VibeCode(api_key="test_key")
    yield c
    await c.close()


@pytest.fixture
def bot():
    b = Bot(api_key="test_key", bot_code="test_bot", bot_name="Test Bot")
    b.bot_id = 1
    return b


@pytest.fixture
def message_event():
    return {
        "eventId": 100,
        "type": "ONIMBOTV2MESSAGEADD",
        "date": "2026-03-23T10:00:00Z",
        "data": {
            "message": {"id": 1, "chatId": 10, "authorId": 42, "text": "hello"},
            "chat": {"id": 10, "dialogId": "chat10", "name": "Test", "type": "chat", "owner": 1},
            "user": {"id": 42, "name": "Alice", "bot": False, "email": "alice@test.com"},
        },
    }


@pytest.fixture
def command_event():
    return {
        "eventId": 200,
        "type": "ONIMBOTV2COMMANDADD",
        "date": "2026-03-23T10:00:00Z",
        "data": {
            "message": {"id": 2, "chatId": 10, "authorId": 42, "text": "/help"},
            "chat": {"id": 10, "dialogId": "chat10", "name": "Test", "type": "chat", "owner": 1},
            "user": {"id": 42, "name": "Alice", "bot": False},
            "command": {"id": 1, "command": "/help", "params": "", "context": "textarea"},
        },
    }


@pytest.fixture
def bot_event():
    return {
        "eventId": 300,
        "type": "ONIMBOTV2MESSAGEADD",
        "date": "2026-03-23T10:00:00Z",
        "data": {
            "message": {"id": 3, "chatId": 10, "authorId": 12, "text": "I am bot"},
            "chat": {"id": 10, "dialogId": "chat10", "name": "Test", "type": "chat", "owner": 1},
            "user": {"id": 12, "name": "Bot", "bot": True},
        },
    }
