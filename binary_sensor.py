"""Binary sensor platform."""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.core import callback
from .const import DOMAIN, ICON_ALERT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    device_map = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, data in device_map.items():
        entities.append(EnergyGuardBinarySensor(device_id, data))
    async_add_entities(entities)

class EnergyGuardBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Overload Alert"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, device_id, data):
        self._device_id = device_id
        self._data = data
        self._source_entity = data["power_entity"]
        self._cutoff_switch = data["switch_entity"]
        self._attr_unique_id = f"{device_id}_alert"
        self._attr_is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers=set(tuple(x) for x in self._data["identifiers"]),
            connections=set(tuple(x) for x in self._data["connections"])
        )

    @property
    def icon(self):
        return ICON_ALERT if self.is_on else "mdi:shield-check"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._source_entity], self._check_power)
        )

    @callback
    def _check_power(self, event):
        new_state = event.data.get("new_state")
        if not new_state or new_state.state in ("unknown", "unavailable"):
            return
        
        try:
            raw = new_state.state.replace(',', '.').strip()
            clean = ''.join(c for c in raw if c.isdigit() or c == '.')
            val = float(clean)
            
            unit = (new_state.attributes.get("unit_of_measurement") or "").lower()
            if unit in ["kw", "kilowatt"]:
                val *= 1000.0
            
            # Logic placeholder for V2
        except ValueError:
            pass