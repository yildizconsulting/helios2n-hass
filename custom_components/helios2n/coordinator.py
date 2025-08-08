# coordinator.py
import logging
from datetime import timedelta
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_interval


_LOGGER = logging.getLogger(__name__)



class HapiCoordinator:
    def __init__(self, hass, client):
        self.hass = hass
        self.client = client
        self._cancel = None

    async def async_start(self):
        await self.client.log_subscribe()
        self._cancel = async_track_time_interval(self.hass, self._pull, timedelta(seconds=3))

    async def async_stop(self):
        if self._cancel: self._cancel()
        await self.client.log_unsubscribe()

    async def _pull(self, now):
        events = await self.client.log_pull() or []
        for e in events:
            t = (e.get("Type") or e.get("type") or "").lower()
            self.hass.bus.async_fire("my2n_event", e)
            # update your sensors here (ring/motion/input)
