"""tests for weather_dashboard."""
from weather_dashboard.weather import _generate_mock_weather, fetch_weather, format_dashboard

def test_generate_mock_weather():
    data = _generate_mock_weather("Austin,TX")
    assert data["location"] == "Austin,TX"
    assert "temp_f" in data["current"]
    assert len(data["forecast"]) == 6

def test_fetch_weather_no_key():
    data = fetch_weather("Seattle,WA")
    assert data["metadata"]["source"] == "mocked"

def test_format_dashboard():
    data = _generate_mock_weather("New York,NY")
    # inject a fake alert for coverage
    data["current"]["alert"] = "Tornado Warning"
    board = format_dashboard(data)
    assert "WEATHER DASHBOARD: NEW YORK,NY" in board
    assert "SEVERE WEATHER ALERT" in board
    assert "Tornado Warning" in board
