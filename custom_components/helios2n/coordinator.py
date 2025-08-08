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
        # Handle error response gracefully
        if isinstance(events, dict) and not events.get("success", True):
            log_debug("Log pull error: %s", events.get("error"))
            return
        if not isinstance(events, list):
            log_debug("Events is not a list, skipping event processing.")
            return
        for e in events:
            if isinstance(e, dict):
                self.hass.bus.async_fire("my2n_event", e)
                log_debug("Fired event: %s", e)
            else:
                log_debug("Event is not a dict: %s", e)
            # update your sensors here (ring/motion/input)
