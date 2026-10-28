import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.earthquake_processor import EarthquakeProcessor, calculate_distance
from modules.config import get_felt_distance, get_magnitude_color, get_alert_level


def test_calculate_distance():
    dist = calculate_distance(49.6116, 6.1319, 48.8566, 2.3522)
    assert 280 < dist < 300


def test_felt_distance_thresholds():
    assert get_felt_distance(4.5) == 5000
    assert get_felt_distance(5.5) == 10000


def test_magnitude_colors():
    assert get_magnitude_color(3.5) == "grey"
    assert get_magnitude_color(7.5) == "red"


def test_alert_levels():
    assert get_alert_level(3.0) == 0
    assert get_alert_level(8.0) == 4
