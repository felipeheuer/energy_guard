"""Button platform."""
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory # <--- IMPORT NOVO
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    device_map = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, data in device_map.items():
        entities.append(EnergyGuardResetButton(device_id, data))
    async_add_entities(entities)

class EnergyGuardResetButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Reset Statistics"
    _attr_icon = "mdi:restart"
    
    # ADICIONADO
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device_id, data):
        self._device_id = device_id
        self._data = data
        self._attr_unique_id = f"{device_id}_reset_btn"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers=set(tuple(x) for x in self._data["identifiers"]),
            connections=set(tuple(x) for x in self._data["connections"])
        )

    async def async_press(self) -> None:
        self.hass.bus.async_fire(f"energy_guard_reset_{self._device_id}")