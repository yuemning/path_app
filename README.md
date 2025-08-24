# PATH Train Departures - Grove Street Station

A simple, clean web app to display real-time PATH train departure times for Grove Street (GRV) station. Perfect for apartment displays or quick departure checks.

## Features

- **Real-time data** from the official PATH API
- **Clean, modern interface** with color-coded line indicators
- **Auto-refresh** every 30 seconds
- **Mobile responsive** design
- **Visual indicators** for urgent/soon/normal departure times
- **Lightweight** - just Flask and requests dependencies

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   python app.py
   ```

3. **Open in browser:**
   ```
   http://localhost:5000
   ```

## Data Source

This app fetches real-time data from the official Port Authority PATH API:
- API: https://www.panynj.gov/bin/portauthority/ridepath.json
- Shows departures for Grove Street (GRV) station
- Updates automatically every 30 seconds

## Display Features

- **Color-coded lines** matching PATH system colors
- **Time-based urgency indicators:**
  - Red (pulsing): ≤5 minutes or delayed
  - Yellow: 5-10 minutes  
  - Green: >10 minutes
- **Direction labels:** "To New York" or "To New Jersey"
- **Clean destination names** (e.g., "33rd St" instead of "33rd Street via Hoboken")

## Apartment Display Tips

- Works great on tablets, phones, or small monitors
- Responsive design adapts to different screen sizes
- Auto-refresh means you can leave it running continuously
- Glass-morphism design looks modern on any wall mount

## Technical Details

- **Backend:** Python Flask (lightweight web server)
- **Frontend:** Vanilla HTML/CSS/JavaScript (no frameworks)
- **API calls:** Uses requests library with error handling
- **Refresh rate:** 30 seconds (configurable in JavaScript)
- **Port:** Runs on port 5000 by default

Enjoy your real-time PATH departures! 🚇
