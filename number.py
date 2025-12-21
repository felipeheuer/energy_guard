"""Number platform."""
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, DEFAULT_LIMIT_W, DEFAULT_DELAY_SEC

async def async_setup_entry(hass, entry, async_add_entities):
    device_map = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, data in device_map.items():
        entities.append(EnergyGuardNumber(
            device_id, data, "power_limit", "Power Limit", "W", DEFAULT_LIMIT_W, 0, 10000, 10, "mdi:lightning-bolt"
        ))
        entities.append(EnergyGuardNumber(
            device_id, data, "trip_delay", "Trip Delay", "s", DEFAULT_DELAY_SEC, 0, 60, 1, "mdi:timer-outline"
        ))
    async_add_entities(entities)

class EnergyGuardNumber(NumberEntity):
    def __init__(self, device_id, data, key, name, unit, default, min_v, max_v, step, icon):
        self._device_id = device_id
        self._data = data
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_native_value = default
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_step = step
        self._attr_icon = icon
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_mode = NumberMode.BOX

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers=set(tuple(x) for x in self._data["identifiers"]),
            connections=set(tuple(x) for x in self._data["connections"])
        )

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()