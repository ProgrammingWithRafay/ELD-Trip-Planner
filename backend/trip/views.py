import traceback
import math
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TripRequestSerializer
from .services.geocode import geocode_location
from .services.routing import get_route
from .services.hos_engine import build_daily_logs, Stop, TripPlan

from dataclasses import asdict

class PlanTripView(APIView):
    def post(self, request):
        serializer = TripRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "Invalid input", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        
        # 1. Geocode locations
        try:
            cur_lat, cur_lng, cur_label = geocode_location(data["current_location"])
            pick_lat, pick_lng, pick_label = geocode_location(data["pickup_location"])
            drop_lat, drop_lng, drop_label = geocode_location(data["dropoff_location"])
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Geocoding service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        # 2. Routing
        waypoints = [(cur_lat, cur_lng), (pick_lat, pick_lng), (drop_lat, drop_lng)]
        try:
            route_data = get_route(waypoints)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Routing service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        # 3. HOS Calculation
        try:
            daily_logs = build_daily_logs(
                total_driving_hours=route_data["duration_hours"],
                total_distance_miles=route_data["distance_miles"],
                current_cycle_used=data["current_cycle_used"]
            )
        except Exception as e:
            traceback.print_exc()
            return Response({"error": "Failed to calculate daily logs."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # 4. Compile stops with approximate locations for fuel/rest
        stops = []
        stops.append(Stop(type="start", location_label=data["current_location"], lat=cur_lat, lng=cur_lng, day=1))
        stops.append(Stop(type="pickup", location_label=data["pickup_location"], lat=pick_lat, lng=pick_lng, day=1))
        
        route_geom = route_data["geometry"]
        def get_interpolated_coord(ratio: float) -> tuple[float, float]:
            if not route_geom:
                return (0.0, 0.0)
            idx = int(ratio * (len(route_geom) - 1))
            idx = max(0, min(len(route_geom) - 1, idx))
            return route_geom[idx][0], route_geom[idx][1]

        # In a real app, we would sum segment durations to find exactly when the rest/fuel occurs
        # and interpolate along the route line by distance.
        # For this assessment, we approximate the mid-route stops.
        time_elapsed = 0.0
        
        for log in daily_logs:
            for seg in log.segments:
                if seg.status == "driving":
                    time_elapsed += (seg.end_hr - seg.start_hr)
                elif seg.status == "on_duty_not_driving" and "fuel" in seg.label.lower():
                    ratio = time_elapsed / max(1e-6, route_data["duration_hours"])
                    lat, lng = get_interpolated_coord(ratio)
                    stops.append(Stop(type="fuel", location_label="approx. mid-route", lat=lat, lng=lng, day=log.day))
                elif seg.status == "off_duty" and "break" in seg.label.lower():
                    ratio = time_elapsed / max(1e-6, route_data["duration_hours"])
                    lat, lng = get_interpolated_coord(ratio)
                    stops.append(Stop(type="rest", location_label="approx. mid-route", lat=lat, lng=lng, day=log.day))
        
        stops.append(Stop(type="dropoff", location_label=data["dropoff_location"], lat=drop_lat, lng=drop_lng, day=daily_logs[-1].day))
        
        warnings = []
        if data["current_cycle_used"] >= 70.0:
            warnings.append("Note: driver must take a 34-hour restart before this trip can begin due to cycle hours already used.")
        
        trip_plan = TripPlan(
            route={
                "geometry": route_data["geometry"],
                "distance_miles": route_data["distance_miles"],
                "duration_hours": route_data["duration_hours"],
            },
            stops=stops,
            daily_logs=daily_logs,
            warnings=warnings
        )
        
        return Response(asdict(trip_plan), status=status.HTTP_200_OK)
