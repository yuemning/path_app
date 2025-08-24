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
        
        # Convert to hours
        sunrise_hour = 12 - (hour_angle * 12 / math.pi) - (GROVE_STREET_LON / 15) + 1  # +1 for timezone adjustment
        sunset_hour = 12 + (hour_angle * 12 / math.pi) - (GROVE_STREET_LON / 15) + 1
        
        # Convert to time strings
        sunrise_time = f"{int(sunrise_hour):02d}:{int((sunrise_hour % 1) * 60):02d}"
        sunset_time = f"{int(sunset_hour):02d}:{int((sunset_hour % 1) * 60):02d}"
        
        return sunrise_time, sunset_time
    except Exception as e:
        print(f"Error calculating sunrise/sunset: {e}")
        return "6:30", "18:30"  # Fallback times

def get_weather_data():
    """Get weather data - using a simple weather service"""
    try:
        # Using a free weather API (OpenWeatherMap alternative)
        # For production, you'd want to add an API key
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={GROVE_STREET_LAT}&longitude={GROVE_STREET_LON}&current_weather=true&timezone=America/New_York"
        
        response = requests.get(weather_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get('current_weather', {})
        temp_c = current.get('temperature', 0)
        temp_f = round(temp_c * 9/5 + 32)
        weather_code = current.get('weathercode', 0)
        
        # Simple weather icon mapping
        weather_icons = {
            0: '☀️',  # Clear sky
            1: '🌤️',  # Mainly clear
            2: '⛅',   # Partly cloudy  
            3: '☁️',   # Overcast
            45: '🌫️', # Fog
            48: '🌫️', # Depositing rime fog
            51: '🌦️', # Light drizzle
            53: '🌧️', # Moderate drizzle
            55: '🌧️', # Dense drizzle
            61: '🌧️', # Slight rain
            63: '🌧️', # Moderate rain
            65: '⛈️',  # Heavy rain
            71: '🌨️', # Slight snow
            73: '🌨️', # Moderate snow
            75: '❄️',  # Heavy snow
            95: '⛈️',  # Thunderstorm
        }
        
        icon = weather_icons.get(weather_code, '🌤️')
        sunrise, sunset = calculate_sunrise_sunset()
        
        return {
            'temperature': f"{temp_f}°F",
            'icon': icon,
            'sunrise': sunrise,
            'sunset': sunset
        }
        
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        sunrise, sunset = calculate_sunrise_sunset()
        return {
            'temperature': 'N/A',
            'icon': '🌤️',
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
