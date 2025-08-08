# client.py
import asyncio
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

class LocalHapiClient:
    def __init__(self, hass, host, username, password, timeout=5):
        self._base = f"http://{host}/api"
        self._auth = aiohttp.BasicAuth(username, password)
        self._session = async_get_clientsession(hass)
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _request(self, method, path, **kwargs):
        url = f"{self._base}{path}"
        for attempt in (1, 2):  # tiny retry
            try:
                async with self._session.request(
                    method, url, auth=self._auth, timeout=self._timeout, **kwargs
                ) as r:
                    r.raise_for_status()
                    if r.headers.get("Content-Type","").startswith("application/json"):
                        return await r.json()
                    return await r.read()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt == 2:
                    raise
                await asyncio.sleep(0.4)

    async def get(self, path):  return await self._request("GET", path)
    async def post(self, path): return await self._request("POST", path)

    # HAPI convenience
    async def system_info(self):        return await self.get("/system/info")
    async def switch_status(self):      return await self.get("/switch/status")
    async def switch_ctrl(self, n,a):   return await self.post(f"/switch/ctrl?switch={n}&action={a}")
    async def io_status(self):          return await self.get("/io/status")
    async def io_ctrl(self, i,a):       return await self.post(f"/io/ctrl?io={i}&action={a}")
    async def log_subscribe(self):      return await self.post("/log/subscribe")
    async def log_pull(self):           return await self.post("/log/pull")
    async def log_unsubscribe(self):    return await self.post("/log/unsubscribe")
    async def snapshot(self, cam=None): return await self.get("/camera/snapshot" + (f"?camera={cam}" if cam else ""))
