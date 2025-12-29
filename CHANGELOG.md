# Changelog

## 0.1.0

### Changed
- **Improved Configuration Flow:**
    - The device selection list is now automatically filtered to only show controllable devices (e.g., smart plugs, sockets) that have both a power sensor (`W` or `kW`) and a `switch` entity. This prevents non-switchable devices like lights from appearing in the list.
    - The device selection list is now sorted alphabetically.
    - Disabled devices are now hidden from the selection list.
    - In the sensor selection step, the device's friendly name is now displayed as the label for clarity.
