# Domoticz World Earthquakes Plugin

A modular Python plugin for **Domoticz** that fetches worldwide seismic activity from the [Seismic Portal API](https://www.seismicportal.eu/) and updates a native **Alert Sensor** in Domoticz based on earthquake location, magnitude, and distance to your target position.

---

## Features
- **Native Modular Python Implementation**: Clean package layout (`modules/`).
- **Geographic Distance Processing**: Calculates distance using the Haversine formula.
- **Dynamic Felt-Distance Filtering**: Categorizes earthquakes as felt vs. unnoticed according to magnitude thresholds.
- **Alert Sensor Integration**: Automatically creates and updates an Alert Sensor in Domoticz with direct links to Google Maps and Seismic Portal details.
- **Configurable Notifications**: Sends notifications via Domoticz's internal notification system.

---

## Installation

1. Extract this archive into your Domoticz `plugins` directory:
   ```bash
   tar -xzf Domoticz-WorldEarthquakes-<latest release>.tar.gz -C /srv/domoticz/plugins/
   ```
2. Restart Domoticz:
   ```bash
   sudo systemctl restart domoticz
   ```

---

## Configuration

1. In Domoticz, go to **Setup** > **Hardware**.
2. Select **World Earthquakes** from the type dropdown menu.
3. Configure your coordinates, email, and magnitude thresholds, then click **Add**.

---

## License
MIT License
