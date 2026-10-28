"""
<plugin key="Domoticz-WorldEarthquakes" name="World Earthquakes" author="Jan Reimen" version="0.1.1">
    <description>
        <h2>Earthquake Alerting Tool</h2><br/>
        Fill in Latitude, Longitude, E-Mail to contact of Earthquakes, Min Magnitude to alert, Max Age of the Earthquake to consider, Radius to look in
    </description>
    <params>
        <param field="Latitude" label="Latitude" width="100" required="true" default="49.711975"/>
        <param field="Longitude" label="Longitude" width="100" required="true" default="6.253245"/>
        <param field="Email" label="Notification Email" width="200" required="false" default="jan.reimen@pt.lu"/>
        <param field="MinMagnitude" label="Min Magnitude" width="50" required="true" default="5"/>
        <param field="MaxAgeMinutes" label="Max Age (Minutes)" width="50" required="true" default="121"/>
        <param field="Radius" label="Max Radius (km)" width="100" required="true" default="960000"/>
        <param field="Mode1" label="Debug" width="75">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""

import datetime
import json
import math
import time
import urllib.request
import os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import Domoticz  # noqa: E402  (provided by Domoticz)


ALERT_LEVEL_GREY = 0
ALERT_LEVEL_GREEN = 1
ALERT_LEVEL_YELLOW = 2
ALERT_LEVEL_ORANGE = 3
ALERT_LEVEL_RED = 4

FELT_DISTANCE_THRESHOLDS = [
    (5.0, 5000),
    (6.0, 10000),
    (7.0, 15000),
    (8.0, 20000),
    (9.0, 50000),
]

MAGNITUDE_COLORS = [
    (4.0, "grey"),
    (5.0, "blue"),
    (6.0, "green"),
    (7.0, "orange"),
    (8.0, "red"),
    (9.0, "purple"),
]


def get_felt_distance(magnitude: float) -> int:
    for threshold_mag, distance in FELT_DISTANCE_THRESHOLDS:
        if magnitude < threshold_mag:
            return distance
    return 50000


def get_magnitude_color(magnitude: float) -> str:
    for threshold_mag, color in MAGNITUDE_COLORS:
        if magnitude < threshold_mag:
            return color
    return "purple"


def get_alert_level(max_magnitude: float) -> int:
    if max_magnitude >= 7.5:
        return ALERT_LEVEL_RED
    if max_magnitude >= 6.7:
        return ALERT_LEVEL_ORANGE
    if max_magnitude >= 5.5:
        return ALERT_LEVEL_YELLOW
    if max_magnitude >= 4.0:
        return ALERT_LEVEL_GREEN
    return ALERT_LEVEL_GREY


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_earth = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_earth * c


class BasePlugin:

    def __init__(self):
        self.processor = None

    def onStart(self):
        try:
            if Parameters["Mode1"] == "Debug":
                Domoticz.Debugging(1)

            Domoticz.Log("World Earthquakes Plugin started.")

            if 1 not in Devices:
                Domoticz.Device(
                    Name="World Earthquake Alert",
                    Unit=1,
                    TypeName="Alert",
                    Description="World Earthquake Monitoring Device",
                ).Create()
                Domoticz.Log("Created World Earthquake Alert Sensor device.")

            Domoticz.Heartbeat(60)
        except Exception as e:
            Domoticz.Error(f"Error in onStart: {str(e)}")

    def onTimer(self):
        now = datetime.datetime.now()
        if now.minute == 27 and (now.hour % 2 == 0):
            Domoticz.Log("Timer triggered: Fetching earthquake data...")
            self.fetch_earthquakes()

    def fetch_earthquakes(self):
        try:
            lat = Parameters["Latitude"]
            lon = Parameters["Longitude"]
            url = f"https://www.seismicportal.eu/fdsnws/event/1/query?limit=1000&lat={lat}&lon={lon}&minradius=0.01&maxradius=180&format=json"

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Domoticz-WorldEarthquakesPlugin/0.1.7"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    self.process_response(data)
                else:
                    Domoticz.Error(f"Failed to fetch seismic data. HTTP Status: {response.status}")
        except Exception as e:
            Domoticz.Error(f"Error fetching seismic data: {str(e)}")

    def process_response(self, data: dict):
        user_lat = float(Parameters["Latitude"])
        user_lon = float(Parameters["Longitude"])
        min_mag = float(Parameters["MinMagnitude"])
        max_age_min = int(Parameters["MaxAgeMinutes"])
        max_radius_km = float(Parameters["Radius"])

        features = data.get("features", [])
        alert_text = ""
        message = ""
        current_time = time.time()
        max_mag_seen = 0.0
        unnoticed_count = 0
        unnoticed_details = ""
        noticed_count = 0
        has_felt_events = False

        for event in features:
            props = event.get("properties", {})
            mag = props.get("mag")
            if mag is None or float(mag) < min_mag:
                continue

            magnitude = float(mag)
            region_raw = str(props.get("flynn_region", ""))
            region = " ".join(word.capitalize() for word in region_raw.lower().split())
            time_str = props.get("time", "")
            lat = float(props.get("lat", 0))
            lon = float(props.get("lon", 0))
            depth = float(props.get("depth", 0))
            unid = props.get("unid", "")

            distance = calculate_distance(user_lat, user_lon, lat, lon)

            try:
                dt = datetime.datetime.strptime(time_str[:19], "%Y-%m-%dT%H:%M:%S")
                timestamp = int(dt.timestamp())
            except ValueError:
                timestamp = int(current_time)

            timediff_offset = 3600
            event_age_minutes = (current_time - timestamp - timediff_offset) / 60

            if event_age_minutes > max_age_min or distance > max_radius_km:
                continue

            felt_dist = get_felt_distance(magnitude)
            is_felt = distance <= felt_dist

            if not is_felt:
                if magnitude > max_mag_seen:
                    max_mag_seen = magnitude
                unnoticed_count += 1
                unnoticed_details += (
                    f"{timestamp} : Unnoticed Earthquake in {region} ({lat}/{lon} ="
                    f" {distance:.1f} km away) with magnitude: {magnitude}<br>"
                )
                continue

            has_felt_events = True
            if magnitude > max_mag_seen:
                max_mag_seen = magnitude
            noticed_count += 1

            color = get_magnitude_color(magnitude)
            date_formatted = datetime.datetime.fromtimestamp(timestamp).strftime(
                "%d-%m-%Y %H:%M"
            )

            event_html = (
                f'<span style="color: {color}">🎯 Distance: {distance:.1f} km<br>'
                f"Magnitude: {magnitude:.1f}<br>Depth: {depth:.1f} km<br>Location: "
                f"{region}<br>UTC Time: {date_formatted}<br>"
                f'<a href="https://maps.google.com/?q={lat:.6f},{lon:.6f}" style="color: RED;">Google Maps</a><br>'
                f'<a href="https://www.seismicportal.eu/eventdetails.html?unid={unid}" style="color: BLUE;">Seismic Portal</a></span>'
            )

            alert_text += event_html + "<br>------<br>"
            message += event_html + "<br>------<br>"

        if not has_felt_events:
            alert_text += f"Unnoticed Earthquakes: {unnoticed_count}<br>"
            message += f"Unnoticed Earthquakes: {unnoticed_count}<br>"
        elif unnoticed_count > 0:
            alert_text += f".. and {unnoticed_count} Unnoticed Earthquakes<br>"
            message += (
                f".. and {unnoticed_count} Unnoticed Earthquakes :<br>"
                f" {unnoticed_details}"
            )

        alert_level = get_alert_level(max_mag_seen)

        prev_text = Devices[1].sValue if 1 in Devices else ""

        if alert_text != prev_text and 1 in Devices:
            Devices[1].UpdateAlertSensor(alert_level, alert_text)
            Domoticz.Log("Updated Earthquake Alert Sensor.")

        mailto = Parameters["Email"]
        if message != "" and mailto:
            if noticedCount > 0 or (
                unnoticed_count > 0 and max_mag_seen >= 5.0
            ):
                subject = f"[RPI4 Office World Earthquake Alert] (Mag {max_mag_seen})"
                Domoticz.SendNotification(subject, message)
                Domoticz.Log("Sent earthquake notification alert.")


global _plugin
_plugin = BasePlugin()


def onStart():
    _plugin.onStart()


def onStop():
    _plugin.onStop() if hasattr(_plugin, 'onStop') else None


def onConnect(Connection, Status, Description):
    pass


def onMessage(Connection, Data):
    pass


def onCommand(Unit, Command, Level, Color):
    pass


def onNotification(Data):
    pass


def onDisconnect(Connection):
    pass


def onTimer():
    _plugin.onTimer()
