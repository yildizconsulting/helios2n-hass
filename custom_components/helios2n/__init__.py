from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from .const import DOMAIN, PLATFORMS, DEBUG_ENABLED
from .client import LocalHapiClient
from .coordinator import HapiCoordinator
import logging

_LOGGER = logging.getLogger(__name__)

def log_debug(msg, *args):
    if DEBUG_ENABLED:
        _LOGGER.debug(msg, *args)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("Setting up 2N Helios integration for host: %s", entry.data.get(CONF_HOST))
    try:
        log_debug("Creating LocalHapiClient...")
        client = LocalHapiClient(
            hass=hass,
            host=entry.data[CONF_HOST],
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD]
        )
        log_debug("LocalHapiClient created: %s", client)
        coordinator = HapiCoordinator(hass, client)
        log_debug("Starting HapiCoordinator...")
        await coordinator.async_start()
        log_debug("HapiCoordinator started.")
        info = await client.system_info()
        log_debug("Full system_info response: %s", info)
        device_data = await client.switch_status()
        log_debug("Full switch_status response: %s", device_data)
        # Use correct keys from API response
        info_result = info.get("result", {}) if isinstance(info, dict) else {}
        switch_result = device_data.get("result", {}) if isinstance(device_data, dict) else {}
        switches = []
        for sw in switch_result.get("switches", []):
            # Ensure each switch has id, name, and state
            switch_id = sw.get("id")
            switch_name = sw.get("name", f"Relay {sw.get('id', '?')}")
            switch_state = sw.get("state", "unknown")
            switches.append({
                "id": switch_id,
                "name": switch_name,
                "state": switch_state
            })
            log_debug("Found switch: id=%s, name=%s, state=%s", switch_id, switch_name, switch_state)
        device_obj = type("Device", (), {
            "data": type("DeviceData", (), {
                "serial": info_result.get("serialNumber", "unknown"),
                "mac": info_result.get("mac", "unknown"),
                "name": info_result.get("deviceName", "2N Helios"),
                "model": info_result.get("model", "unknown"),
                "hardware": info_result.get("hwVersion", "unknown"),
                "firmware": info_result.get("swVersion", "unknown"),
                "ports": switches
            })()
        })()
        log_debug("Device object created: %s", device_obj)
        hass.data[DOMAIN][entry.entry_id] = {
            "client": client,
            "coordinator": coordinator,
            "device": device_obj
        }
        log_debug("Stored client, coordinator, and device in hass.data.")
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("2N Helios integration setup complete for host: %s", entry.data.get(CONF_HOST))
        return True
    except Exception as e:
        _LOGGER.error("Error setting up 2N Helios integration: %s", e, exc_info=True)
        log_debug("Exception during setup: %s", e)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    log_debug("Unloading entry for host: %s", entry.data.get(CONF_HOST))
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        log_debug("Removed data for entry_id: %s", entry.entry_id)
        if data and "coordinator" in data:
            await data["coordinator"].async_stop()
            log_debug("Stopped coordinator for entry_id: %s", entry.entry_id)
    return unload_ok
