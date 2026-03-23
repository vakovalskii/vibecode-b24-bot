"""Low-level async HTTP client for VibeCode API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

logger = logging.getLogger("vibecode")

DEFAULT_BASE = "https://vibecode.bitrix24.tech/v1"


class APIError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class VibeCode:
    """Async client for VibeCode API.

    Usage::

        async with VibeCode(api_key="vibe_api_...") as client:
            me = await client.me()
            deals = await client.get("/deals", limit=50)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE,
        max_retries: int = 5,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "X-Api-Key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> VibeCode:
        await self._ensure_session()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        session = await self._ensure_session()
        url = f"{self.base_url}{path}"

        for attempt in range(self.max_retries):
            try:
                async with session.request(method, url, **kwargs) as resp:
                    if resp.status == 429:
                        wait = min(2 ** attempt, 30)
                        logger.warning("Rate limited, retry in %ds", wait)
                        await asyncio.sleep(wait)
                        continue

                    data = await resp.json()

                    if not data.get("success", True):
                        err = data.get("error", {})
                        raise APIError(
                            err.get("code", "UNKNOWN"),
                            err.get("message", str(data)),
                        )
                    return data.get("data", data.get("result", data))

            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    wait = min(2 ** attempt, 30)
                    logger.warning("Network error: %s, retry in %ds", e, wait)
                    await asyncio.sleep(wait)
                else:
                    raise

        raise APIError("MAX_RETRIES", "Exceeded max retries")

    async def get(self, path: str, **params: Any) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, **body: Any) -> Any:
        return await self.request("POST", path, json=body)

    async def patch(self, path: str, **body: Any) -> Any:
        return await self.request("PATCH", path, json=body)

    async def delete(self, path: str, **params: Any) -> Any:
        return await self.request("DELETE", path, params=params)

    # --- Shortcuts ---

    async def me(self) -> dict:
        return await self.get("/me")

    async def guide(self) -> dict:
        return await self.get("/guide")

    async def batch(self, calls: list[dict]) -> Any:
        return await self.post("/batch", calls=calls)

    async def call(self, method: str, params: dict | None = None) -> Any:
        return await self.post("/call", method=method, params=params or {})

    # --- Entity CRUD ---

    async def list_entity(self, entity: str, limit: int = 50, offset: int = 0) -> list:
        return await self.get(f"/{entity}", limit=limit, offset=offset)

    async def get_entity(self, entity: str, id: int) -> dict:
        return await self.get(f"/{entity}/{id}")

    async def create_entity(self, entity: str, **fields: Any) -> dict:
        return await self.post(f"/{entity}", **fields)

    async def update_entity(self, entity: str, id: int, **fields: Any) -> dict:
        return await self.patch(f"/{entity}/{id}", **fields)

    async def delete_entity(self, entity: str, id: int) -> Any:
        return await self.delete(f"/{entity}/{id}")

    async def search_entity(self, entity: str, **query: Any) -> list:
        return await self.post(f"/{entity}/search", **query)
