"""Switch platform."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, ICON_GUARD_ON, ICON_GUARD_OFF

async def async_setup_entry(hass, entry, async_add_entities):
    device_map = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, data in device_map.items():
        entities.append(EnergyGuardSwitch(
            device_id, data, "monitor_enabled", "Monitor Enabled", True, "mdi:eye", "mdi:eye-off"
        ))
        if data['switch_entity']:
            entities.append(EnergyGuardSwitch(
                device_id, data, "safety_cutoff", "Safety Cutoff Action", False, ICON_GUARD_ON, ICON_GUARD_OFF
            ))
    async_add_entities(entities)

class EnergyGuardSwitch(SwitchEntity):
    def __init__(self, device_id, data, key, name, default, icon_on, icon_off):
        self._device_id = device_id
        self._data = data
        self._key = key
        self._attr_name = name
        self._is_on = default
        self._icon_on = icon_on
        self._icon_off = icon_off
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{device_id}_{key}"

    @property
    def is_on(self):
        return self._is_on

    @property
    def icon(self):
        return self._icon_on if self.is_on else self._icon_off

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers=set(tuple(x) for x in self._data["identifiers"]),
            connections=set(tuple(x) for x in self._data["connections"])
        )

    async def async_turn_on(self, **kwargs):
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        self.async_write_ha_state()