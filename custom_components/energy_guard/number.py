"""Number platform for Energy Guard."""
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN, DEFAULT_POWER_LIMIT, DEFAULT_TRIP_DELAY

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the number entities."""
    device_settings = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, settings in device_settings.items():
        entities.extend([
            EnergyGuardNumber(
                device_id,
                settings,
                "peak_power",
                "Guard: Power Limit",
                "W",
                settings.get("peak_power", DEFAULT_POWER_LIMIT),
                0,
                10000,
                1,
                "mdi:lightning-bolt",
            ),
            EnergyGuardNumber(
                device_id,
                settings,
                "trip_delay",
                "Guard: Trip Delay",
                "s",
                settings.get("trip_delay", DEFAULT_TRIP_DELAY),
                0,
                60,
                1,
                "mdi:timer-outline",
            ),
        ])
    async_add_entities(entities)

class EnergyGuardNumber(NumberEntity, RestoreEntity):
    """Representation of an Energy Guard number entity."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(
        self, device_id, settings, key, name, unit, default, min_v, max_v, step, icon
    ):
        """Initialize the number entity."""
        self._device_id = device_id
        self._settings = settings
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_native_value = default
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_step = step
        self._attr_icon = icon
        self._attr_unique_id = f"{device_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._settings["device_name"],
        )

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._attr_native_value = float(last_state.state)
            except (ValueError, TypeError):
                pass

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        self.async_write_ha_state()