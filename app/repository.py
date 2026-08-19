"""Thin Supabase PostgREST gateway. All production persistence goes through Supabase."""
from typing import Any
import httpx
from .config import Settings


class SupabaseRepository:
    def __init__(self, settings: Settings, access_token: str):
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY are required")
        self.base = f"{settings.supabase_url.rstrip('/')}/rest/v1"
        self.headers = {"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    async def request(self, method: str, table: str, *, params: dict | None = None, json: Any = None, prefer: str = "return=representation") -> list[dict]:
        headers = {**self.headers, "Prefer": prefer}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(method, f"{self.base}/{table}", params=params, json=json, headers=headers)
        response.raise_for_status()
        return response.json() if response.content else []

    async def one(self, table: str, filters: dict) -> dict | None:
        rows = await self.request("GET", table, params={**filters, "limit": "1"})
        return rows[0] if rows else None

    async def insert(self, table: str, row: dict) -> dict:
        return (await self.request("POST", table, json=row))[0]

    async def update(self, table: str, filters: dict, row: dict) -> dict | None:
        rows = await self.request("PATCH", table, params=filters, json=row)
        return rows[0] if rows else None

    async def delete(self, table: str, filters: dict) -> None:
        await self.request("DELETE", table, params=filters, prefer="return=minimal")
