# ========================
# STEP 1: CLEAN THE RAW TAXI DATA

# What this file does:
# - Loads the raw NYC taxi trip data
# - Removes bad or impossible records
# - Creates new useful columns from existing ones
# - Saves the cleaned data for the database
# ==========================   

import pandas as pd
import os
import json
from datetime import datetime

print("=" * 50)
print("STARTING DATA CLEANING...")
print("=" * 50)

# LOAD THE RAW FILES
# We need 3 files: trip data, zone names, zone map
print("\nChecking all required files exist...")

files = [
    'data/yellow_tripdata_2024-01.parquet',
    'data/taxi_zone_lookup.csv',
    'data/taxi_zones.geojson'
]

for f in files:
    if os.path.exists(f):
        size = os.path.getsize(f) / (1024 * 1024)
        print(f"  FOUND: {f} ({size:.1f} MB)")
    else:
        print(f"  MISSING: {f} - please download this file!")

# Load the main trip data
print("\nLoading taxi trips...")
trips = pd.read_parquet('data/yellow_tripdata_2024-01.parquet')
original_count = len(trips)
print(f"  Loaded {original_count:,} raw trips")

# Load zone lookup (maps location IDs to borough names)
print("Loading zone names...")
zones = pd.read_csv('data/taxi_zone_lookup.csv')
print(f"  Loaded {len(zones):,} zones")

# Load GeoJSON (map boundaries - used for map visualisation)
print("Loading map boundaries...")
try:
    with open('data/taxi_zones.geojson', 'r') as f:
        geo_zones = json.load(f)
    print(f"  Loaded GeoJSON successfully")
except Exception as e:
    print(f"  GeoJSON warning: {e}")
    geo_zones = None

# SHOW WHAT THE RAW DATA LOOKS LIKE

print("\n" + "=" * 60)
print("RAW DATA OVERVIEW")
print("=" * 60)

print(f"\nColumns in the dataset:")
for col in trips.columns.tolist():
    print(f"  - {col}")

print(f"\nSize: {trips.shape[0]:,} rows x {trips.shape[1]} columns")

print(f"\nMissing values found:")
missing = trips.isnull().sum()
for col, count in missing[missing > 0].items():
    print(f"  - {col}: {count:,} missing")

print(f"\nBasic stats before cleaning:")
for col in ['fare_amount', 'trip_distance', 'passenger_count']:
    if col in trips.columns:
        print(f"  {col}: min={trips[col].min()}, max={trips[col].max()}, avg={trips[col].mean():.2f}")


# CLEANING LOG

cleaning_log = {
    "date": str(datetime.now()),
    "original_rows": original_count,
    "removed": {}
}

print("\n" + "=" * 60)
print("CLEANING THE DATA")
print("=" * 60)

# STEP 1: RENAME COLUMNS
# The raw column names are confusing, we rename them

print("\nStep 1: Renaming confusing column names...")
rename_map = {}
if 'tpep_pickup_datetime'  in trips.columns:
    rename_map['tpep_pickup_datetime']  = 'pickup_datetime'
if 'tpep_dropoff_datetime' in trips.columns:
    rename_map['tpep_dropoff_datetime'] = 'dropoff_datetime'
if 'VendorID'              in trips.columns:
    rename_map['VendorID']              = 'vendor_id'
if 'RatecodeID'            in trips.columns:
    rename_map['RatecodeID']            = 'rate_code_id'
if 'PULocationID'          in trips.columns:
    rename_map['PULocationID']          = 'pickup_location_id'
if 'DOLocationID'          in trips.columns:
    rename_map['DOLocationID']          = 'dropoff_location_id'

trips = trips.rename(columns=rename_map)
print(f"  Renamed {len(rename_map)} columns to friendlier names")


# STEP 2: FIX DATA TYPES

print("\nStep 2: Fixing data types...")
trips['pickup_datetime']  = pd.to_datetime(trips['pickup_datetime'],  errors='coerce')
trips['dropoff_datetime'] = pd.to_datetime(trips['dropoff_datetime'], errors='coerce')

for col in ['fare_amount', 'trip_distance', 'passenger_count',
            'tip_amount', 'total_amount',
            'pickup_location_id', 'dropoff_location_id']:
    if col in trips.columns:
        trips[col] = pd.to_numeric(trips[col], errors='coerce')

print("  All data types fixed")


# STEP 3: REMOVE DUPLICATES
# Some trips appear more than once - we keep only one

print("\nStep 3: Removing duplicate trips...")
before = len(trips)
trips  = trips.drop_duplicates()
removed = before - len(trips)
cleaning_log["removed"]["duplicates"] = int(removed)
print(f"  Removed {removed:,} duplicate rows")

# STEP 4: HANDLE MISSING VALUES
# Rows missing important info are removed

print("\nStep 4: Removing rows with missing important values...")
trips['passenger_count'] = trips['passenger_count'].fillna(1)

before = len(trips)
trips  = trips.dropna(subset=[
    'pickup_datetime', 'dropoff_datetime',
    'pickup_location_id', 'dropoff_location_id',
    'fare_amount', 'trip_distance'
])
removed = before - len(trips)
cleaning_log["removed"]["missing_critical"] = int(removed)
print(f"  Removed {removed:,} rows with missing data")

# STEP 5: REMOVE IMPOSSIBLE VALUES
# Real NYC taxi trips cannot have negative fares, zero distance, or dropoff before pickup time

print("\nStep 5: Removing impossible or suspicious trips...")

def remove_bad(df, mask, label, log):
    # Count how many rows match the bad condition
    count = int(mask.sum())
    log["removed"][label] = count
    print(f"  Removed {count:,} rows - reason: {label}")
    return df[~mask]  # Return only the good rows

trips = remove_bad(trips, trips['fare_amount'] <= 0,
    "fare is zero or negative", cleaning_log)

trips = remove_bad(trips, trips['trip_distance'] <= 0,
    "distance is zero or negative", cleaning_log)

trips = remove_bad(trips, trips['trip_distance'] > 200,
    "distance over 200 miles (impossible in NYC)", cleaning_log)

trips = remove_bad(trips, trips['fare_amount'] > 1000,
    "fare over $1000 (suspicious)", cleaning_log)

trips = remove_bad(trips,
    (trips['passenger_count'] <= 0) | (trips['passenger_count'] > 6),
    "passenger count invalid (must be 1-6)", cleaning_log)

trips = remove_bad(trips,
    trips['dropoff_datetime'] <= trips['pickup_datetime'],
    "dropoff time is before or same as pickup", cleaning_log)

# Calculate duration to check for more outliers
duration = (trips['dropoff_datetime'] - trips['pickup_datetime']).dt.total_seconds()

trips = remove_bad(trips, duration > 86400,
    "trip longer than 24 hours", cleaning_log)

duration = (trips['dropoff_datetime'] - trips['pickup_datetime']).dt.total_seconds()

trips = remove_bad(trips, duration < 60,
    "trip shorter than 1 minute", cleaning_log)

print(f"\n  Rows remaining after cleaning: {len(trips):,}")


# STEP 6: CREATE NEW USEFUL COLUMNS (Feature Engineering)
# These give us deeper insights into the data

print("\n" + "=" * 60)
print("CREATING NEW FEATURES FROM EXISTING DATA")
print("=" * 60)

# New column 1: How long was the trip in minutes?
trips['trip_duration_mins'] = (
    (trips['dropoff_datetime'] - trips['pickup_datetime'])
    .dt.total_seconds() / 60
).round(2)
print("\n  Created: trip_duration_mins")
print("  Why: Lets us analyse how long trips take in different areas")

# New column 2: How fast was the taxi going on average?
trips['avg_speed_mph'] = (
    trips['trip_distance'] / (trips['trip_duration_mins'] / 60)
).round(2)
# Remove trips with impossible speeds
trips = trips[trips['avg_speed_mph'].between(1, 150)]
print("\n  Created: avg_speed_mph")
print("  Why: Low speed means heavy traffic - useful for city planning")

# New column 3: What percentage of the fare was tipped?
trips['tip_percentage'] = (
    (trips['tip_amount'] / trips['fare_amount']) * 100
).round(2).clip(0, 100).fillna(0)
print("\n  Created: tip_percentage")
print("  Why: Shows tipping patterns across different boroughs")

# New column 4: What time period was the pickup?
def get_time_of_day(hour):
    # Group hours into meaningful time periods
    if   5  <= hour < 9:  return 'Morning Rush'
    elif 9  <= hour < 12: return 'Mid Morning'
    elif 12 <= hour < 17: return 'Afternoon'
    elif 17 <= hour < 20: return 'Evening Rush'
    elif 20 <= hour < 24: return 'Night'
    else:                 return 'Late Night'

trips['hour_of_day'] = trips['pickup_datetime'].dt.hour
trips['time_of_day'] = trips['hour_of_day'].apply(get_time_of_day)
print("\n  Created: hour_of_day and time_of_day")
print("  Why: Identifies when taxis are busiest during the day")

# New column 5: What day of the week was the trip?
trips['day_of_week'] = trips['pickup_datetime'].dt.day_name()
trips['is_weekend']  = trips['pickup_datetime'].dt.dayofweek.isin([5, 6])
print("\n  Created: day_of_week and is_weekend")
print("  Why: Weekend trips behave very differently to weekday trips")

# STEP 7: ADD BOROUGH AND ZONE NAMES

print("\n" + "=" * 60)
print("ADDING BOROUGH AND ZONE NAMES")
print("=" * 60)

zones = zones.rename(columns={
    'LocationID':   'location_id',
    'Borough':      'borough',
    'Zone':         'zone',
    'service_zone': 'service_zone'
})

# Add pickup borough and zone name
trips = trips.merge(
    zones[['location_id', 'borough', 'zone']],
    left_on='pickup_location_id',
    right_on='location_id',
    how='left'
).rename(columns={'borough': 'pickup_borough', 'zone': 'pickup_zone'})

if 'location_id' in trips.columns:
    trips.drop(columns=['location_id'], inplace=True)

# Add dropoff borough and zone name
trips = trips.merge(
    zones[['location_id', 'borough', 'zone']],
    left_on='dropoff_location_id',
    right_on='location_id',
    how='left'
).rename(columns={'borough': 'dropoff_borough', 'zone': 'dropoff_zone'})

if 'location_id' in trips.columns:
    trips.drop(columns=['location_id'], inplace=True)

print("\n  Borough and zone names added successfully")
print(f"  Boroughs found: {trips['pickup_borough'].unique()[:5].tolist()}")

# STEP 8: SAVE THE CLEANED DATA
# Save in different formats for different uses

print("\n" + "=" * 60)
print("SAVING CLEANED DATA")
print("=" * 60)

os.makedirs('data/cleaned', exist_ok=True)

# Save full cleaned dataset as parquet (fast format for database loading)
trips.to_parquet('data/cleaned/trips_clean.parquet', index=False)
print("\n  Saved full dataset: data/cleaned/trips_clean.parquet")

# Save cleaned zone names
zones.to_csv('data/cleaned/zones_clean.csv', index=False)
print("  Saved zones: data/cleaned/zones_clean.csv")

# Save a small sample for quick testing
trips.head(10000).to_csv('data/cleaned/trips_sample.csv', index=False)
print("  Saved sample (10,000 rows): data/cleaned/trips_sample.csv")

# Save cleaning log so we can report what was removed and why
os.makedirs('docs', exist_ok=True)
final_count = len(trips)
cleaning_log["final_rows"]      = final_count
cleaning_log["percentage_kept"] = round((final_count / original_count) * 100, 2)

with open('docs/cleaning_log.json', 'w') as f:
    json.dump(cleaning_log, f, indent=4)
print("  Saved cleaning log: docs/cleaning_log.json")

# --------------------------------------------------
# FINAL SUMMARY
# --------------------------------------------------
print("\n" + "=" * 50)
print("CLEANING COMPLETE!")
print("=" * 50)
print(f"  Started with : {original_count:,} raw trips")
print(f"  Ended with   : {final_count:,} clean trips")
print(f"  Removed      : {original_count - final_count:,} bad records")
print(f"  Data kept    : {cleaning_log['percentage_kept']}%")
print("\n  New columns created:")
print("  1. trip_duration_mins  - how long the trip took")
print("  2. avg_speed_mph       - average speed of the taxi")
print("  3. tip_percentage      - tip as a % of the fare")
print("  4. time_of_day         - morning rush, evening rush etc.")
print("  5. day_of_week         - Monday, Tuesday etc.")
print("=" * 50)
print("NEXT STEP: py backend/load_database.py")
print("=" * 50)