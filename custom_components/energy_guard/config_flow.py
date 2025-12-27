"""Config flow for Energy Guard."""
import logging
from typing import Any, Dict
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

class EnergyGuardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.selected_devices = []

    async def async_step_user(self, user_input: Dict[str, Any] | None = None):
        if user_input is not None:
            self.selected_devices = user_input["devices"]
            return await self.async_step_sensors()

        valid_devices = self._get_devices()
        if not valid_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("devices"): cv.multi_select(valid_devices)
            }),
        )

    async def async_step_sensors(self, user_input: Dict[str, Any] | None = None):
        if user_input is not None:
            stored_data = {}
            for key, entity_id in user_input.items():
                if key.startswith("sensor_"):
                    device_id = key.replace("sensor_", "")
                    stored_data[device_id] = entity_id

            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={"selection_map": stored_data}
            )

        schema_dict = {}
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)

        for device_id in self.selected_devices:
            device_sensors = {}
            entries = er.async_entries_for_device(ent_reg, device_id)
            for entry in entries:
                if entry.domain == "sensor":
                    label = f"{entry.entity_id} ({entry.original_name or entry.name or ''})"
                    device_sensors[entry.entity_id] = label
            
            if device_sensors:
                first_val = list(device_sensors.keys())[0]
                schema_dict[vol.Required(f"sensor_{device_id}", default=first_val)] = vol.In(device_sensors)

        return self.async_show_form(step_id="sensors", data_schema=vol.Schema(schema_dict))

    def _get_devices(self):
        dev_reg = dr.async_get(self.hass)
        ent_reg = er.async_get(self.hass)
        valid = {}
        for entity in ent_reg.entities.values():
            if entity.domain == "sensor" and entity.device_id:
                if entity.device_id not in valid:
                    dev = dev_reg.async_get(entity.device_id)
                    if dev:
                        name = dev.name_by_user or dev.name or f"Device {dev.id}"
                        valid[entity.device_id] = f"{name} ({dev.manufacturer})"
        return valid