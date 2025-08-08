import logging
from typing import Any, Coroutine

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform

from py2n import Py2NDevice

from .const import DOMAIN, DEBUG_ENABLED
from .coordinator import HapiCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORM = Platform.SWITCH

def log_debug(msg, *args):
    if DEBUG_ENABLED:
        _LOGGER.debug(msg, *args)

async def async_setup_entry(hass: HomeAssistant, config: ConfigType, async_add_entities: AddEntitiesCallback):
    entry_id = config.entry_id
    data = hass.data[DOMAIN][entry_id]
    device = data["device"]
    coordinator = data["coordinator"]
    log_debug("Setting up switch entities for entry_id: %s", entry_id)
    entities = []
    for port in getattr(device.data, "ports", []):
        log_debug("Found switch port: %s", port)
        # According to 2N API, port should have 'id' and 'state'
        port_id = port.get("id") if isinstance(port, dict) else getattr(port, "id", None)
        port_state = port.get("state") if isinstance(port, dict) else getattr(port, "state", None)
        if port_id is not None:
            log_debug("Adding switch entity for port_id: %s, state: %s", port_id, port_state)
            entities.append(Helios2nPortSwitchEntity(coordinator, device, port_id))
        else:
            log_debug("Skipping port with missing id: %s", port)
    async_add_entities(entities)
    log_debug("Added %d switch entities.", len(entities))
    return True

class Helios2nPortSwitchEntity(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: HapiCoordinator, device, port_id: str) -> None:
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{self._device.data.serial}_port_{port_id}"
        self._attr_name = f"Switch {port_id}"
        self._port_id = port_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            id = self._device.data.serial,
            identifiers = {(DOMAIN, self._device.data.serial)},
            name= self._device.data.name,
            manufacturer = "2N/Helios",
            model = self._device.data.model,
            hw_version = self._device.data.hardware,
            sw_version = self._device.data.firmware,
        )

    @property
    def is_on(self) -> bool:
        for port in getattr(self._device.data, "ports", []):
            port_id = port.get("id") if isinstance(port, dict) else getattr(port, "id", None)
            port_state = port.get("state") if isinstance(port, dict) else getattr(port, "state", None)
            if port_id == self._port_id:
                return port_state == "on"
        return False

    async def async_turn_on(self, **kwargs) -> None:
        await self._device.set_port(self._port_id, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self._device.set_port(self._port_id, False)
        await self.coordinator.async_request_refresh()
