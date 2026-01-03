# Changelog

## [0.2.1] - 2026-01-03

### Fixed
- Fixed Tasmota Device Linking: Corrected an issue where Energy Guard entities (Power Limit, Trip Delay) were not appearing under Tasmota devices due to incorrect device linking. All entities should now correctly associate with their respective parent devices.

## [0.2.0] - 2026-01-03

### Changed
- **Architectural Rework:** The integration now runs as a single instance. New devices are added by running the "Add Integration" flow again, which intelligently finds and adds new devices to the existing setup.
- **Improved Configuration Flow:** The device selection list now excludes already configured devices.
- **Type changed to "Service":** The integration is now correctly classified as a "service" in Home Assistant.

### Fixed
- Resolved multiple bugs that caused the configuration flow to crash or show confusing dialogs.
- Fixed a critical bug that created new, duplicate "Energy Guard" devices instead of attaching entities to the original device.

## 0.1.0

### Changed
- **Improved Configuration Flow:**
    - The device selection list is now automatically filtered to only show controllable devices (e.g., smart plugs, sockets) that have both a power sensor (`W` or `kW`) and a `switch` entity. This prevents non-switchable devices like lights from appearing in the list.
    - The device selection list is now sorted alphabetically.
    - Disabled devices are now hidden from the selection list.
    - In the sensor selection step, the device's friendly name is now displayed as the label for clarity.
