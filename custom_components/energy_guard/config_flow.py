"""Config flow for Energy Guard."""
import logging
from typing import Any, Dict, Set

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICES, Platform, UnitOfPower
from homeassistant.helpers import device_registry as dr, entity_registry as er
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_POWER_LIMIT,
    DEFAULT_TRIP_DELAY,
    DEFAULT_SAFETY_CUTOFF,
)


_LOGGER = logging.getLogger(__name__)


class EnergyGuardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Energy Guard."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.selected_devices: list[str] = []
        self.sensor_map: Dict[str, str] = {}
        self.power_devices_map: Dict[str, list[str]] = {}

    async def async_step_user(self, user_input: Dict[str, Any] | None = None):
        """Handle the initial step where the user selects devices."""
        if user_input is not None:
            self.selected_devices = user_input[CONF_DEVICES]
            return await self.async_step_sensors()

        self.power_devices_map = await self._get_power_devices_map()

        if not self.power_devices_map:
            return self.async_abort(reason="no_power_devices_found")

        device_names = await self._get_device_names(list(self.power_devices_map.keys()))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_DEVICES): cv.multi_select(device_names)}),
            last_step=False,
        )

    async def async_step_sensors(self, user_input: Dict[str, Any] | None = None):
        """For each selected device, ask the user to confirm the power sensor."""
        if user_input is not None:
            ent_reg = er.async_get(self.hass)
            for entity_id in user_input.values():
                entry = ent_reg.async_get(entity_id)
                if entry and entry.device_id:
                    self.sensor_map[entry.device_id] = entity_id
            return await self.async_step_options()

        schema_fields = {}
        device_names_list = await self._get_device_names(self.selected_devices)

        for device_id in self.selected_devices:
            power_sensors = self.power_devices_map.get(device_id, [])
            sensor_options = self._get_sensor_options(power_sensors)

            if sensor_options:
                default_sensor = power_sensors[0] if power_sensors else None
                device_name = device_names_list.get(device_id, device_id)
                schema_fields[vol.Required(device_name, default=default_sensor)] = vol.In(
                    sensor_options
                )

        if not schema_fields:
            return self.async_abort(reason="no_sensors_found")

        return self.async_show_form(
            step_id="sensors", data_schema=vol.Schema(schema_fields), last_step=False
        )

    async def async_step_options(self, user_input: Dict[str, Any] | None = None):
        """Ask the user to configure device-specific options."""
        if user_input is not None:
            final_devices = {}
            for device_id, sensor_entity in self.sensor_map.items():
                final_devices[device_id] = {
                    "power_sensor": sensor_entity,
                    "peak_power": user_input[f"peak_power_{device_id}"],
                    "trip_delay": user_input[f"trip_delay_{device_id}"],
                    "safety_cutoff_enabled": user_input[f"safety_cutoff_{device_id}"],
                }

            return self.async_create_entry(
                title=DEFAULT_NAME, data={CONF_DEVICES: final_devices}
            )

        schema_fields = {}
        device_names_list = await self._get_device_names(self.selected_devices)

        for device_id in self.selected_devices:
            device_name = device_names_list.get(device_id, device_id)
            # Add a visual separator/marker for each device
            schema_fields[vol.Marker(device_name)] = str

            # Add fields for this device
            schema_fields[
                vol.Required(
                    f"peak_power_{device_id}", default=DEFAULT_POWER_LIMIT
                )
            ] = vol.All(vol.Coerce(int), vol.Range(min=1))
            schema_fields[
                vol.Required(
                    f"trip_delay_{device_id}", default=DEFAULT_TRIP_DELAY
                )
            ] = vol.All(vol.Coerce(int), vol.Range(min=0))
            schema_fields[
                vol.Required(
                    f"safety_cutoff_{device_id}",
                    default=DEFAULT_SAFETY_CUTOFF,
                )
            ] = cv.boolean

        return self.async_show_form(
            step_id="options", data_schema=vol.Schema(schema_fields)
        )

    def _get_sensor_options(self, power_sensors: list[str]) -> Dict[str, str]:
        """Create a dictionary of {entity_id: friendly_name} for a dropdown."""
        ent_reg = er.async_get(self.hass)
        sensor_options = {}
        for entity_id in power_sensors:
            entry = ent_reg.async_get(entity_id)
            if entry:
                name = entry.original_name or entry.name or entity_id
                sensor_options[entity_id] = f"{name} ({entity_id})"
        return sensor_options

    async def _get_switch_device_ids(self) -> Set[str]:
        """Returns a set of device IDs that have at least one switch entity."""
        switch_devices = set()
        ent_reg = er.async_get(self.hass)
        for entity in ent_reg.entities.values():
            if entity.domain == Platform.SWITCH and entity.device_id:
                switch_devices.add(entity.device_id)
        return switch_devices

    async def _get_power_devices_map(self) -> Dict[str, list[str]]:
        """
        Scan all sensor entities and return a map of devices that have
        both power sensors (W or kW) AND a switch entity.
        """
        power_devices = {}
        ent_reg = er.async_get(self.hass)
        switch_devices_set = await self._get_switch_device_ids()

        for entity in ent_reg.entities.values():
            if (
                entity.domain == Platform.SENSOR
                and entity.device_id
                and entity.unit_of_measurement in (UnitOfPower.WATT, UnitOfPower.KILO_WATT)
                and entity.device_id in switch_devices_set
            ):
                if entity.device_id not in power_devices:
                    power_devices[entity.device_id] = []
                power_devices[entity.device_id].append(entity.entity_id)

        return power_devices

    async def _get_device_names(self, device_ids: list[str]) -> Dict[str, str]:
        """
        Get friendly names for a list of device IDs, excluding disabled ones,
        and sorted alphabetically.
        """
        dev_reg = dr.async_get(self.hass)
        device_names = {}
        for device_id in device_ids:
            device = dev_reg.async_get(device_id)
            if device and not device.disabled_by:
                name = device.name_by_user or device.name or f"Device {device.id}"
                manufacturer = f" ({device.manufacturer})" if device.manufacturer else ""
                device_names[device_id] = f"{name}{manufacturer}"

        return dict(sorted(device_names.items(), key=lambda item: item[1]))