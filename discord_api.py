import json
import re
import sys
from typing import Optional

try:
    import httpx
except ImportError as _exc:
    sys.exit(f"missing dependency '{_exc.name}'. run: pip install -r requirements.txt")

BASE = "https://discord.com/api/v9"
_GIFT_CODE_RE = re.compile(r"^[a-zA-Z0-9]{16,24}$")

class DiscordAPI:
    def __init__(self, token: str):
        self.token = token
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": token,
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Content-Type": "application/json",
            },
            timeout=10.0,
            http2=True,
        )

    async def redeem_nitro(self, code: str) -> bool:
        if not _GIFT_CODE_RE.match(code):
            return False
        url = f"{BASE}/entitlements/gift-code-redemptions/{code}"
        payload = {"channel_id": None, "payment_source_id": None}
        try:
            r = await self._client.post(url, json=payload)
        except httpx.RequestError:
            return False
        if r.status_code == 429:
            retry = r.headers.get("Retry-After")
            if retry:
                import asyncio
                await asyncio.sleep(float(retry))
        if r.status_code in (200, 204):
            return True
        return False

    async def check_nitro_status(self) -> Optional[dict]:
        try:
            r = await self._client.get(f"{BASE}/users/@me/billing/subscriptions")
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError:
            return None

    async def join_invite(self, code: str) -> bool:
        url = f"{BASE}/invites/{code}"
        try:
            r = await self._client.post(url, json={})
        except httpx.RequestError:
            return False
        if r.status_code == 429:
            retry = r.headers.get("Retry-After")
            if retry:
                import asyncio
                await asyncio.sleep(float(retry))
                try:
                    r = await self._client.post(url, json={})
                except httpx.RequestError:
                    return False
        return r.status_code in (200, 204)
