import re
import pytest
from unittest.mock import patch, AsyncMock
from aioresponses import aioresponses

from vibecode_b24_bot.client import VibeCode, APIError

BASE = "https://vibecode.bitrix24.tech/v1"
# Use regex patterns for URLs with query params
DEALS_RE = re.compile(r"^https://vibecode\.bitrix24\.tech/v1/deals(\?.*)?$")
TASKS_RE = re.compile(r"^https://vibecode\.bitrix24\.tech/v1/tasks(\?.*)?$")


@pytest.fixture
async def client():
    c = VibeCode(api_key="test_key")
    yield c
    await c.close()


async def test_get_returns_data(client):
    with aioresponses() as m:
        m.get(DEALS_RE, payload={"success": True, "data": [{"ID": 1}]})
        result = await client.get("/deals", limit=10)
        assert result == [{"ID": 1}]


async def test_post_returns_data(client):
    with aioresponses() as m:
        m.post(f"{BASE}/deals", payload={"success": True, "data": {"id": 1}})
        result = await client.post("/deals", title="Test")
        assert result == {"id": 1}


async def test_patch_sends_json(client):
    with aioresponses() as m:
        m.patch(f"{BASE}/deals/1", payload={"success": True, "data": {"ok": True}})
        result = await client.patch("/deals/1", stageId="WON")
        assert result == {"ok": True}


async def test_delete(client):
    with aioresponses() as m:
        m.delete(f"{BASE}/deals/1", payload={"success": True, "result": True})
        result = await client.delete("/deals/1")
        assert result is True


async def test_api_error_raised(client):
    with aioresponses() as m:
        m.get(f"{BASE}/deals", payload={
            "success": False,
            "error": {"code": "ACCESS_DENIED", "message": "No access"},
        })
        with pytest.raises(APIError) as exc:
            await client.get("/deals")
        assert exc.value.code == "ACCESS_DENIED"
        assert "No access" in exc.value.message


async def test_retry_on_429(client):
    with aioresponses() as m:
        m.get(f"{BASE}/me", status=429, payload={})
        m.get(f"{BASE}/me", payload={"success": True, "data": {"portal": "test"}})

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.get("/me")
            assert result["portal"] == "test"


async def test_max_retries_exceeded(client):
    client.max_retries = 2
    with aioresponses() as m:
        m.get(f"{BASE}/me", status=429, repeat=True)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(APIError, match="MAX_RETRIES"):
                await client.get("/me")


async def test_context_manager():
    async with VibeCode(api_key="test_key") as client:
        assert client._session is not None
        assert not client._session.closed
    assert client._session.closed


async def test_me_shortcut(client):
    with aioresponses() as m:
        m.get(f"{BASE}/me", payload={"success": True, "data": {"portal": "test.bitrix24.ru"}})
        result = await client.me()
        assert result["portal"] == "test.bitrix24.ru"


async def test_batch_shortcut(client):
    with aioresponses() as m:
        m.post(f"{BASE}/batch", payload={"success": True, "data": [{"result": 1}, {"result": 2}]})
        result = await client.batch([{"method": "crm.status.list"}])
        assert len(result) == 2


async def test_entity_list(client):
    with aioresponses() as m:
        m.get(TASKS_RE, payload={"success": True, "data": []})
        result = await client.list_entity("tasks", limit=10)
        assert result == []


async def test_entity_get(client):
    with aioresponses() as m:
        m.get(f"{BASE}/deals/42", payload={"success": True, "data": {"ID": 42, "TITLE": "X"}})
        result = await client.get_entity("deals", 42)
        assert result["ID"] == 42


async def test_entity_create(client):
    with aioresponses() as m:
        m.post(f"{BASE}/contacts", payload={"success": True, "data": {"id": 1}})
        result = await client.create_entity("contacts", name="Alice")
        assert result["id"] == 1


async def test_entity_update(client):
    with aioresponses() as m:
        m.patch(f"{BASE}/deals/1", payload={"success": True, "data": {"ok": True}})
        result = await client.update_entity("deals", 1, stageId="WON")
        assert result["ok"] is True


async def test_entity_delete(client):
    with aioresponses() as m:
        m.delete(f"{BASE}/deals/1", payload={"success": True, "result": True})
        result = await client.delete_entity("deals", 1)
        assert result is True


async def test_entity_search(client):
    with aioresponses() as m:
        m.post(f"{BASE}/deals/search", payload={"success": True, "data": [{"ID": 1}]})
        result = await client.search_entity("deals", filter={"stageId": "NEW"})
        assert len(result) == 1
