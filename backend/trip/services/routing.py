import requests
from typing import List, Tuple, Dict, Any

def get_route(waypoints: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    waypoints: list of (lat, lng) tuples.
    Returns dict with geometry (list of [lat, lng]), distance_miles, duration_hours.
    """
    # OSRM expects lon,lat for coordinates
    coords = ";".join([f"{lng},{lat}" for lat, lng in waypoints])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("Couldn't calculate a route right now — please try again.")
        
    route = data["routes"][0]
    
    # OSRM returns coordinates as [lon, lat], Leaflet expects [lat, lon]
    geometry = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]
    
    distance_miles = route["distance"] * 0.000621371
    duration_hours = route["duration"] / 3600.0
    
    return {
        "geometry": geometry,
        "distance_miles": distance_miles,
        "duration_hours": duration_hours
    }
