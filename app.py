#!/usr/bin/env python3
"""
Simple Flask app to display real-time PATH train departures for Grove Street (GRV) station.
"""

import requests
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
import time
import math

app = Flask(__name__)

# API endpoints
PATH_API_URL = "https://www.panynj.gov/bin/portauthority/ridepath.json"

# Grove Street coordinates (for weather/sunrise/sunset)
GROVE_STREET_LAT = 40.7197
GROVE_STREET_LON = -74.0431

def fetch_path_data():
    """Fetch real-time PATH data from the API"""
    try:
        response = requests.get(PATH_API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching PATH data: {e}")
        return None

def get_grove_street_departures():
    """Extract Grove Street (GRV) departure information"""
    data = fetch_path_data()
    if not data or 'results' not in data:
        return None
    
    # Find Grove Street station data
    for station in data['results']:
        if station.get('consideredStation') == 'GRV':
            departures = []
            
            for destination in station.get('destinations', []):
                label = destination.get('label', '')
                direction = "To New York" if label == "ToNY" else "To New Jersey"
                
                for message in destination.get('messages', []):
                    departure = {
                        'direction': direction,
                        'destination': message.get('headSign', ''),
                        'arrival_time': message.get('arrivalTimeMessage', ''),
                        'seconds_to_arrival': message.get('secondsToArrival', 0),
                        'line_color': message.get('lineColor', ''),
                        'last_updated': message.get('lastUpdated', ''),
                        'target': message.get('target', '')
                    }
                    departures.append(departure)
            
            # Sort by seconds to arrival
            departures.sort(key=lambda x: int(x['seconds_to_arrival']) if str(x['seconds_to_arrival']).isdigit() else 9999)
            return departures
    
    return None

def calculate_sunrise_sunset():
    """Calculate sunrise and sunset times for Grove Street location"""
    try:
        from datetime import date
        
        # Simple sunrise/sunset calculation (approximate)
        # For more accuracy, you could use the 'astral' library
        now = datetime.now()
        day_of_year = now.timetuple().tm_yday
        
        # Simplified calculation for NYC area
        # This is approximate - for exact times you'd use astronomical calculations
        latitude_rad = math.radians(GROVE_STREET_LAT)
        
        # Solar declination approximation
        solar_decl = math.radians(23.45) * math.sin(math.radians(360 * (284 + day_of_year) / 365))
        
        # Hour angle calculation
        hour_angle = math.acos(-math.tan(latitude_rad) * math.tan(solar_decl))
        
        # Convert to hours (local approximation). Account for timezone offset roughly (+1) and wrap to 24h.
        sunrise_hour = 12 - (hour_angle * 12 / math.pi) - (GROVE_STREET_LON / 15) + 1
        sunset_hour = 12 + (hour_angle * 12 / math.pi) - (GROVE_STREET_LON / 15) + 1

        def format_hour_to_hhmm(hour_float: float) -> str:
            total_minutes = int(round(hour_float * 60)) % (24 * 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours:02d}:{minutes:02d}"

        # Convert to time strings with proper wrapping
        sunrise_time = format_hour_to_hhmm(sunrise_hour)
        sunset_time = format_hour_to_hhmm(sunset_hour)
        
        return sunrise_time, sunset_time
    except Exception as e:
        print(f"Error calculating sunrise/sunset: {e}")
        return "6:30", "18:30"  # Fallback times

def get_weather_data():
    """Get weather for Jersey City (near Grove St) and Manhattan in Celsius."""
    try:
        # Locations: Jersey City (Grove St) and Midtown Manhattan (approx Bryant Park)
        locations = {
            'jersey_city': { 'name': 'Jersey City', 'lat': 40.7197, 'lon': -74.0431 },
            'manhattan': { 'name': 'Manhattan', 'lat': 40.7549, 'lon': -73.9840 },
        }

        weather_icons = {
            0: '☀️',
            1: '🌤️',
            2: '⛅',
            3: '☁️',
            45: '🌫️',
            48: '🌫️',
            51: '🌦️',
            53: '🌧️',
            55: '🌧️',
            61: '🌧️',
            63: '🌧️',
            65: '⛈️',
            71: '🌨️',
            73: '🌨️',
            75: '❄️',
            95: '⛈️',
        }

        results = {}
        sunrise_time = None
        sunset_time = None
        for key, loc in locations.items():
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}"
                f"&current_weather=true&daily=sunrise,sunset&forecast_days=1&timezone=America/New_York"
            )
            response = requests.get(weather_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            current = data.get('current_weather', {})
            temp_c = round(current.get('temperature', 0))
            weather_code = current.get('weathercode', 0)
            icon = weather_icons.get(weather_code, '🌤️')

            results[key] = {
                'name': loc['name'],
                'temperature_c': f"{temp_c}°C",
                'icon': icon,
            }

            # Capture sunrise/sunset once from the first successful response
            if sunrise_time is None and 'daily' in data:
                daily = data.get('daily', {})
                sunrise_list = daily.get('sunrise', [])
                sunset_list = daily.get('sunset', [])
                if sunrise_list and sunset_list:
                    try:
                        sunrise_iso = sunrise_list[0]
                        sunset_iso = sunset_list[0]
                        # Times are already in America/New_York per API parameter
                        sunrise_dt = datetime.fromisoformat(sunrise_iso)
                        sunset_dt = datetime.fromisoformat(sunset_iso)
                        sunrise_time = sunrise_dt.strftime('%H:%M')
                        sunset_time = sunset_dt.strftime('%H:%M')
                    except Exception:
                        sunrise_time, sunset_time = calculate_sunrise_sunset()

        # Fallback if API daily times were not available
        if sunrise_time is None or sunset_time is None:
            sunrise_time, sunset_time = calculate_sunrise_sunset()

        return {
            'jersey_city': results.get('jersey_city', {}),
            'manhattan': results.get('manhattan', {}),
            'sunrise': sunrise_time,
            'sunset': sunset_time
        }

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        sunrise, sunset = calculate_sunrise_sunset()
        return {
            'jersey_city': {'name': 'Jersey City', 'temperature_c': 'N/A', 'icon': '🌤️'},
            'manhattan': {'name': 'Manhattan', 'temperature_c': 'N/A', 'icon': '🌤️'},
            'sunrise': sunrise,
            'sunset': sunset
        }

@app.route('/')
def index():
    """Main page displaying departure times"""
    return render_template('index.html')

@app.route('/api/departures')
def api_departures():
    """API endpoint to get current departure data"""
    departures = get_grove_street_departures()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        'departures': departures,
        'last_fetch': current_time,
        'station': 'Grove Street (GRV)'
    })

@app.route('/api/weather')
def api_weather():
    """API endpoint to get weather data"""
    weather_data = get_weather_data()
    return jsonify(weather_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
