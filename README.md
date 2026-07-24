# ELD Trip Planner

A full-stack web application designed to help commercial truck drivers plan their routes and automatically generate Electronic Logging Device (ELD) style driver logs in compliance with FMCSA Hours of Service (HOS) regulations.

## Features

- **Route Planning**: Enter your current location, pickup, and dropoff destinations.
- **HOS Compliance Engine**: Automatically calculates driving limits (11-hour limit, 14-hour window, 70-hour/8-day rolling limit) and inserts mandatory 30-minute breaks and 34-hour restarts when needed.
- **Automated Stops**: Inserts 1-hour stops for pickup and dropoff, and automatically schedules 30-minute fuel stops every 1,000 miles.
- **FMCSA Log Generation**: Dynamically draws the standard FMCSA daily graph grid in SVG, spanning multiple days for long cross-country routes.
- **Modern UI**: A responsive, clean React frontend using Leaflet for interactive map visualizations of the route and stops.

## Tech Stack

- **Frontend**: React, Vite, Leaflet (React-Leaflet), Vanilla CSS (Custom Design System).
- **Backend**: Python, Django, Django REST Framework.
- **External Services**: 
  - Nominatim (OpenStreetMap) for geocoding
  - OSRM (Open Source Routing Machine) for route distance, duration, and geometry

## Project Structure

- `/backend`: The Django backend containing the core pure-Python `hos_engine.py` logic and API views.
- `/frontend`: The Vite+React frontend containing the interactive trip form, summary, map, and SVG log components.

## Local Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # (On Windows) or source venv/bin/activate (On Mac/Linux)
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Start the Django development server
python manage.py runserver
```

### 2. Frontend Setup

```bash
cd frontend
npm install

# Start the Vite development server
npm run dev
```

The application will now be available at `http://localhost:5173`.

## Assumptions & Simplifications

As per the project scope, the following assumptions were made:
- **Driver Type**: Property-carrying driver (not passenger-carrying).
- **Adverse Conditions**: No adverse driving condition extensions are supported.
- **Sleeper Berth**: Complex split-sleeper berth provisions are intentionally excluded. All mandatory rests are logged as standard `off_duty`.
- **Persistence**: There are no user accounts or saved trips. The application is entirely stateless.

## Testing

The core business logic (the HOS engine) is completely isolated from Django and the network. You can run the extensive test suite using:

```bash
cd backend
python manage.py test trip.tests
```

This will run through multiple simulated scenarios (short trips, multi-day long hauls, max-cycle restarts) to ensure the engine accurately tracks duty status buckets exactly as the FMCSA manual defines.
