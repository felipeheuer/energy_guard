"""Init for Energy Guard."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Energy Guard from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    selection_map = entry.data.get("selection_map", {})
    device_map = {}
    
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    
    for device_id, power_sensor_id in selection_map.items():
        device = dev_reg.async_get(device_id)
        if not device:
            continue

        control_switch_id = None
        for entity in er.async_entries_for_device(ent_reg, device_id):
            if entity.domain == "switch" and entity.platform != DOMAIN:
                control_switch_id = entity.entity_id
                break
        
        device_map[device_id] = {
            "power_entity": power_sensor_id,
            "switch_entity": control_switch_id,
            "identifiers": device.identifiers,
            "connections": device.connections,
            "name": device.name or "Unknown"
        }

    hass.data[DOMAIN][entry.entry_id] = device_map
    
    # Set up a listener to automatically reload the integration when data is updated
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    # Forward the setup to all platforms (sensor, switch, etc.)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)