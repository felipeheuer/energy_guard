"""Binary sensor platform (Logic Core)."""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event, async_call_later
from homeassistant.helpers.entity_registry import async_get as async_get_ent_reg
from homeassistant.core import callback
from homeassistant.const import STATE_ON, SERVICE_TURN_OFF
from .const import DOMAIN, ICON_ALERT, DEFAULT_POWER_LIMIT, DEFAULT_TRIP_DELAY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary sensor platform."""
    device_map = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, data in device_map.items():
        entities.append(EnergyGuardBinarySensor(hass, device_id, data))
    async_add_entities(entities)

class EnergyGuardBinarySensor(BinarySensorEntity):
    """Binary sensor representing the alert state and handling core logic."""

    _attr_has_entity_name = True
    _attr_name = "Guard: Alert Status"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, hass, device_id, data):
        self.hass = hass
        self._device_id = device_id
        self._data = data
        self._source_entity = data["power_entity"]
        self._cutoff_switch_physical = data["switch_entity"]
        
        self._attr_unique_id = f"{device_id}_alert"
        self._attr_is_on = False
        
        # Internal state variables
        self._timer_remove = None
        
        # Control Entity IDs
        self._ent_limit = None
        self._ent_delay = None
        self._ent_monitor = None
        self._ent_cutoff_config = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers=self._data["identifiers"],
        )

    @property
    def icon(self):
        return ICON_ALERT if self.is_on else "mdi:shield-check"

    async def async_added_to_hass(self) -> None:
        """Initialize and link to config entities."""
        ent_reg = async_get_ent_reg(self.hass)
        
        # Helper to resolve entity IDs
        def resolve_entity(key, domain):
            return ent_reg.async_get_entity_id(
                domain, DOMAIN, f"{self._device_id}_{key}"
            )

        self._ent_limit = resolve_entity("power_limit", "number")
        self._ent_delay = resolve_entity("trip_delay", "number")
        self._ent_monitor = resolve_entity("monitor_enabled", "switch")
        self._ent_cutoff_config = resolve_entity("safety_cutoff", "switch")

        # Build a list of entities to watch
        # We trigger logic if Power changes OR if Settings change
        watch_list = [self._source_entity]
        
        if self._ent_limit:
            watch_list.append(self._ent_limit)
        if self._ent_monitor:
            watch_list.append(self._ent_monitor)
            
        # Start monitoring all inputs
        self.async_on_remove(
            async_track_state_change_event(self.hass, watch_list, self._update_logic)
        )

    @callback
    def _update_logic(self, event=None):
        """Main logic loop triggered by ANY state change (Power or Config)."""
        
        # 1. Check if Master Monitor is enabled
        if self._ent_monitor:
            state = self.hass.states.get(self._ent_monitor)
            if state and state.state != STATE_ON:
                self._cancel_timer()
                if self._attr_is_on:
                    self._attr_is_on = False
                    self.async_write_ha_state()
                return

        # 2. Get Current Power (Always fetch fresh state, ignore event data)
        power_state = self.hass.states.get(self._source_entity)
        if not power_state or power_state.state in ("unknown", "unavailable"):
            return

        try:
            # String cleanup
            raw = power_state.state.replace(',', '.').strip()
            clean = ''.join(c for c in raw if c.isdigit() or c == '.')
            current_power = float(clean)
            
            # kW to W conversion
            unit = (power_state.attributes.get("unit_of_measurement") or "").lower()
            if unit in ["kw", "kilowatt"]:
                current_power *= 1000.0
        except ValueError:
            return

        # 3. Read Configured Limit (Slider)
        limit = DEFAULT_POWER_LIMIT # Fallback if entity not ready
        if self._ent_limit:
            st = self.hass.states.get(self._ent_limit)
            if st and st.state not in ("unknown", "unavailable"):
                try:
                    limit = float(st.state)
                except ValueError: pass

        # 4. Comparison Logic
        if current_power > limit:
            # --- OVERLOAD DETECTED ---
            if self._attr_is_on:
                return # Already tripped, do nothing
            
            if self._timer_remove is None:
                # Start Tolerance Timer (Delay)
                delay = DEFAULT_TRIP_DELAY # Fallback if entity not ready
                if self._ent_delay:
                    st = self.hass.states.get(self._ent_delay)
                    if st and st.state not in ("unknown", "unavailable"):
                        try:
                            delay = float(st.state)
                        except ValueError: pass
                
                _LOGGER.debug(f"EnergyGuard: Overload ({current_power}W > {limit}W). Waiting {delay}s...")
                self._timer_remove = async_call_later(self.hass, delay, self._trip_alarm)
        else:
            # --- NORMAL CONDITION ---
            self._cancel_timer()
            if self._attr_is_on:
                _LOGGER.debug(f"EnergyGuard: Power normalized ({current_power}W). Resetting alert.")
                self._attr_is_on = False
                self.async_write_ha_state()

    def _cancel_timer(self):
        """Cancel the wait timer if power drops."""
        if self._timer_remove:
            self._timer_remove()
            self._timer_remove = None

    async def _trip_alarm(self, _now):
        """Tolerance time over: Trip Alarm!"""
        self._timer_remove = None
        self._attr_is_on = True
        self.async_write_ha_state()
        
        _LOGGER.warning(f"Energy Guard TRIPPED on device {self._device_id}!")
        
        # 1. Increment Counter
        self.hass.bus.async_fire(f"energy_guard_increment_{self._device_id}")
        
        # 2. Fire event
        self.hass.bus.async_fire("energy_guard_tripped", {
            "device_id": self._device_id,
            "entity_id": self.entity_id,
            "source": self._source_entity
        })

        # 3. Safety Cutoff
        if self._ent_cutoff_config and self._cutoff_switch_physical:
            st = self.hass.states.get(self._ent_cutoff_config)
            if st and st.state == STATE_ON:
                _LOGGER.warning(f"Energy Guard: Executing Safety Cutoff on {self._cutoff_switch_physical}")
                await self.hass.services.async_call(
                    "switch", "turn_off", {"entity_id": self._cutoff_switch_physical}
                )