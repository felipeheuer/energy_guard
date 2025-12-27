"""The Energy Guard integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "number", "switch", "button"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Energy Guard from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Data structure: { "switch.example": { "power_entity": "sensor.w", ... }, ... }
    devices_data = entry.data.get("devices", {})
    
    clean_map = {}

    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    for switch_id, config in devices_data.items():
        identifiers = set()
        connections = set()
        
        # Link to physical device if possible
        registry_entry = ent_reg.async_get(switch_id)
        if registry_entry and registry_entry.device_id:
            device = dev_reg.async_get(registry_entry.device_id)
            if device:
                identifiers = device.identifiers
                connections = device.connections

        # Fallback to virtual identifier
        if not identifiers:
            identifiers = {(DOMAIN, switch_id)}

        clean_map[switch_id] = {
            "power_entity": config["power_entity"],
            "switch_entity": config.get("switch_entity", switch_id),
            "identifiers": identifiers,
            "connections": connections,
            "original_name": registry_entry.original_name if registry_entry else switch_id
        }

    hass.data[DOMAIN][entry.entry_id] = clean_map

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok