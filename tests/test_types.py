import pytest
from vibecode_b24_bot.types import User, Chat, MessageData, Command, Event, Message


def test_user_from_dict():
    u = User.from_dict({
        "id": 42, "name": "Alice Smith", "firstName": "Alice",
        "lastName": "Smith", "bot": False, "email": "alice@test.com",
        "status": "online",
    })
    assert u.id == 42
    assert u.name == "Alice Smith"
    assert u.first_name == "Alice"
    assert u.last_name == "Smith"
    assert u.is_bot is False
    assert u.email == "alice@test.com"


def test_user_from_dict_defaults():
    u = User.from_dict({})
    assert u.id == 0
    assert u.name == ""
    assert u.is_bot is False


def test_user_from_dict_bot():
    u = User.from_dict({"id": 12, "bot": True})
    assert u.is_bot is True


def test_chat_from_dict():
    c = Chat.from_dict({
        "id": 10, "dialogId": "chat10", "name": "Dev",
        "type": "chat", "owner": 1,
    })
    assert c.id == 10
    assert c.dialog_id == "chat10"
    assert c.name == "Dev"
    assert c.type == "chat"
    assert c.owner == 1


def test_chat_from_dict_defaults():
    c = Chat.from_dict({})
    assert c.id == 0
    assert c.dialog_id == ""


def test_message_data_from_dict():
    m = MessageData.from_dict({
        "id": 1, "chatId": 10, "authorId": 42, "text": "hello",
    })
    assert m.id == 1
    assert m.chat_id == 10
    assert m.author_id == 42
    assert m.text == "hello"


def test_message_data_alt_keys():
    """Test that snake_case keys also work (chat_id, author_id)."""
    m = MessageData.from_dict({
        "id": 1, "chat_id": 10, "author_id": 42, "text": "hi",
    })
    assert m.chat_id == 10
    assert m.author_id == 42


def test_command_from_dict():
    c = Command.from_dict({
        "id": 5, "command": "/help", "params": "topic",
        "context": "textarea",
    })
    assert c.id == 5
    assert c.command == "/help"
    assert c.params == "topic"
    assert c.context == "textarea"
    assert c.raw["command"] == "/help"


def test_event_from_dict():
    e = Event.from_dict({
        "eventId": 100, "type": "ONIMBOTV2MESSAGEADD",
        "date": "2026-01-01", "data": {"message": {"text": "hi"}},
    })
    assert e.event_id == 100
    assert e.type == "ONIMBOTV2MESSAGEADD"
    assert e.data["message"]["text"] == "hi"


def test_message_properties():
    msg = Message(
        data=MessageData(id=1, chat_id=10, author_id=42, text="hello"),
        chat=Chat(id=10, dialog_id="chat10"),
        user=User(id=42, name="Alice"),
        bot_id=1,
    )
    assert msg.text == "hello"
    assert msg.message_id == 1
    assert msg.dialog_id == "chat10"
    assert msg.from_user.name == "Alice"


def test_message_answer_no_bot():
    msg = Message(
        data=MessageData(id=1, chat_id=10, author_id=42, text="hello"),
        chat=Chat(id=10, dialog_id="chat10"),
        user=User(id=42, name="Alice"),
        _bot=None,
    )
    with pytest.raises(RuntimeError, match="not bound to bot"):
        import asyncio
        asyncio.get_event_loop().run_until_complete(msg.answer("hi"))


def test_message_typing_no_bot():
    msg = Message(
        data=MessageData(id=1, chat_id=10, author_id=42),
        chat=Chat(id=10, dialog_id="chat10"),
        user=User(id=42),
        _bot=None,
    )
    with pytest.raises(RuntimeError, match="not bound to bot"):
        import asyncio
        asyncio.get_event_loop().run_until_complete(msg.typing())
