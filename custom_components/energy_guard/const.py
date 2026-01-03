"""Constants for Energy Guard."""
from homeassistant.const import Platform

DOMAIN = "energy_guard"
DEFAULT_NAME = "Energy Guard"

PLATFORMS = [
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.BUTTON,
]

CONF_MONITORED_DEVICES = "monitored_devices"

# Default values for config flow options
DEFAULT_POWER_LIMIT = 2000  # Watts
DEFAULT_TRIP_DELAY = 3  # Seconds
DEFAULT_SAFETY_CUTOFF = False

ICON_GUARD_ON = "mdi:shield-check"
ICON_GUARD_OFF = "mdi:shield-off"
ICON_ALERT = "mdi:alert-circle"