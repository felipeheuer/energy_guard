"""Switch platform for Energy Guard."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import STATE_ON
from .const import DOMAIN, ICON_GUARD_ON, ICON_GUARD_OFF

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch entities."""
    device_settings = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, settings in device_settings.items():
        entities.extend([
            EnergyGuardSwitch(
                device_id, settings, "monitor_enabled", "Guard: Monitor Enabled", True, "mdi:eye", "mdi:eye-off"
            ),
            EnergyGuardSwitch(
                device_id,
                settings,
                "safety_cutoff",
                "Guard: Safety Cutoff",
                settings.get("safety_cutoff_enabled"),
                ICON_GUARD_ON,
                ICON_GUARD_OFF,
            ),
        ])
    async_add_entities(entities)

class EnergyGuardSwitch(SwitchEntity, RestoreEntity):
    """Representation of an Energy Guard switch entity."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True

    def __init__(self, device_id, settings, key, name, default, icon_on, icon_off):
        """Initialize the switch entity."""
        self._device_id = device_id
        self._settings = settings
        self._key = key
        self._attr_name = name
        self._is_on = default
        self._icon_on = icon_on
        self._icon_off = icon_off
        self._attr_unique_id = f"{device_id}_{key}"

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._is_on

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon_on if self.is_on else self._icon_off

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link to the original device."""
        return DeviceInfo(
            identifiers=self._settings["identifiers"],
        )

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state is not None:
            self._is_on = last_state.state == STATE_ON

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        self._is_on = False
        self.async_write_ha_state()