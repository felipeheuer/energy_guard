"""Config flow for Energy Guard, following the Battery Notes pattern."""
import logging
from typing import Any, Dict, List

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import device_registry as dr, entity_registry as er
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)


async def _get_power_devices_map(hass) -> Dict[str, List[str]]:
    """Scans for devices with both a switch and a power sensor."""
    power_devices = {}
    ent_reg = er.async_get(hass)
    
    switch_devices = {
        entity.device_id
        for entity in ent_reg.entities.values()
        if entity.domain == "switch" and entity.device_id
    }

    for entity in ent_reg.entities.values():
        if (
            entity.device_id in switch_devices
            and entity.domain == "sensor"
            and entity.unit_of_measurement in ("W", "kW")
        ):
            power_devices.setdefault(entity.device_id, []).append(entity.entity_id)
            
    return power_devices


async def _get_device_names(hass, device_ids: List[str]) -> Dict[str, str]:
    """Gets friendly names for a list of device IDs."""
    dev_reg = dr.async_get(hass)
    device_names = {
        device_id: (dev.name_by_user or dev.name or f"Device {dev.id}")
        for device_id in device_ids
        if (dev := dev_reg.async_get(device_id)) and not dev.disabled_by
    }
    return dict(sorted(device_names.items(), key=lambda item: item[1]))


class EnergyGuardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handles the config flow for Energy Guard."""
    VERSION = 1

    def __init__(self):
        self.power_devices_map: Dict[str, List[str]] = {}
        self.selected_devices: List[str] = []
        self.existing_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Find the single instance of this integration, if it exists
        if self.hass.config_entries.async_entries(DOMAIN):
            self.existing_entry = self.hass.config_entries.async_entries(DOMAIN)[0]

        if user_input is not None:
            self.selected_devices = user_input["devices"]
            return await self.async_step_sensors()

        self.power_devices_map = await _get_power_devices_map(self.hass)
        if not self.power_devices_map:
            return self.async_abort(reason="no_power_devices_found")

        # Exclude devices that are already configured
        if self.existing_entry:
            current_selection = self.existing_entry.data.get("selection_map", {})
            available_devices = {
                k: v for k, v in self.power_devices_map.items() if k not in current_selection
            }
        else:
            available_devices = self.power_devices_map

        if not available_devices:
            return self.async_abort(reason="no_new_devices_found")

        device_names = await _get_device_names(self.hass, list(available_devices.keys()))
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("devices"): cv.multi_select(device_names)}),
            last_step=False,
        )

    async def async_step_sensors(self, user_input=None):
        """Handle the sensor selection step."""
        if user_input is not None:
            selection_map = {}
            if self.existing_entry:
                # Get the existing map and update it
                selection_map = self.existing_entry.data.get("selection_map", {}).copy()

            ent_reg = er.async_get(self.hass)
            for entity_id in user_input.values():
                entry = ent_reg.async_get(entity_id)
                if entry and entry.device_id:
                    selection_map[entry.device_id] = entity_id
            
            if self.existing_entry:
                # Update the existing entry's data
                self.hass.config_entries.async_update_entry(
                    self.existing_entry, data={"selection_map": selection_map}
                )
                # End the flow
                return self.async_abort(reason="reconfigure_successful")
            else:
                # Create a new entry
                return self.async_create_entry(title=DEFAULT_NAME, data={"selection_map": selection_map})

        device_names = await _get_device_names(self.hass, self.selected_devices)
        schema = {}
        for device_id in self.selected_devices:
            power_sensors = self.power_devices_map.get(device_id, [])
            sensor_options = {s: f"{s.split('.')[-1].replace('_', ' ').title()} ({s})" for s in power_sensors}

            if sensor_options:
                device_name = device_names.get(device_id, device_id)
                schema[vol.Required(device_name, default=power_sensors[0])] = vol.In(sensor_options)

        return self.async_show_form(step_id="sensors", data_schema=vol.Schema(schema))