from dataclasses import dataclass
from typing import Literal

DutyStatus = Literal["off_duty", "sleeper_berth", "driving", "on_duty_not_driving"]

@dataclass
class Segment:
    status: DutyStatus
    start_hr: float
    end_hr: float
    label: str

@dataclass
class DayLog:
    day: int
    date_offset: int
    segments: list[Segment]
    total_driving_hr: float
    total_on_duty_hr: float
    total_off_duty_hr: float
    total_sleeper_hr: float

@dataclass
class Stop:
    type: Literal["start", "pickup", "dropoff", "rest", "fuel"]
    location_label: str
    lat: float
    lng: float
    day: int | None

@dataclass
class TripPlan:
    route: dict  # {'geometry': ..., 'distance_miles': ..., 'duration_hours': ...}
    stops: list[Stop]
    daily_logs: list[DayLog]
    warnings: list[str]

def build_daily_logs(
    total_driving_hours: float,
    total_distance_miles: float,
    current_cycle_used: float,
) -> list[DayLog]:
    remaining_drive = total_driving_hours
    cycle_used = current_cycle_used
    day_idx = 1
    segments_today = []
    
    clock_14hr = 0.0
    drive_since_break = 0.0
    mile_marker = 0.0
    
    current_hr = 0.0
    
    logs = []
    
    def add_segment(status: DutyStatus, duration: float, label: str):
        nonlocal current_hr, day_idx, segments_today
        rem = duration
        while rem > 0:
            space_today = 24.0 - current_hr
            if space_today <= 1e-6:
                create_new_day_log()
                space_today = 24.0
            
            chunk = min(rem, space_today)
            if chunk > 1e-6:
                segments_today.append(Segment(status, current_hr, current_hr + chunk, label))
            current_hr += chunk
            rem -= chunk

    def create_new_day_log():
        nonlocal day_idx, current_hr, segments_today, clock_14hr, drive_since_break
        # Ensure it sums to 24
        if current_hr < 24.0 - 1e-6:
            segments_today.append(Segment("off_duty", current_hr, 24.0, "Rest"))
            current_hr = 24.0

        total_driving = sum(s.end_hr - s.start_hr for s in segments_today if s.status == "driving")
        total_on_duty = sum(s.end_hr - s.start_hr for s in segments_today if s.status in ("driving", "on_duty_not_driving"))
        total_off_duty = sum(s.end_hr - s.start_hr for s in segments_today if s.status == "off_duty")
        total_sleeper = sum(s.end_hr - s.start_hr for s in segments_today if s.status == "sleeper_berth")
        
        # Invariant check
        total_sum = total_driving + (total_on_duty - total_driving) + total_off_duty + total_sleeper
        assert abs(total_sum - 24.0) < 1e-6, f"Day {day_idx} segments sum to {total_sum}, not 24."
        
        logs.append(DayLog(
            day=day_idx,
            date_offset=day_idx - 1,
            segments=list(segments_today),
            total_driving_hr=total_driving,
            total_on_duty_hr=total_on_duty,
            total_off_duty_hr=total_off_duty,
            total_sleeper_hr=total_sleeper
        ))
        
        segments_today.clear()
        day_idx += 1
        current_hr = 0.0
        clock_14hr = 0.0
        drive_since_break = 0.0

    def enforce_34hr_restart():
        nonlocal clock_14hr, drive_since_break, cycle_used
        add_segment("off_duty", 34.0, "34-hour restart")
        clock_14hr = 0.0
        drive_since_break = 0.0
        cycle_used = 0.0

    # Insert pickup
    if cycle_used + 1.0 > 70.0:
        enforce_34hr_restart()
        
    add_segment("on_duty_not_driving", 1.0, "Pickup")
    clock_14hr += 1.0
    cycle_used += 1.0

    fuel_interval = total_distance_miles / total_driving_hours if total_driving_hours > 0 else 0
    next_fuel_mile = 1000.0
    
    def get_hours_driven_today():
        return sum(s.end_hr - s.start_hr for s in segments_today if s.status == "driving")

    while remaining_drive > 1e-6:
        if cycle_used >= 70.0 - 1e-6:
            enforce_34hr_restart()
            continue
            
        if drive_since_break >= 8.0 - 1e-6:
            add_segment("off_duty", 0.5, "30-minute break")
            clock_14hr += 0.5
            drive_since_break = 0.0
            continue
            
        if clock_14hr >= 14.0 - 1e-6 or get_hours_driven_today() >= 11.0 - 1e-6:
            create_new_day_log()
            continue

        max_drive = remaining_drive
        max_drive = min(max_drive, 11.0 - get_hours_driven_today())
        max_drive = min(max_drive, 14.0 - clock_14hr)
        max_drive = min(max_drive, 8.0 - drive_since_break)
        max_drive = min(max_drive, 70.0 - cycle_used)
        
        if fuel_interval > 0:
            dist_to_fuel = next_fuel_mile - mile_marker
            time_to_fuel = dist_to_fuel / fuel_interval
            if time_to_fuel > 1e-6 and time_to_fuel < max_drive:
                max_drive = time_to_fuel

        if max_drive > 1e-6:
            add_segment("driving", max_drive, "Driving")
            remaining_drive -= max_drive
            clock_14hr += max_drive
            drive_since_break += max_drive
            cycle_used += max_drive
            mile_marker += max_drive * fuel_interval
        
        if fuel_interval > 0 and abs(mile_marker - next_fuel_mile) < 1e-4:
            add_segment("on_duty_not_driving", 0.5, "Fuel stop")
            clock_14hr += 0.5
            cycle_used += 0.5
            next_fuel_mile += 1000.0

    # End of trip - Dropoff
    if cycle_used + 1.0 > 70.0:
        enforce_34hr_restart()

    add_segment("on_duty_not_driving", 1.0, "Dropoff")
    
    create_new_day_log()

    return logs
