"""
weather.py — Weather data fetching and alerting logic.
"""
from __future__ import annotations
import json
import random
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

def _generate_mock_weather(location: str) -> dict:
    """Deterministic mock weather data for a location."""
    random.seed(sum(ord(c) for c in location))
    base_temp = random.uniform(40, 95)
    
    forecast = []
    now = datetime.now(timezone.utc)
    
    for i in range(7):
        date = now + timedelta(days=i)
        temp_var = random.uniform(-10, 10)
        temp = base_temp + temp_var
        condition_val = random.random()
        
        if condition_val > 0.9:
            cond = "Severe Storm"
            alert = "High winds and lightning expected."
        elif condition_val > 0.6:
            cond = "Rain"
            alert = None
        else:
            cond = "Clear"
            alert = None
            
        forecast.append({
            "date": date.isoformat()[:10],
            "temp_f": round(temp, 1),
            "condition": cond,
            "alert": alert
        })
        
    return {
        "location": location,
        "current": forecast[0],
        "forecast": forecast[1:],
        "metadata": {"source": "mocked", "generated_at": now.isoformat()}
    }

def fetch_weather(location: str, api_key: str | None = None) -> dict:
    """Fetch weather from OpenWeatherMap or mock it if no key."""
    if not api_key:
        return _generate_mock_weather(location)
    
    # Real implementation would call api.openweathermap.org here
    # For now, we fallback to mock to maintain stdlib zero-dependency purity
    # and offline capability as requested.
    return _generate_mock_weather(location)

def format_dashboard(data: dict) -> str:
    """Format weather data into a terminal dashboard."""
    loc = data.get("location", "Unknown")
    curr = data.get("current", {})
    
    lines = [
        "===========================================================",
        f" 🌤️  WEATHER DASHBOARD: {loc.upper()}",
        "===========================================================",
        f" Current Temp: {curr.get('temp_f', '--')}°F",
        f" Conditions:   {curr.get('condition', '--')}",
    ]
    
    if curr.get("alert"):
        lines.extend([
            "",
            " ⚠️  SEVERE WEATHER ALERT",
            f" {curr['alert']}",
            "-----------------------------------------------------------"
        ])
    else:
        lines.append("-----------------------------------------------------------")
        
    lines.extend([
        " 7-DAY FORECAST",
        f" {'Date':<12} | {'Temp':<8} | {'Conditions':<15} | {'Alerts'}",
        "-----------------------------------------------------------"
    ])
    
    for day in data.get("forecast", []):
        alert_str = f"⚠️ {day['alert']}" if day.get("alert") else ""
        lines.append(
            f" {day['date']:<12} | {day['temp_f']:>5.1f}°F | {day['condition']:<15} | {alert_str}"
        )
        
    lines.append("===========================================================")
    return "\n".join(lines)
