"""BB-code formatting helpers for Bitrix24 chat messages.

Bitrix24 uses BB-codes, NOT Markdown. Use these helpers to format messages.

Usage::

    from vibecode import bb

    bb.bold("Important!")              # [b]Important![/b]
    bb.italic("Note")                  # [i]Note[/i]
    bb.code("print('hello')")         # [code]print('hello')[/code]
    bb.link("https://example.com")    # [url]https://example.com[/url]
"""


class bb:
    """BB-code formatter for Bitrix24 chat."""

    @staticmethod
    def bold(text: str) -> str:
        return f"[b]{text}[/b]"

    @staticmethod
    def italic(text: str) -> str:
        return f"[i]{text}[/i]"

    @staticmethod
    def underline(text: str) -> str:
        return f"[u]{text}[/u]"

    @staticmethod
    def strike(text: str) -> str:
        return f"[s]{text}[/s]"

    @staticmethod
    def code(text: str) -> str:
        return f"[code]{text}[/code]"

    @staticmethod
    def link(url: str, text: str | None = None) -> str:
        if text:
            return f"[url={url}]{text}[/url]"
        return f"[url]{url}[/url]"

    @staticmethod
    def quote(text: str) -> str:
        return f"[quote]{text}[/quote]"

    @staticmethod
    def list(items: list[str]) -> str:
        body = "".join(f"[*]{item}" for item in items)
        return f"[list]{body}[/list]"

    @staticmethod
    def mention(user_id: int) -> str:
        return f"[user={user_id}][/user]"

    @staticmethod
    def strip(text: str) -> str:
        """Remove all BB-codes from text."""
        import re
        return re.sub(r"\[/?[a-z]+(?:=[^\]]+)?\]", "", text)
