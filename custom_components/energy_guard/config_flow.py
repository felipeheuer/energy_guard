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
        if user_input is not None:
            # Data comes in as {'sensor_DEVICE_ID': 'sensor.entity_id'}
            # We store it as {'DEVICE_ID': 'sensor.entity_id'}
            selection_map = {
                key.replace("sensor_", ""): entity_id
                for key, entity_id in user_input.items()
            }

            return self.async_create_entry(
                title=DEFAULT_NAME, data={"selection_map": selection_map}
            )

        schema_fields = {}
        ent_reg = er.async_get(self.hass)

        device_names_list = await self._get_device_names(self.selected_devices)

        for device_id in self.selected_devices:
            power_sensors = self.power_devices_map.get(device_id, [])

            # Create a dictionary of {entity_id: friendly_name} for the dropdown
            sensor_options = {}
            for entity_id in power_sensors:
                entry = ent_reg.async_get(entity_id)
                if entry:
                    # Use original name (from integration) or name (user-customized)
                    name = entry.original_name or entry.name or entity_id
                    sensor_options[entity_id] = f"{name} ({entity_id})"

            if sensor_options:
                # Auto-select the first sensor found as the default
                default_sensor = power_sensors[0] if power_sensors else None
                device_name = device_names_list.get(device_id, device_id)

                schema_fields[
                    vol.Required(f"sensor_{device_id}", default=default_sensor)
                ] = vol.In(sensor_options)

        if not schema_fields:
            # This should ideally not be reached if the user step worked correctly
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
            Example: {"device_id_1": ["sensor.power_1"], "device_id_2": ["sensor.power_2"]}
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
        Get friendly names for a list of device IDs.

        Returns:
            A dictionary mapping device IDs to their friendly names.
            Example: {"device_id_1": "Smart Plug (TP-Link)"}
        """
        dev_reg = dr.async_get(self.hass)
        device_names = {}
        for device_id in device_ids:
            device = dev_reg.async_get(device_id)
            if device:
                name = device.name_by_user or device.name or f"Device {device.id}"
                manufacturer = f" ({device.manufacturer})" if device.manufacturer else ""
                device_names[device_id] = f"{name}{manufacturer}"
        return device_names