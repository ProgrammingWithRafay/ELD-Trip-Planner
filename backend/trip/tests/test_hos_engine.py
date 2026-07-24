"""
test_hos_engine.py

Concrete test cases for hos_engine.build_daily_logs(), with expected values
derived BY HAND against the FMCSA rules (see 02-TechSpec.md) before any
implementation exists. Do not adjust these expected values to match whatever
the implementation produces -- if a test fails, the implementation has a
bug, not the test. If you believe an expected value here is actually wrong,
flag it in 07-Tracker.md's "Known issues" section with your reasoning
rather than silently changing the assertion.

Field convention (see 05-Schema.md):
  total_driving_hr = 'driving' status only
  total_on_duty_hr = 'driving' + 'on_duty_not_driving' COMBINED
                      (this is the FMCSA on-duty definition used against the
                      11hr/14hr/70hr limits, NOT on_duty_not_driving alone)
  total_off_duty_hr = 'off_duty' status only
  total_sleeper_hr  = 'sleeper_berth' status only

  Independent buckets that must sum to 24 for every day:
    total_driving_hr
    + (total_on_duty_hr - total_driving_hr)   # on_duty_not_driving portion
    + total_off_duty_hr
    + total_sleeper_hr

Fixed assumptions baked into every scenario (per PRD Section 4):
  - property-carrying driver, 70hr/8-day cycle
  - no adverse driving conditions
  - fuel stop every 1000 miles (0.5hr, on_duty_not_driving)
  - pickup = 1hr on_duty_not_driving, dropoff = 1hr on_duty_not_driving
  - 30-minute break required after 8 cumulative driving hours
  - 11hr driving limit, 14hr on-duty window, per day
  - 10 consecutive off-duty hours resets the 11hr/14hr clocks
  - 70hr/8-day rolling on-duty ceiling; hitting it forces a 34-consecutive-
    hour restart (off_duty or sleeper_berth) before driving can resume
"""

import pytest
from trip.services.hos_engine import build_daily_logs, DayLog, Segment


def _assert_day_sums_to_24(day: DayLog):
    """Structural invariant that must hold for every single day, in every
    scenario, with no exceptions."""
    on_duty_not_driving = day.total_on_duty_hr - day.total_driving_hr
    total = (
        day.total_driving_hr
        + on_duty_not_driving
        + day.total_off_duty_hr
        + day.total_sleeper_hr
    )
    assert total == pytest.approx(24, abs=1e-6), (
        f"Day {day.day} sums to {total}, not 24. "
        f"driving={day.total_driving_hr}, on_duty_not_driving={on_duty_not_driving}, "
        f"off_duty={day.total_off_duty_hr}, sleeper={day.total_sleeper_hr}"
    )
    # segments themselves must also cover 0-24 with no gaps or overlaps
    segs = sorted(day.segments, key=lambda s: s.start_hr)
    assert segs[0].start_hr == pytest.approx(0, abs=1e-6)
    assert segs[-1].end_hr == pytest.approx(24, abs=1e-6)
    for a, b in zip(segs, segs[1:]):
        assert a.end_hr == pytest.approx(b.start_hr, abs=1e-6), (
            f"Gap or overlap between segments in day {day.day}: "
            f"{a} ends at {a.end_hr}, next starts at {b.start_hr}"
        )


def _assert_no_cap_violations(day: DayLog):
    """No day may show more than 11 driving hours, and total on-duty time
    from the start of the on-duty period to the end of the last driving
    segment must not exceed 14 hours (the 14-hour window)."""
    assert day.total_driving_hr <= 11 + 1e-6, (
        f"Day {day.day} shows {day.total_driving_hr}hr driving, exceeds 11hr limit"
    )
    driving_segs = [s for s in day.segments if s.status == "driving"]
    if driving_segs:
        on_duty_segs = [
            s for s in day.segments
            if s.status in ("driving", "on_duty_not_driving")
        ]
        window_start = min(s.start_hr for s in on_duty_segs)
        window_end = max(s.end_hr for s in driving_segs)
        assert window_end - window_start <= 14 + 1e-6, (
            f"Day {day.day} 14-hour on-duty window violated: "
            f"{window_end - window_start}hr from on-duty start to last driving segment"
        )


# ---------------------------------------------------------------------------
# Scenario 1: short trip -- single day, no fuel stop, no 30-min break needed
# ---------------------------------------------------------------------------
def test_short_trip_single_day():
    """
    200 miles, 4 hours driving, cycle_used=0.
    Expected: everything fits in day 1.
      - pickup: 1hr on_duty_not_driving (hr 0-1)
      - driving: 4hr (hr 1-5)
      - dropoff: 1hr on_duty_not_driving (hr 5-6)
      - off_duty: remaining 18hr (hr 6-24)
    No fuel stop (200 < 1000 miles). No 30-min break (4hr driving < 8hr
    threshold).
    """
    logs = build_daily_logs(
        total_driving_hours=4.0,
        total_distance_miles=200.0,
        current_cycle_used=0.0,
    )

    assert len(logs) == 1
    day = logs[0]

    assert day.total_driving_hr == pytest.approx(4.0)
    assert day.total_on_duty_hr == pytest.approx(6.0)  # 4 driving + 1 pickup + 1 dropoff
    assert day.total_off_duty_hr == pytest.approx(18.0)
    assert day.total_sleeper_hr == pytest.approx(0.0)

    statuses = [s.status for s in day.segments]
    assert "driving" in statuses
    assert statuses.count("on_duty_not_driving") >= 2  # pickup + dropoff, no fuel

    fuel_segments = [s for s in day.segments if "fuel" in s.label.lower()]
    assert len(fuel_segments) == 0, "200-mile trip should not trigger a fuel stop"

    break_segments = [
        s for s in day.segments
        if s.status == "off_duty" and "break" in s.label.lower()
    ]
    assert len(break_segments) == 0, "4hr driving should not trigger the 30-min break"

    _assert_day_sums_to_24(day)
    _assert_no_cap_violations(day)


# ---------------------------------------------------------------------------
# Scenario 2: medium trip -- exactly hits 11hr driving limit, triggers the
# 30-minute break, all still fits within one day's 14-hour window
# ---------------------------------------------------------------------------
def test_medium_trip_triggers_break_single_day():
    """
    650 miles, 11 hours driving (right at the daily driving cap), cycle_used=0.
    Expected within day 1:
      - pickup: 1hr on_duty_not_driving (hr 0-1)
      - driving: 8hr (hr 1-9)              <- hits 8hr cumulative driving
      - 30-min break: 0.5hr off_duty (hr 9-9.5)
      - driving: 3hr (hr 9.5-12.5)          <- brings total driving to 11hr
      - dropoff: 1hr on_duty_not_driving (hr 12.5-13.5)
      - off_duty: remaining 10.5hr (hr 13.5-24)
    14-hour window check: on-duty starts at hr 0 (pickup), last driving
    segment ends at hr 12.5 -> 12.5hr window used, under the 14hr cap.
    No fuel stop (650 < 1000 miles).
    Total off_duty for the day = 0.5hr break + 10.5hr end-of-day rest = 11.0hr.
    """
    logs = build_daily_logs(
        total_driving_hours=11.0,
        total_distance_miles=650.0,
        current_cycle_used=0.0,
    )

    assert len(logs) == 1
    day = logs[0]

    assert day.total_driving_hr == pytest.approx(11.0)
    assert day.total_on_duty_hr == pytest.approx(13.0)  # 11 driving + 1 pickup + 1 dropoff
    assert day.total_off_duty_hr == pytest.approx(11.0)  # 0.5hr break + 10.5hr end-of-day rest
    assert day.total_sleeper_hr == pytest.approx(0.0)

    break_segments = [
        s for s in day.segments
        if s.status == "off_duty" and s.end_hr - s.start_hr == pytest.approx(0.5)
        and s.end_hr < 20  # distinguish the mid-day break from the end-of-day rest
    ]
    assert len(break_segments) == 1, "11hr driving trip must trigger exactly one 30-min break"

    fuel_segments = [s for s in day.segments if "fuel" in s.label.lower()]
    assert len(fuel_segments) == 0, "650-mile trip should not trigger a fuel stop"

    _assert_day_sums_to_24(day)
    _assert_no_cap_violations(day)


# ---------------------------------------------------------------------------
# Scenario 3: long trip -- multi-day, multiple fuel stops
# ---------------------------------------------------------------------------
def test_long_trip_multi_day_with_fuel_stops():
    """
    2400 miles, 40 hours driving, cycle_used=0.
    Expected shape (derived by hand, see derivation notes below):
      - 4 driving days total
      - driving hours per day: [11, 11, 11, 7]
      - exactly 2 fuel stops total (crossed at ~1000mi and ~2000mi, which
        fall within day 2 and day 3 respectively given the above driving
        distribution)
      - exactly 3 thirty-minute breaks (days 1, 2, 3 each hit 8hr cumulative
        driving before completing that day's driving; day 4 only drives 7hr
        and never crosses the 8hr threshold within that day)
      - pickup appears only on day 1, dropoff only on the final day
      - total driving across all days == 40.0
      - every day individually respects the 11hr/14hr caps
      - cycle_used stays well under 70 throughout (0 -> ~40 by trip end),
        so no 34-hour restart should be triggered in this scenario
    """
    logs = build_daily_logs(
        total_driving_hours=40.0,
        total_distance_miles=2400.0,
        current_cycle_used=0.0,
    )

    assert len(logs) == 4, f"expected 4 days, got {len(logs)}"

    expected_driving_by_day = [11.0, 11.0, 11.0, 7.0]
    for day, expected in zip(logs, expected_driving_by_day):
        assert day.total_driving_hr == pytest.approx(expected), (
            f"day {day.day}: expected {expected}hr driving, got {day.total_driving_hr}"
        )

    total_driving = sum(day.total_driving_hr for day in logs)
    assert total_driving == pytest.approx(40.0)

    all_segments = [s for day in logs for s in day.segments]
    fuel_segments = [s for s in all_segments if "fuel" in s.label.lower()]
    assert len(fuel_segments) == 2, f"expected 2 fuel stops, got {len(fuel_segments)}"

    pickup_segments = [s for s in all_segments if "pickup" in s.label.lower()]
    dropoff_segments = [s for s in all_segments if "dropoff" in s.label.lower()]
    assert len(pickup_segments) == 1
    assert len(dropoff_segments) == 1
    assert any("pickup" in s.label.lower() for s in logs[0].segments), (
        "pickup must be on day 1"
    )
    assert any("dropoff" in s.label.lower() for s in logs[-1].segments), (
        "dropoff must be on the final day"
    )

    restart_segments = [
        s for s in all_segments
        if s.status in ("off_duty", "sleeper_berth") and (s.end_hr - s.start_hr) >= 34
    ]
    assert len(restart_segments) == 0, (
        "this trip should not require a 34-hour restart (cycle_used stays under 70)"
    )

    for day in logs:
        _assert_day_sums_to_24(day)
        _assert_no_cap_violations(day)


# ---------------------------------------------------------------------------
# Scenario 4: high starting cycle -- forces a 34-hour restart almost
# immediately since only 5 hours remain before the 70-hour ceiling
# ---------------------------------------------------------------------------
def test_high_starting_cycle_forces_immediate_restart():
    """
    300 miles, 6 hours driving, current_cycle_used=65 (only 5hr remain
    before the 70hr/8-day ceiling).

    Expected (derived by hand):
      Day 1:
        - pickup: 1hr on_duty_not_driving (hr 0-1) -> cycle_used becomes 66
        - driving: 4hr (hr 1-5) -> cycle_used becomes 70, the ceiling
          (70hr cap binds before the 11hr/14hr caps do -- only 5hr of
          on-duty capacity existed before hitting 70)
        - off_duty: remaining 19hr (hr 5-24) -- this begins the mandatory
          34-consecutive-hour restart
        - 2 driving hours still owed (6 total - 4 done = 2 remaining)
      Day 2:
        - off_duty: hr 0-15 (completes the 34hr restart: 19hr from day 1
          + 15hr into day 2 = 34hr exactly)
        - cycle resets to 0 once the restart completes
        - driving: 2hr (hr 15-17) -- the remaining driving from the trip
        - dropoff: 1hr on_duty_not_driving (hr 17-18)
        - off_duty: remaining 6hr (hr 18-24)

    This is the one scenario where the 70-hour limit, not the 11-hour or
    14-hour limit, is what forces the day to end.
    """
    logs = build_daily_logs(
        total_driving_hours=6.0,
        total_distance_miles=300.0,
        current_cycle_used=65.0,
    )

    assert len(logs) == 2, f"expected 2 days, got {len(logs)}"

    day1, day2 = logs[0], logs[1]

    assert day1.total_driving_hr == pytest.approx(4.0)
    assert day1.total_on_duty_hr == pytest.approx(5.0)  # 4 driving + 1 pickup
    assert day1.total_off_duty_hr == pytest.approx(19.0)
    assert day1.total_sleeper_hr == pytest.approx(0.0)

    restart_segments_day1 = [
        s for s in day1.segments
        if s.status == "off_duty" and (s.end_hr - s.start_hr) == pytest.approx(19.0)
    ]
    assert len(restart_segments_day1) == 1, "day 1 must end with a 19hr off-duty block starting the restart"

    restart_portion_day2 = [
        s for s in day2.segments
        if s.status == "off_duty" and s.start_hr == pytest.approx(0.0)
        and (s.end_hr - s.start_hr) == pytest.approx(15.0)
    ]
    assert len(restart_portion_day2) == 1, (
        "day 2 must begin with a 15hr off-duty block completing the 34hr restart "
        "(19hr from day 1 + 15hr = 34hr total)"
    )

    assert day2.total_driving_hr == pytest.approx(2.0)
    assert day2.total_on_duty_hr == pytest.approx(3.0)  # 2 driving + 1 dropoff
    assert day2.total_off_duty_hr == pytest.approx(21.0)  # 15hr restart completion + 6hr after
    assert day2.total_sleeper_hr == pytest.approx(0.0)

    total_driving = day1.total_driving_hr + day2.total_driving_hr
    assert total_driving == pytest.approx(6.0)

    for day in logs:
        _assert_day_sums_to_24(day)
        _assert_no_cap_violations(day)


# ---------------------------------------------------------------------------
# Scenario 5 (cross-cutting): every scenario above already asserts the day-24
# invariant and cap checks individually via the helpers. This test re-runs
# the same invariant across a broader sweep of inputs as a regression net,
# so a future change to the engine can't quietly break the 24-hour or cap
# invariants for input combinations not covered by scenarios 1-4 above.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "total_driving_hours,total_distance_miles,current_cycle_used",
    [
        (1.0, 50.0, 0.0),
        (10.5, 600.0, 0.0),
        (25.0, 1500.0, 10.0),
        (70.0, 4000.0, 0.0),
        (5.0, 300.0, 69.5),
    ],
)
def test_invariants_hold_across_input_sweep(
    total_driving_hours, total_distance_miles, current_cycle_used
):
    logs = build_daily_logs(
        total_driving_hours=total_driving_hours,
        total_distance_miles=total_distance_miles,
        current_cycle_used=current_cycle_used,
    )
    assert len(logs) >= 1
    total_driving = sum(day.total_driving_hr for day in logs)
    assert total_driving == pytest.approx(total_driving_hours, abs=1e-6), (
        f"total driving across all days ({total_driving}) does not match "
        f"requested trip driving hours ({total_driving_hours})"
    )
    for day in logs:
        _assert_day_sums_to_24(day)
        _assert_no_cap_violations(day)
