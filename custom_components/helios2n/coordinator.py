# coordinator.py
import logging
from datetime import timedelta
import async_timeout
from .const import DEBUG_ENABLED

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_interval


_LOGGER = logging.getLogger(__name__)

def log_debug(msg, *args):
    if DEBUG_ENABLED:
        _LOGGER.debug(msg, *args)

class HapiCoordinator:
    def __init__(self, hass, client):
        self.hass = hass
        self.client = client
        self._cancel = None
        log_debug("HapiCoordinator initialized.")

    async def async_start(self):
        log_debug("Subscribing to log events...")
        await self.client.log_subscribe()
        self._cancel = async_track_time_interval(self.hass, self._pull, timedelta(seconds=3))
        log_debug("Log subscription started.")

    async def async_stop(self):
        log_debug("Unsubscribing from log events...")
        if self._cancel: self._cancel()
        await self.client.log_unsubscribe()
        log_debug("Log subscription stopped.")

    async def _pull(self, now):
        log_debug("Pulling events from log...")
        events = await self.client.log_pull() or []
        log_debug("Events pulled: %s", events)
        for e in events:
            t = (e.get("Type") or e.get("type") or "").lower()
            self.hass.bus.async_fire("my2n_event", e)
            log_debug("Fired event: %s", e)
            # update your sensors here (ring/motion/input)
