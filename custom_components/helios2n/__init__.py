from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from .const import DOMAIN, PLATFORMS
from .client import LocalHapiClient
from .coordinator import HapiCoordinator
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("Setting up 2N Helios integration for host: %s", entry.data.get(CONF_HOST))
    try:
        client = LocalHapiClient(
            hass=hass,
            host=entry.data[CONF_HOST],
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD]
        )
        coordinator = HapiCoordinator(hass, client)
        await coordinator.async_start()
        info = await client.system_info()
        _LOGGER.info("2N system info: %s", info)
        # Fetch device ports and create a device object
        # You may need to adjust this if Py2NDevice is required
        device_data = await client.switch_status()  # or another method that returns ports
        device = type("Device", (), {"data": device_data})()  # simple dynamic object with .data
        hass.data[DOMAIN][entry.entry_id] = {
            "client": client,
            "coordinator": coordinator,
            "device": device
        }
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("2N Helios integration setup complete for host: %s", entry.data.get(CONF_HOST))
        return True
    except Exception as e:
        _LOGGER.error("Error setting up 2N Helios integration: %s", e, exc_info=True)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data and "coordinator" in data:
            await data["coordinator"].async_stop()
    return unload_ok
