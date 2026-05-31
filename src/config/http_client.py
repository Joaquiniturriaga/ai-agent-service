import httpx
from src.config.settings import settings

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0),
            headers={
                "Content-Type": "application/json",
                "x-internal-key": settings.INTERNAL_SECRET,
                "x-user-id": "0",
                "x-user-role": "admin",
                "x-user-brigade": "null",
            },
        )
    return _client


async def close_client():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()