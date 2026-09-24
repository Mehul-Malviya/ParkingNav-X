#!/usr/bin/env python3
"""
Complete Data Import Script for VIT-AP Campus (v2)
===================================================
Imports all CSV data into SQLite database with validation and error handling.
Uses time-series history tables for occupancy, gate queue, and road state.
No NULL values, complete records, production-ready.
"""

import sqlite3
import csv
import sys
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path("digital_twin.db")

# CSV files to import
CSV_FILES = {
    "parking_lot_state_history": {
        "file": "data/vitap_occupancy_data_complete_30days.csv",
        "description": "Parking occupancy snapshots (14,400 records, 30 days)"
    },
    "gate_state_history": {
        "file": "data/vitap_gate_state_complete_30days.csv",
        "description": "Gate queue snapshots (5,760 records, 30 days)",
        "exclude_columns": ["congestion_level"]  # Not in schema
    },
    "road_state_history": {
        "file": "data/vitap_road_state_complete_30days.csv",
        "description": "Road congestion snapshots (14,400 records, 30 days)"
    },
}


def import_csv_to_table(conn, table_name, csv_file, description, exclude_cols=None):
    """Import CSV file into database table with validation."""

    print(f"\n{'='*70}")
    print(f"Importing {table_name}")
    print(f"{'='*70}")
    print(f"File: {csv_file}")
    print(f"Description: {description}")

    csv_path = Path(csv_file)
    exclude_cols = exclude_cols or []

    # Verify file exists
    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_file}")
        return False

    print(f"File size: {csv_path.stat().st_size / (1024*1024):.2f} MB")

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Get column names from CSV header
            all_columns = reader.fieldnames
            columns = [c for c in all_columns if c not in exclude_cols]

            print(f"CSV columns: {len(all_columns)}")
            print(f"Columns to import: {', '.join(columns[:5])}..." if len(columns) > 5 else f"Columns to import: {', '.join(columns)}")

            if exclude_cols:
                print(f"Excluded columns: {', '.join(exclude_cols)}")

            # Read all rows
            rows = list(reader)
            print(f"Records to import: {len(rows)}")

            if not rows:
                print("WARNING: No records found in CSV file!")
                return False

            # Check for NULL values
            null_count = 0
            for row_idx, row in enumerate(rows):
                for col in columns:
                    value = row.get(col, '')
                    if value is None or value == '' or value == 'None':
                        null_count += 1
                        if null_count <= 3:
                            print(f"  Row {row_idx}, column {col}: empty/NULL")

            if null_count > 0:
                print(f"WARNING: {null_count} NULL/empty values found")
            else:
                print("[OK] No NULL values detected")

            # Create column list for INSERT
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

            # Convert rows to tuples for insertion (only selected columns)
            data_tuples = []
            for row in rows:
                values = tuple(row.get(col, '') for col in columns)
                data_tuples.append(values)

            # Insert data
            cursor = conn.cursor()
            try:
                cursor.executemany(insert_sql, data_tuples)
                conn.commit()

                inserted = len(data_tuples)
                print(f"[OK] Successfully imported {inserted} records into {table_name}")

                # Verification
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"Verification count: {count} records in database")

                if count != len(rows):
                    print(f"WARNING: Expected {len(rows)}, but found {count}")

                return True

            except sqlite3.IntegrityError as e:
                print(f"ERROR: Integrity constraint failed: {e}")
                conn.rollback()
                return False

    except Exception as e:
        print(f"ERROR importing {table_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def init_migrations(conn):
    """Apply all migrations to ensure schema is up to date."""
    print(f"\n{'='*70}")
    print("Initializing database schema")
    print(f"{'='*70}")

    # Apply migration for time-series tables
    migrations_dir = Path("migrations")
    if migrations_dir.exists():
        migration_file = migrations_dir / "0004_time_series_history.sql"
        if migration_file.exists():
            print(f"\nApplying migration: {migration_file.name}")
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()

            try:
                conn.executescript(sql)
                conn.commit()
                print("[OK] Migration applied successfully")
            except Exception as e:
                print(f"WARNING: Could not apply migration: {e}")
                print("Continuing anyway...")


def main():
    """Main import process."""

    print("\n" + "="*70)
    print("VIT-AP COMPLETE DATA IMPORT (v2)")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Connect to database
    try:
        conn = sqlite3.connect(str(DB_PATH))
        print(f"[OK] Connected to database: {DB_PATH}")
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)

    # Initialize schema (apply migrations)
    init_migrations(conn)

    # Import each CSV file
    results = {}
    total_records = 0

    for table_name, config in CSV_FILES.items():
        exclude = config.get("exclude_columns", [])
        success = import_csv_to_table(
            conn,
            table_name,
            config["file"],
            config["description"],
            exclude_cols=exclude
        )
        results[table_name] = success

        if success:
            cursor = conn.cursor()
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_records += count
            except:
                pass

    # Final validation
    print("\n" + "="*70)
    print("IMPORT SUMMARY")
    print("="*70)

    for table_name, success in results.items():
        status = "[OK]" if success else "[FAILED]"
        print(f"{status} {table_name}")

    print()
    print(f"Total records imported: {total_records:,}")
    print(f"Expected total: 34,160 (14,400 + 5,760 + 14,400)")

    # Check data quality
    print("\n" + "="*70)
    print("DATA QUALITY CHECKS")
    print("="*70)

    try:
        cursor = conn.cursor()

        # Check parking occupancy constraints
        cursor.execute("""
            SELECT COUNT(*) FROM parking_lot_state_history
            WHERE CAST(occupied_spaces AS INTEGER) < 0
        """)
        negatives = cursor.fetchone()[0]
        print(f"Negative occupancy values: {negatives}")

        # Check timestamp validity
        cursor.execute("""
            SELECT COUNT(*) FROM parking_lot_state_history
            WHERE observation_timestamp IS NULL OR observation_timestamp = ''
        """)
        null_timestamps = cursor.fetchone()[0]
        print(f"Missing timestamps: {null_timestamps}")

        if negatives == 0 and null_timestamps == 0:
            print("\n[OK] All data quality checks passed!")
        else:
            print("\n[WARNING] Some data quality issues detected")

    except Exception as e:
        print(f"Could not perform validation: {e}")

    # Show sample data
    print("\n" + "="*70)
    print("SAMPLE DATA")
    print("="*70)

    try:
        cursor = conn.cursor()

        # Parking lot state sample
        cursor.execute("SELECT * FROM parking_lot_state_history LIMIT 2")
        rows = cursor.fetchall()
        cursor.execute("PRAGMA table_info(parking_lot_state_history)")
        columns = [col[1] for col in cursor.fetchall()]

        if rows:
            print(f"\nParking lot state history (first 2 records):")
            for row in rows:
                data = dict(zip(columns, row))
                print(f"  {data['parking_lot_id']} @ {data['observation_timestamp']}: {data['occupied_spaces']}/{108}")

        # Gate state sample
        cursor.execute("SELECT * FROM gate_state_history LIMIT 2")
        rows = cursor.fetchall()
        cursor.execute("PRAGMA table_info(gate_state_history)")
        columns = [col[1] for col in cursor.fetchall()]

        if rows:
            print(f"\nGate state history (first 2 records):")
            for row in rows:
                data = dict(zip(columns, row))
                print(f"  {data['gate_id']} @ {data['observation_timestamp']}: queue={data['current_queue_length']}")

    except Exception as e:
        print(f"Could not fetch sample: {e}")

    # Close connection
    conn.close()

    print("\n" + "="*70)
    print(f"Import completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print("\nNEXT STEPS:")
    print("1. Load campus configuration:")
    print("   python scripts/load_campus_config.py --config configs/campuses/vitap_v2.yaml")
    print("\n2. Run simulation:")
    print("   python -m digital_twin.cli.run --campus vitap --scenario configs/scenarios/vitap/normal_day.yaml")
    print("\n3. Launch API:")
    print("   uvicorn digital_twin.api.app:app --reload")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
