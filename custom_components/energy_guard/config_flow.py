"""Config flow for Energy Guard."""
import logging
from typing import Any, Dict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import device_registry as dr, entity_registry as er
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)


class EnergyGuardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Energy Guard."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.selected_devices = []
        self.power_devices_map: Dict[str, list[str]] = {}

    async def async_step_user(self, user_input: Dict[str, Any] | None = None):
        """
        Handle the initial step where the user selects devices
        that have power-monitoring entities.
        """
        if user_input is not None:
            self.selected_devices = user_input["devices"]
            return await self.async_step_sensors()

        # Find all devices that have at least one power sensor (W or kW)
        self.power_devices_map = await self._get_power_devices_map()

        if not self.power_devices_map:
            return self.async_abort(reason="no_power_devices_found")

        # Get user-friendly names for the discovered devices
        device_names = await self._get_device_names(list(self.power_devices_map.keys()))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("devices"): cv.multi_select(device_names)}
            ),
            last_step=False,
        )

    async def async_step_sensors(self, user_input: Dict[str, Any] | None = None):
        """
        For each selected device, ask the user to confirm the power sensor.
        Auto-selects the first one found if multiple exist.
        """
        ent_reg = er.async_get(self.hass)

        if user_input is not None:
            selection_map = {}
            # User input is now { friendly_device_name: entity_id }
            # We need to get the device_id from the entity_id
            for entity_id in user_input.values():
                entry = ent_reg.async_get(entity_id)
                if entry and entry.device_id:
                    selection_map[entry.device_id] = entity_id

            return self.async_create_entry(
                title=DEFAULT_NAME, data={"selection_map": selection_map}
            )

        schema_fields = {}
        device_names_list = await self._get_device_names(self.selected_devices)

        for device_id in self.selected_devices:
            power_sensors = self.power_devices_map.get(device_id, [])

            # Create a dictionary of {entity_id: friendly_name} for the dropdown
            sensor_options = {}
            for entity_id in power_sensors:
                entry = ent_reg.async_get(entity_id)
                if entry:
                    name = entry.original_name or entry.name or entity_id
                    sensor_options[entity_id] = f"{name} ({entity_id})"

            if sensor_options:
                # Auto-select the first sensor as default
                default_sensor = power_sensors[0] if power_sensors else None
                # Get the friendly name for the label
                device_name = device_names_list.get(device_id, device_id)

                # Use the friendly name as the key, which the UI will use as the label
                schema_fields[
                    vol.Required(device_name, default=default_sensor)
                ] = vol.In(sensor_options)

        if not schema_fields:
            return self.async_abort(reason="no_sensors_found")

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(schema_fields),
        )

    async def _get_power_devices_map(self) -> Dict[str, list[str]]:
        """
        Scan all sensor entities and return a map of devices that have
        power sensors (W or kW).

        Returns:
            A dictionary mapping device IDs to a list of their power sensor entity IDs.
        """
        power_devices = {}
        ent_reg = er.async_get(self.hass)

        for entity in ent_reg.entities.values():
            if (
                entity.domain == "sensor"
                and entity.device_id
                and entity.unit_of_measurement in ("W", "kW")
            ):
                if entity.device_id not in power_devices:
                    power_devices[entity.device_id] = []
                power_devices[entity.device_id].append(entity.entity_id)

        return power_devices

    async def _get_device_names(self, device_ids: list[str]) -> Dict[str, str]:
        """
        Get friendly names for a list of device IDs, excluding disabled ones,
        and sorted alphabetically.

        Returns:
            A sorted dictionary mapping device IDs to their friendly names.
        """
        dev_reg = dr.async_get(self.hass)
        device_names = {}
        for device_id in device_ids:
            device = dev_reg.async_get(device_id)
            if device and not device.disabled_by:
                name = device.name_by_user or device.name or f"Device {device.id}"
                manufacturer = f" ({device.manufacturer})" if device.manufacturer else ""
                device_names[device_id] = f"{name}{manufacturer}"
        
        # Sort the dictionary by device name (the value)
        return dict(sorted(device_names.items(), key=lambda item: item[1]))