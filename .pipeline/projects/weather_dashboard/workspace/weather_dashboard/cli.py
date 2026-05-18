"""
cli.py — weather_dashboard CLI.
"""
import argparse, os, sys
from weather_dashboard.weather import fetch_weather, format_dashboard

def main():
    parser = argparse.ArgumentParser(prog="weather_dashboard")
    parser.add_argument("command", choices=["view"])
    parser.add_argument("location", help="City name or Zip code")
    
    args = parser.parse_args()

    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        print("Note: OPENWEATHER_API_KEY not set. Using offline simulated data.", file=sys.stderr)

    data = fetch_weather(args.location, api_key=api_key)
    print(format_dashboard(data))

if __name__ == "__main__":
    main()
