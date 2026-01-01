"""Sensor platform."""
import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.core import callback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor entities."""
    device_settings = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, settings in device_settings.items():
        entities.extend([
            EnergyGuardPeakSensor(
                device_id, settings, "max_peak", "Guard: Max Peak"
            ),
            EnergyGuardCounterSensor(
                device_id, settings, "trip_count", "Guard: Trip Count"
            ),
        ])
    async_add_entities(entities)

class EnergyGuardPeakSensor(SensorEntity, RestoreEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "W"
    _attr_icon = "mdi:chart-histogram"
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device_id, settings, key, name):
        self._device_id = device_id
        self._settings = settings
        self._source_entity = settings["power_sensor"]
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_name = name
        self._attr_native_value = 0

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link to the original device."""
        return DeviceInfo(
            identifiers=self._settings["identifiers"],
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._attr_native_value = float(last_state.state)
            except ValueError:
                self._attr_native_value = 0
        
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._source_entity], self._on_state_change)
        )
        self.async_on_remove(
            self.hass.bus.async_listen(f"energy_guard_reset_{self._device_id}", self._handle_reset)
        )

    @callback
    def _on_state_change(self, event):
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
            
            if val > (self._attr_native_value or 0):
                self._attr_native_value = val
                self.async_write_ha_state()
        except ValueError:
            pass

    @callback
    def _handle_reset(self, event):
        self._attr_native_value = 0
        self.async_write_ha_state()

class EnergyGuardCounterSensor(SensorEntity, RestoreEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device_id, settings, key, name):
        self._device_id = device_id
        self._settings = settings
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_name = name
        self._attr_native_value = 0

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link to the original device."""
        return DeviceInfo(
            identifiers=self._settings["identifiers"],
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and str(last_state.state).isdigit():
            self._attr_native_value = int(last_state.state)
        
        self.async_on_remove(
            self.hass.bus.async_listen(f"energy_guard_increment_{self._device_id}", self._handle_increment)
        )
        self.async_on_remove(
            self.hass.bus.async_listen(f"energy_guard_reset_{self._device_id}", self._handle_reset)
        )

    @callback
    def _handle_increment(self, event):
        self._attr_native_value = int(self._attr_native_value or 0) + 1
        self.async_write_ha_state()

    @callback
    def _handle_reset(self, event):
        self._attr_native_value = 0
        self.async_write_ha_state()