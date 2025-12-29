# 🛡️ Energy Guard (Beta)

**Energy Guard** is a custom integration for Home Assistant that acts as a **Virtual Circuit Breaker**. It monitors the power usage (W) of your smart plugs and switches, triggering alerts or cutting off power when a user-defined limit is exceeded.

> ⚠️ **BETA WARNING**: This integration is currently in **BETA**. Features may change, and bugs may be present. Please report any issues on the GitHub Issues page.

---

## 🚨 Important Safety Disclaimer

**READ BEFORE USING:**
This integration is a **software-based monitoring tool**. It relies on Home Assistant, your network connection, and the reporting frequency of your devices (Tasmota, Tuya, Zigbee, etc.).

* **DO NOT** rely on Energy Guard as a replacement for physical safety devices like circuit breakers, fuses, or GFCI outlets.
* **DO NOT** use this integration to protect against short circuits or immediate electrical faults.
* **ALWAYS** ensure your appliances and wiring are rated for the load they are carrying.
* **Latency exists:** Network delays or Home Assistant restarts may prevent the "Safety Cutoff" from activating instantly.

---

## ✨ Features

* **Focused Compatibility:** Works with any controllable device (e.g., smart plugs, sockets) that has both a **Power sensor** (in `W` or `kW`) and a **`switch` entity**. This ensures that only devices that can be physically turned off by the integration are listed.
* **2-Step Configuration:** Easily select your devices and map the correct power sensor via the UI.
* **Smart Normalization:** Automatically handles sensors reporting in `W` or `kW`.
* **Configurable Limits:**
    * **Power Limit (W):** Set the threshold for the alert.
    * **Trip Delay (s):** Set a tolerance time to avoid false alarms from short spikes (inrush current).
* **Safety Cutoff:** Optionally turn off the physical switch when an overload is detected.
* **Auto-Reset:** The alert clears automatically when power returns to safe levels.
* **Persistent Settings:** Limits and settings are saved and restored after Home Assistant restarts.
* **Statistics:** Tracks "Max Peak Recorded" and "Trip Counts".

---

## 📦 Installation

### Manual Installation
1.  Download the `energy_guard` folder from this repository.
2.  Copy the folder into your Home Assistant's `custom_components` directory:
    ```
    /config/custom_components/energy_guard
    ```
3.  Restart Home Assistant.

---

## ⚙️ Configuration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for **"Energy Guard"**.
3.  **Step 1:** Select the devices you want to protect from the list.
4.  **Step 2:** For each selected device, choose the specific **Power Sensor** (e.g., `sensor.tasmota_energy_power`) from the dropdown menu.
5.  Click **Submit**.

---

## 🎛️ Usage

Once configured, Energy Guard creates specific entities for each device, grouped under the device page:

### Configuration (Sliders & Switches)
* **Guard: Power Limit (W):** Set the maximum allowed wattage (Step: 1W).
* **Guard: Trip Delay (s):** How long the power must stay above the limit before triggering (Default: 3s).
* **Guard: Monitor Enabled:** Master switch to enable/disable the logic for this device.
* **Guard: Safety Cutoff:** If enabled, Energy Guard will physically turn off the device switch when tripped.
* **Guard: Reset Stats:** A button to reset the Peak and Count statistics.

### Diagnostics (Sensors)
* **Guard: Alert Status:** A binary sensor that turns `On` (Problem) when overloaded.
* **Guard: Max Peak:** Records the highest wattage ever seen.
* **Guard: Trip Count:** Counts how many times the limit was exceeded.

---

## 🚀 Roadmap & Planned Features

We are constantly working to improve Energy Guard. Here are the features planned for future releases (V2+):

* **📉 Low Limit / Under-load Monitor:**
    * Trigger alerts when power drops *below* a certain threshold.
    * *Use Cases:* Detect when a washing machine finishes its cycle or if a freezer/fridge compressor fails to start.
* **⚠️ Soft Limit (Warning Threshold):**
    * A secondary slider to trigger a "Warning" notification before the actual Cutoff limit is reached (e.g., warn at 90% load).
* **🌍 Internationalization (Translations):**
    * Native language support for the configuration UI (starting with Portuguese-BR).
* **🎨 Dynamic Icons:**
    * Entity icons that change color/shape based on load percentage (Green/Yellow/Red).
* **🤖 Automation Blueprints:**
    * Pre-made blueprints to easily set up notifications to your phone when Energy Guard trips.
* **🔧 Repair Flow:**
    * Ability to re-select a sensor if the entity ID changes, without reinstalling the integration.

---

## 🛠️ Troubleshooting

* **Tasmota Devices:** Ensure your Tasmota device is discovered by Home Assistant (SetOption19 0 recommended). The integration looks for sensors with `device_class: power` or unit `W`/`kW`.
* **Values Resetting?** Ensure you are running the latest version. Settings are stored using `RestoreEntity`.

---

## 📄 License

[MIT License](LICENSE)