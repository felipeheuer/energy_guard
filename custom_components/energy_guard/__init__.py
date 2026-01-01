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

    device_settings = {}
    config_devices = entry.data.get("devices", {})

    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    for device_id, settings in config_devices.items():
        device = dev_reg.async_get(device_id)
        if not device:
            _LOGGER.warning(f"Device with ID {device_id} not found, skipping.")
            continue

        control_switch_id = None
        for entity in er.async_entries_for_device(ent_reg, device_id):
            if entity.domain == "switch" and entity.platform != DOMAIN:
                control_switch_id = entity.entity_id
                break
        
        if not control_switch_id:
            _LOGGER.warning(
                f"No controllable switch found for device {device.name} ({device_id}), skipping."
            )
            continue
            
        device_settings[device_id] = {
            "power_sensor": settings["power_sensor"],
            "peak_power": settings["peak_power"],
            "trip_delay": settings["trip_delay"],
            "safety_cutoff_enabled": settings["safety_cutoff_enabled"],
            "switch_entity": control_switch_id,
            "device_name": device.name or "Unknown Device",
            "identifiers": device.identifiers,
        }

    hass.data[DOMAIN][entry.entry_id] = device_settings
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)