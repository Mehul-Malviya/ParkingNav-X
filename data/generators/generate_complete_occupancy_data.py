#!/usr/bin/env python3
"""
Complete VIT-AP Synthetic Occupancy Data Generator
====================================================
Generates 1 month of parking occupancy data with:
✅ NO NULL values
✅ Realistic temporal patterns (morning peak, lunch dip, evening peak)
✅ Enforced capacity constraints (occupied <= capacity)
✅ Temporal continuity (occupancy evolves, not random)
✅ Field-level provenance tracking
✅ Academic calendar integration
✅ Event-aware demand multipliers
✅ Complete CSV output ready for database import

Generation: 2026-09-01 to 2026-09-30 (30 days)
Resolution: 15-minute intervals = 2,880 observations per lot
Total records: 2,880 × 5 lots = 14,400 rows (NO NULLs)
"""

import csv
import json
from datetime import datetime, timedelta
import random
import math


# =====================================================================
# CONSTANTS & CONFIGURATION
# =====================================================================

CAMPUS_ID = "vitap"
START_DATE = datetime(2026, 9, 1, 0, 0, 0)
END_DATE = datetime(2026, 9, 30, 23, 45, 0)
INTERVAL_MINUTES = 15

PARKING_LOTS = {
    "vitap-lot-academic-main": {
        "total_capacity": 120,
        "usable_capacity": 108,
        "reserved_capacity": 8,
        "restricted_capacity": 4,
        "base_demand_factor": 0.75,  # Occupancy 75% on average
        "zone": "academic_zone",
    },
    "vitap-lot-hostel": {
        "total_capacity": 180,
        "usable_capacity": 162,
        "reserved_capacity": 12,
        "restricted_capacity": 6,
        "base_demand_factor": 0.60,  # Occupancy 60% on average
        "zone": "hostel_zone",
    },
    "vitap-lot-admin-visitor": {
        "total_capacity": 80,
        "usable_capacity": 72,
        "reserved_capacity": 5,
        "restricted_capacity": 3,
        "base_demand_factor": 0.50,  # Occupancy 50% on average
        "zone": "admin_zone",
    },
    "vitap-lot-sports": {
        "total_capacity": 100,
        "usable_capacity": 90,
        "reserved_capacity": 7,
        "restricted_capacity": 3,
        "base_demand_factor": 0.40,  # Occupancy 40% on average
        "zone": "sports_zone",
    },
    "vitap-lot-overflow": {
        "total_capacity": 60,
        "usable_capacity": 54,
        "reserved_capacity": 4,
        "restricted_capacity": 2,
        "base_demand_factor": 0.20,  # Occupancy 20% (only used during peak)
        "zone": "overflow_zone",
    },
}

# Time-of-day demand patterns (multipliers for base demand)
HOUR_DEMAND_PROFILE = {
    # Night: minimal demand
    0: 0.05,   1: 0.03,   2: 0.02,   3: 0.02,   4: 0.03,   5: 0.05,
    # Early morning: slow increase
    6: 0.15,   7: 0.30,
    # Morning peak (classes start)
    8: 0.85,   9: 0.95,   10: 0.90,
    # Late morning
    11: 0.80,
    # Noon: slight dip for lunch
    12: 0.70,  13: 0.75,
    # Afternoon: moderate
    14: 0.80,  15: 0.85,  16: 0.90,
    # Evening: decline as classes end
    17: 0.75,  18: 0.50,
    # Night: low
    19: 0.25,  20: 0.15,  21: 0.10,  22: 0.08,  23: 0.06,
}

# Day-of-week factors (Monday=0, Sunday=6)
DAY_DEMAND_FACTORS = {
    0: 1.0,    # Monday: normal
    1: 1.0,    # Tuesday: normal
    2: 1.0,    # Wednesday: normal
    3: 1.0,    # Thursday: normal
    4: 0.95,   # Friday: slightly lower
    5: 0.30,   # Saturday: very low (weekend)
    6: 0.25,   # Sunday: very low (weekend)
}

# Academic calendar modifiers
EXAM_PERIOD_MULTIPLIER = 0.40  # Exams reduce campus presence
HOLIDAY_MULTIPLIER = 0.05      # Holidays have minimal traffic
SEMESTER_START_MULTIPLIER = 1.2  # Semester start increases traffic
PLACEMENT_SEASON_MULTIPLIER = 1.15  # Placement season increases demand

# Events with demand multipliers
EVENTS = [
    {
        "date": datetime(2026, 9, 5),
        "name": "Semester Start",
        "type": "academic",
        "multiplier": SEMESTER_START_MULTIPLIER,
        "affected_zones": ["academic_zone", "hostel_zone"],
    },
    {
        "date": datetime(2026, 9, 15),
        "name": "Placement Drive Week 1",
        "type": "placement",
        "multiplier": PLACEMENT_SEASON_MULTIPLIER,
        "affected_zones": ["admin_zone", "academic_zone"],
    },
    {
        "date": datetime(2026, 9, 20),
        "name": "Sports Festival",
        "type": "event",
        "multiplier": 1.5,
        "affected_zones": ["sports_zone", "academic_zone"],
    },
]

# Holidays/breaks (minimal traffic)
HOLIDAYS = [
    (datetime(2026, 9, 1), datetime(2026, 9, 1)),  # Founding day
    (datetime(2026, 9, 9), datetime(2026, 9, 9)),  # Mid-month holiday
]


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def get_occupancy_factor(timestamp, lot_zone):
    """
    Calculate occupancy factor for a given timestamp and parking zone.
    Returns a value 0-1 representing demand intensity.
    """
    hour = timestamp.hour
    day_of_week = timestamp.weekday()
    date = timestamp.date()

    # Base hourly demand
    hourly_factor = HOUR_DEMAND_PROFILE.get(hour, 0.5)

    # Day-of-week adjustment
    day_factor = DAY_DEMAND_FACTORS.get(day_of_week, 1.0)

    # Holiday adjustment
    is_holiday = False
    for holiday_start, holiday_end in HOLIDAYS:
        holiday_start_date = holiday_start.date() if isinstance(holiday_start, datetime) else holiday_start
        holiday_end_date = holiday_end.date() if isinstance(holiday_end, datetime) else holiday_end
        if holiday_start_date <= date <= holiday_end_date:
            is_holiday = True
            break

    if is_holiday:
        return hourly_factor * day_factor * HOLIDAY_MULTIPLIER

    # Event-based multiplier
    event_multiplier = 1.0
    for event in EVENTS:
        event_date = event["date"].date()
        # Event affects 3 days (day before, day of, day after)
        if abs((timestamp - event["date"]).days) <= 1:
            if lot_zone in event["affected_zones"]:
                event_multiplier = event["multiplier"]
                break

    # Exam period simulation (Sept 23-30)
    is_exam_period = datetime(2026, 9, 23) <= timestamp <= datetime(2026, 9, 30)
    if is_exam_period:
        hourly_factor *= EXAM_PERIOD_MULTIPLIER

    total_factor = hourly_factor * day_factor * event_multiplier

    # Clamp to valid range
    return min(1.0, max(0.0, total_factor))


def generate_occupancy_with_continuity(
    lot_id, lot_config, timestamp, prev_occupancy
):
    """
    Generate realistic occupancy that evolves continuously.
    occupancy(t+1) ≈ occupancy(t) + arrivals - departures
    """
    capacity = lot_config["usable_capacity"]
    base_demand = lot_config["base_demand_factor"]
    zone = lot_config["zone"]

    # Get demand multiplier for this time
    demand_mult = get_occupancy_factor(timestamp, zone)

    # Target occupancy for this time
    target_occupancy = capacity * base_demand * demand_mult

    # Add small random variation (±5%)
    variation = random.uniform(-0.05, 0.05)
    target_occupancy = target_occupancy * (1 + variation)

    # Smooth transition from previous occupancy (heavy smoothing = more realistic)
    smoothing_factor = 0.3  # 30% change per interval, 70% from previous
    if prev_occupancy is None:
        current_occupancy = target_occupancy
    else:
        current_occupancy = (
            prev_occupancy * smoothing_factor +
            target_occupancy * (1 - smoothing_factor)
        )

    # Ensure within bounds
    current_occupancy = max(0, min(capacity, current_occupancy))

    # Convert to integer
    occupied_spaces = int(round(current_occupancy))

    # Ensure valid constraints
    occupied_spaces = max(0, min(capacity, occupied_spaces))
    available_spaces = capacity - occupied_spaces
    occupancy_rate = occupied_spaces / capacity if capacity > 0 else 0.0

    return occupied_spaces, available_spaces, occupancy_rate


def generate_all_occupancy_data():
    """
    Generate complete occupancy data for all parking lots.
    Returns list of dictionaries ready for CSV export.
    """
    records = []
    current_timestamp = START_DATE
    lot_occupancy_history = {lot_id: None for lot_id in PARKING_LOTS.keys()}

    while current_timestamp <= END_DATE:
        for lot_id, lot_config in PARKING_LOTS.items():
            # Generate realistic occupancy with continuity
            occupied, available, occ_rate = generate_occupancy_with_continuity(
                lot_id, lot_config, current_timestamp, lot_occupancy_history[lot_id]
            )

            # Store for next iteration
            lot_occupancy_history[lot_id] = occupied

            # Create complete record with NO NULL values
            record = {
                "campus_id": CAMPUS_ID,
                "parking_lot_id": lot_id,
                "occupied_spaces": occupied,
                "available_spaces": available,
                "occupancy_percentage": round(occ_rate, 4),
                "predicted_occupancy": json.dumps({
                    "t_15min": min(lot_config["usable_capacity"], int(occupied * 1.05)),
                    "t_30min": min(lot_config["usable_capacity"], int(occupied * 1.10)),
                    "t_60min": min(lot_config["usable_capacity"], int(occupied * 1.15)),
                    "confidence": "SYNTHETIC",
                }),
                "status": "open",
                "observation_timestamp": current_timestamp.isoformat(),
                "ingestion_timestamp": datetime.now().isoformat(),
                "source": "synthetic_generator",
                "provenance": "SYNTHETIC",
            }

            # Validate: no NULL values
            for key, value in record.items():
                if value is None:
                    raise ValueError(f"NULL value in {key} for {lot_id} at {current_timestamp}")

            records.append(record)

        # Move to next 15-minute interval
        current_timestamp += timedelta(minutes=INTERVAL_MINUTES)

    return records


# =====================================================================
# MAIN EXECUTION
# =====================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("VIT-AP COMPLETE OCCUPANCY DATA GENERATOR")
    print("=" * 70)
    print()

    print(f"Generating occupancy data...")
    print(f"  Period: {START_DATE.date()} to {END_DATE.date()} (30 days)")
    print(f"  Interval: {INTERVAL_MINUTES} minutes")
    print(f"  Parking lots: {len(PARKING_LOTS)}")
    print(f"  Total records expected: {len(PARKING_LOTS)} × {(END_DATE - START_DATE).days * 96} = {len(PARKING_LOTS) * (END_DATE - START_DATE).days * 96}")
    print()

    # Generate data
    records = generate_all_occupancy_data()

    print(f"[OK] Generated {len(records)} complete records (NO NULLs)")
    print()

    # Export to CSV
    output_file = "vitap_occupancy_data_complete_30days.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "campus_id",
            "parking_lot_id",
            "occupied_spaces",
            "available_spaces",
            "occupancy_percentage",
            "predicted_occupancy",
            "status",
            "observation_timestamp",
            "ingestion_timestamp",
            "source",
            "provenance",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"[OK] Exported to: {output_file}")
    print()

    # Print summary statistics
    print("=" * 70)
    print("DATA QUALITY VALIDATION")
    print("=" * 70)
    print()

    for lot_id, lot_config in PARKING_LOTS.items():
        lot_records = [r for r in records if r["parking_lot_id"] == lot_id]
        occupancies = [r["occupied_spaces"] for r in lot_records]

        print(f"{lot_id}:")
        print(f"  Total records: {len(lot_records)}")
        print(f"  Capacity: {lot_config['usable_capacity']}")
        print(f"  Min occupancy: {min(occupancies)} ({min(occupancies)/lot_config['usable_capacity']*100:.1f}%)")
        print(f"  Max occupancy: {max(occupancies)} ({max(occupancies)/lot_config['usable_capacity']*100:.1f}%)")
        print(f"  Avg occupancy: {sum(occupancies)/len(occupancies):.1f} ({sum(occupancies)/len(occupancies)/lot_config['usable_capacity']*100:.1f}%)")

        # Validate constraints
        violations = sum(1 for r in lot_records if r["occupied_spaces"] > lot_config["usable_capacity"])
        nulls = sum(1 for r in lot_records if any(v is None for v in r.values()))

        if violations > 0:
            print(f"  ⚠️  CONSTRAINT VIOLATIONS: {violations}")
        else:
            print(f"  ✅ No capacity violations")

        if nulls > 0:
            print(f"  ⚠️  NULL VALUES: {nulls}")
        else:
            print(f"  ✅ No NULL values")

        print()

    print("=" * 70)
    print("OCCUPANCY DATA GENERATION COMPLETE")
    print("=" * 70)
    print()
    print(f"Import into database with:")
    print(f"  sqlite3 digital_twin.db \".mode csv\"")
    print(f"  sqlite3 digital_twin.db \".import {output_file} parking_lot_state\"")
    print()
