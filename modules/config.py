"""Configuration constants and helper calculations for World Earthquakes plugin."""

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
