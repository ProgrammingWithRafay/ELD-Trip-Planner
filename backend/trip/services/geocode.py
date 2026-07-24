import requests
import urllib.parse
from typing import Tuple

def geocode_location(location: str) -> Tuple[float, float, str]:
    """
    Returns (lat, lng, display_name).
    Raises ValueError if location cannot be geocoded.
    """
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location)}&format=json&limit=1"
    headers = {
        "User-Agent": "ELD-Trip-Planner-App/1.0 (test submission)"
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    if not data:
        raise ValueError(f"Couldn't find this location: {location}")
        
    lat = float(data[0]["lat"])
    lng = float(data[0]["lon"])
    display_name = data[0]["display_name"]
        
    return lat, lng, display_name
