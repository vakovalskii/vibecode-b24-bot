"""Data types for VibeCode Bot API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from vibecode.bot import Bot


@dataclass
class User:
    id: int
    name: str = ""
    first_name: str = ""
    last_name: str = ""
    work_position: str | None = None
    email: str = ""
    is_bot: bool = False
    status: str = ""
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> User:
        return cls(
            id=int(data.get("id", 0)),
            name=data.get("name", ""),
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            work_position=data.get("workPosition"),
            email=data.get("email", ""),
            is_bot=bool(data.get("bot", False)),
            status=data.get("status", ""),
            raw=data,
        )


@dataclass
class Chat:
    id: int
    dialog_id: str = ""
    name: str = ""
    type: str = ""
    owner: int = 0
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Chat:
        return cls(
            id=int(data.get("id", 0)),
            dialog_id=str(data.get("dialogId", "")),
            name=data.get("name", ""),
            type=data.get("type", ""),
            owner=int(data.get("owner", 0)),
            raw=data,
        )


@dataclass
class MessageData:
    id: int
    chat_id: int
    author_id: int
    text: str = ""
    date: str = ""
    is_system: bool = False
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> MessageData:
        return cls(
            id=int(data.get("id", 0)),
            chat_id=int(data.get("chatId", data.get("chat_id", 0))),
            author_id=int(data.get("authorId", data.get("author_id", 0))),
            text=data.get("text", ""),
            date=data.get("date", ""),
            is_system=bool(data.get("isSystem", False)),
            raw=data,
        )


@dataclass
class Command:
    id: int
    command: str = ""
    params: str = ""
    context: str = ""
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Command:
        return cls(
            id=int(data.get("id", 0)),
            command=data.get("command", ""),
            params=data.get("params", ""),
            context=data.get("context", ""),
            raw=data,
        )


@dataclass
class Message:
    """Rich message context passed to handlers. Provides shortcuts for reply."""

    data: MessageData
    chat: Chat
    user: User
    bot_id: int = 0
    _bot: Bot | None = field(default=None, repr=False)

    @property
    def text(self) -> str:
        return self.data.text

    @property
    def message_id(self) -> int:
        return self.data.id

    @property
    def dialog_id(self) -> str:
        return self.chat.dialog_id

    @property
    def from_user(self) -> User:
        return self.user

    async def answer(self, text: str, **kwargs: Any) -> dict:
        """Reply to this message."""
        if self._bot is None:
            raise RuntimeError("Message not bound to bot")
        return await self._bot.send_message(self.dialog_id, text, **kwargs)

    async def typing(self, status: str = "thinking") -> None:
        """Show typing indicator."""
        if self._bot is None:
            raise RuntimeError("Message not bound to bot")
        await self._bot.show_typing(self.dialog_id, status)

    async def react(self, reaction: str = "like") -> None:
        """Add reaction to this message."""
        if self._bot is None:
            raise RuntimeError("Message not bound to bot")
        await self._bot.add_reaction(self.message_id, reaction)


@dataclass
class Event:
    event_id: int
    type: str
    date: str = ""
    data: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Event:
        return cls(
            event_id=int(data.get("eventId", 0)),
            type=data.get("type", ""),
            date=data.get("date", ""),
            data=data.get("data", {}),
            raw=data,
        )
