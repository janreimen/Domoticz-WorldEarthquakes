"""Earthquake Data Processing and Distance Calculations Module."""

import datetime
import math
import time
from .config import get_alert_level, get_felt_distance, get_magnitude_color


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_earth = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_earth * c


class EarthquakeProcessor:

    def __init__(self, latitude: float, longitude: float):
        self.user_lat = latitude
        self.user_lon = longitude

    def process(
        self,
        features: list,
        min_mag: float,
        max_age_min: int,
        max_radius_km: float,
    ):
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

            distance = calculate_distance(self.user_lat, self.user_lon, lat, lon)

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

        return {
            "alert_text": alert_text,
            "email_message": message,
            "alert_level": alert_level,
            "max_magnitude": max_mag_seen,
            "noticed_count": noticed_count,
            "unnoticed_count": unnoticed_count,
        }
