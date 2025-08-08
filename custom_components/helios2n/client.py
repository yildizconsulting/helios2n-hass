# client.py
import asyncio
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DEBUG_ENABLED
import logging

_LOGGER = logging.getLogger(__name__)

def log_debug(msg, *args):
    if DEBUG_ENABLED:
        _LOGGER.debug(msg, *args)

class LocalHapiClient:
    def __init__(self, hass, host, username, password, timeout=5):
        self._base = f"http://{host}/api"
        self._auth = aiohttp.BasicAuth(username, password)
        self._session = async_get_clientsession(hass)
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        log_debug("Initialized LocalHapiClient for host: %s", host)

    async def _request(self, method, path, **kwargs):
        url = f"{self._base}{path}"
        log_debug("Requesting %s %s", method, url)
        for attempt in (1, 2):  # tiny retry
            try:
                async with self._session.request(
                    method, url, auth=self._auth, timeout=self._timeout, **kwargs
                ) as r:
                    r.raise_for_status()
                    log_debug("Response status: %s", r.status)
                    if r.headers.get("Content-Type","").startswith("application/json"):
                        result = await r.json()
                        log_debug("JSON response: %s", result)
                        return result
                    result = await r.read()
                    log_debug("Raw response: %s", result)
                    return result
            except (aiohttp.ClientError, asyncio.TimeoutError) as ex:
                log_debug("Request error on attempt %d: %s", attempt, ex)
                if attempt == 2:
                    raise
                await asyncio.sleep(0.4)

    async def get(self, path):
        log_debug("GET %s", path)
        return await self._request("GET", path)
    async def post(self, path):
        log_debug("POST %s", path)
        return await self._request("POST", path)

    # HAPI convenience
    async def system_info(self):
        log_debug("Fetching system_info...")
        return await self.get("/system/info")
    async def switch_status(self):
        log_debug("Fetching switch_status...")
        return await self.get("/switch/status")
    async def switch_ctrl(self, n,a):
        log_debug("Controlling switch: %s, action: %s", n, a)
        return await self.post(f"/switch/ctrl?switch={n}&action={a}")
    async def io_status(self):
        log_debug("Fetching io_status...")
        return await self.get("/io/status")
    async def io_ctrl(self, i,a):
        log_debug("Controlling io: %s, action: %s", i, a)
        return await self.post(f"/io/ctrl?io={i}&action={a}")
    async def log_subscribe(self):
        log_debug("Subscribing to log...")
        return await self.post("/log/subscribe")
    async def log_pull(self):
        log_debug("Pulling log...")
        return await self.post("/log/pull")
    async def log_unsubscribe(self):
        log_debug("Unsubscribing from log...")
        return await self.post("/log/unsubscribe")
    async def snapshot(self, cam=None):
        log_debug("Fetching snapshot for camera: %s", cam)
        return await self.get("/camera/snapshot" + (f"?camera={cam}" if cam else ""))
