"""Config flow for Energy Guard integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class EnergyGuardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Energy Guard."""
    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._existing_entry = None
        self._selected_devices = []
        self._devices_to_configure = []
        self._configured_data = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Check if an instance already exists
        current_entries = self._async_current_entries()
        
        if current_entries:
            self._existing_entry = current_entries[0]
            return await self.async_step_select_devices()
        
        return await self.async_step_select_devices()

    async def async_step_select_devices(self, user_input=None):
        """Allow user to select devices."""
        errors = {}
        
        if user_input is not None:
            self._selected_devices = user_input.get("devices", [])
            if not self._selected_devices:
                return self.async_abort(reason="no_devices_selected")
            
            # Prepare list for sensor mapping
            self._devices_to_configure = list(self._selected_devices)
            
            # If editing, load existing data to preserve it
            if self._existing_entry:
                self._configured_data = dict(self._existing_entry.data.get("devices", {}))
            
            return await self.async_step_map_sensors()

        # Exclude devices already configured if possible, or just allow selection
        # Here we allow selecting anything; overwriting existing config if selected again.
        return self.async_show_form(
            step_id="select_devices",
            data_schema=vol.Schema({
                vol.Required("devices"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["switch", "input_boolean", "light"],
                        multiple=True
                    )
                ),
            }),
            errors=errors
        )

    async def async_step_map_sensors(self, user_input=None):
        """Map power sensors to the selected devices."""
        errors = {}

        # Save previous step data if available
        if user_input is not None:
            # The device being configured in the PREVIOUS iteration
            # We need to track which device we just finished. 
            # Since we pop from the list *before* showing the form, 
            # we need to handle the state carefully.
            
            # Logic: Input comes from the form for the *current_device* variable 
            # that was set in the previous call. 
            # However, standard config flow is stateless between steps unless we save state.
            
            # Alternative: Pop device at the START of the logic.
            pass

        # If input is provided, save it to the dictionary
        if user_input is not None and hasattr(self, "_current_device_id"):
            self._configured_data[self._current_device_id] = {
                "power_entity": user_input["power_sensor"],
                "switch_entity": user_input.get("switch_entity")
            }

        # Check if there are devices left to configure
        if not self._devices_to_configure:
            return self._finish_setup()

        # Get next device
        current_device = self._devices_to_configure.pop(0)
        self._current_device_id = current_device # Save for next iteration
        
        # Try to guess the power sensor
        entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)
        suggested_power = None
        
        current_ent_reg = entity_registry.async_get(current_device)
        
        if current_ent_reg and current_ent_reg.device_id:
            device_entities = [
                entry.entity_id for entry in 
                entity_registry.entities.values() 
                if entry.device_id == current_ent_reg.device_id
            ]
            
            for ent in device_entities:
                state = self.hass.states.get(ent)
                if state and (
                    state.attributes.get("device_class") == "power" or 
                    state.attributes.get("unit_of_measurement") in ["W", "kW"]
                ):
                    suggested_power = ent
                    break

        return self.async_show_form(
            step_id="map_sensors",
            description_placeholders={"device_name": current_device},
            data_schema=vol.Schema({
                vol.Required("power_sensor", default=suggested_power): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional("switch_entity", default=current_device): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch", "light"])
                )
            }),
            errors=errors
        )

    def _finish_setup(self):
        """Save configuration."""
        data = {"devices": self._configured_data}

        if self._existing_entry:
            self.hass.config_entries.async_update_entry(
                self._existing_entry, 
                data=data
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self._existing_entry.entry_id)
            )
            return self.async_abort(reason="reconfigured")
        
        return self.async_create_entry(title="Energy Guard", data=data)