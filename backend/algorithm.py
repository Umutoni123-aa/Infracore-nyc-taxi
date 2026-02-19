# ==================================================
# CUSTOM ALGORITHM: Zone Mobility Ranking
# File: backend/algorithm.py
# What this does:
# - Ranks NYC taxi zones by a custom mobility score
# - Uses insertion sort (no built-in sort() used!)
#
# Time complexity:  O(n²)
# Space complexity: O(1)
# ==================================================

import sqlite3
import os
import sys

# Fix database path to work from any directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'nyc_taxi.db')

def get_zone_stats():
    """
    Fetch trip count, avg fare and avg distance per zone from database.
    
    Returns:
        list: List of dictionaries with zone statistics
    """
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ ERROR: Database not found at {DB_PATH}")
        print(f"\nPlease run this first:")
        print(f"  py backend/lead_databasi.py")
        sys.exit(1)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                pickup_zone,
                pickup_borough,
                COUNT(*) as trip_count,
                AVG(fare_amount) as avg_fare,
                AVG(trip_distance) as avg_distance
            FROM trips
            WHERE pickup_zone IS NOT NULL
            GROUP BY pickup_zone
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        print(f"✅ Loaded {len(rows)} zones from database")
        
        return [
            {
                "zone": r[0], 
                "borough": r[1], 
                "trip_count": r[2],
                "avg_fare": round(r[3], 2), 
                "avg_distance": round(r[4], 2)
            }
            for r in rows
        ]
    
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

def mobility_score(zone):
    """
    Calculate a mobility score for each zone.
    
    Formula: (trip_count / 1000) + (avg_fare * 0.5) + (avg_distance * 2)
    
    Why this formula:
    - trip_count / 1000  → Normalizes trip volume (how busy the zone is)
    - avg_fare * 0.5     → Economic activity indicator
    - avg_distance * 2   → How far people travel from this zone (connectivity)
    
    Args:
        zone (dict): Zone statistics dictionary
        
    Returns:
        float: Calculated mobility score
    """
    return round(
        (zone["trip_count"] / 1000) +
        (zone["avg_fare"] * 0.5) +
        (zone["avg_distance"] * 2), 
        2
    )

def insertion_sort(zones):
    """
    Custom insertion sort implementation — NO built-in sort() used!
    Sorts zones in DESCENDING order by score (highest first).
    
    Pseudo-code:
    ------------
    FOR i FROM 1 TO length(zones):
        current = zones[i]
        j = i - 1
        WHILE j >= 0 AND zones[j].score < current.score:
            zones[j+1] = zones[j]
            j = j - 1
        zones[j+1] = current
    
    Time complexity:  O(n²) - nested loops
    Space complexity: O(1)  - sorts in place, no extra arrays
    
    Why insertion sort:
    - Simple to implement from scratch
    - Good for small datasets
    - Demonstrates algorithm understanding without libraries
    
    Args:
        zones (list): List of zone dictionaries with "score" key
        
    Returns:
        list: Sorted list (in-place, but returned for clarity)
    """
    n = len(zones)
    
    for i in range(1, n):
        current = zones[i]
        j = i - 1
        
        # Move elements greater than current one position ahead
        while j >= 0 and zones[j]["score"] < current["score"]:
            zones[j + 1] = zones[j]
            j -= 1
        
        zones[j + 1] = current
    
    return zones

def rank_zones():
    """
    Main function to rank zones by mobility score.
    
    Process:
    1. Get zone statistics from database
    2. Calculate mobility score for each zone
    3. Sort using custom insertion sort
    4. Assign ranks
    
    Returns:
        list: Ranked zones with scores and ranks
    """
    print("\n" + "=" * 60)
    print("ZONE MOBILITY RANKING ALGORITHM")
    print("=" * 60)
    
    # Step 1: Get raw zone data
    print("\n📊 Step 1: Fetching zone statistics...")
    zones = get_zone_stats()
    
    # Step 2: Calculate mobility scores
    print("\n⚙️  Step 2: Calculating mobility scores...")
    for z in zones:
        z["score"] = mobility_score(z)
    
    print(f"   ✅ Scores calculated for {len(zones)} zones")
    
    # Step 3: Sort using custom algorithm
    print("\n🔄 Step 3: Sorting zones (custom insertion sort)...")
    sorted_zones = insertion_sort(zones)
    print(f"   ✅ Zones sorted by score")
    
    # Step 4: Assign ranks
    print("\n🏆 Step 4: Assigning ranks...")
    for i, z in enumerate(sorted_zones):
        z["rank"] = i + 1
    
    print(f"   ✅ Ranks assigned (1 to {len(sorted_zones)})")
    
    return sorted_zones

def print_results(ranked_zones, top_n=15):
    """
    Print formatted results.
    
    Args:
        ranked_zones (list): List of ranked zones
        top_n (int): Number of top zones to display
    """
    print("\n" + "=" * 60)
    print(f"TOP {top_n} ZONES BY MOBILITY SCORE")
    print("=" * 60)
    print(f"{'Rank':<6} {'Zone':<35} {'Borough':<15} {'Score':<8}")
    print("-" * 60)
    
    for z in ranked_zones[:top_n]:
        print(f"{z['rank']:<6} {z['zone'][:34]:<35} {z['borough']:<15} {z['score']:<8}")
    
    print("\n" + "=" * 60)
    print("DETAILED STATS FOR TOP 5")
    print("=" * 60)
    
    for z in ranked_zones[:5]:
        print(f"\n{z['rank']}. {z['zone']} ({z['borough']})")
        print(f"   Mobility Score  : {z['score']}")
        print(f"   Total Trips     : {z['trip_count']:,}")
        print(f"   Avg Fare        : ${z['avg_fare']}")
        print(f"   Avg Distance    : {z['avg_distance']} miles")

def save_results(ranked_zones, output_file="docs/algorithm_results.txt"):
    """
    Save results to a text file for documentation.
    
    Args:
        ranked_zones (list): List of ranked zones
        output_file (str): Output file path
    """
    output_path = os.path.join(PROJECT_ROOT, output_file)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("NYC TAXI ZONE MOBILITY RANKING RESULTS\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("ALGORITHM: Custom Insertion Sort\n")
        f.write("TIME COMPLEXITY: O(n²)\n")
        f.write("SPACE COMPLEXITY: O(1)\n\n")
        
        f.write("MOBILITY SCORE FORMULA:\n")
        f.write("  (trip_count / 1000) + (avg_fare * 0.5) + (avg_distance * 2)\n\n")
        
        f.write("=" * 60 + "\n")
        f.write(f"ALL {len(ranked_zones)} ZONES RANKED\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"{'Rank':<6} {'Zone':<40} {'Borough':<15} {'Score':<10} {'Trips':<12}\n")
        f.write("-" * 90 + "\n")
        
        for z in ranked_zones:
            f.write(f"{z['rank']:<6} {z['zone'][:39]:<40} {z['borough']:<15} "
                   f"{z['score']:<10} {z['trip_count']:<12,}\n")
    
    print(f"\n💾 Results saved to: {output_path}")

if __name__ == "__main__":
    try:
        # Run the ranking algorithm
        ranked = rank_zones()
        
        # Print results to console
        print_results(ranked, top_n=15)
        
        # Save to file
        save_results(ranked)
        
        print("\n✅ Algorithm completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Algorithm interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
