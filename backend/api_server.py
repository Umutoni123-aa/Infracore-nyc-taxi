# Each route queries the database and returns JSON data

import sqlite3
import json
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

# Create the Flask app
app = Flask(__name__)

# Allow the frontend to talk to this backend
# Without this, the browser would block the requests
CORS(app)

# Path to our database file
DB_PATH = 'data/nyc_taxi.db'


def get_db():
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# --------------------------------------------------
# ROUTE 1: ROOT - shows all available endpoints
# Visit: http://localhost:5000/
# --------------------------------------------------
@app.route('/')
def index():
    return jsonify({
        "message": "NYC Taxi Explorer API",
        "version": "1.0.0",
        "endpoints": [
            "/api/stats",
            "/api/boroughs",
            "/api/trips",
            "/api/trips/by-borough",
            "/api/trips/by-hour",
            "/api/trips/by-day",
            "/api/zones",
            "/api/trips/top-routes"
        ]
    })


# --------------------------------------------------
# ROUTE 2: SUMMARY STATS
# --------------------------------------------------
@app.route('/api/stats')
def get_stats():
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT stat_name, stat_value FROM summary_stats')
        rows = cursor.fetchall()
        conn.close()

        # Convert values to numbers where possible
        stats = {}
        for row in rows:
            try:
                stats[row['stat_name']] = float(row['stat_value'])
            except ValueError:
                stats[row['stat_name']] = row['stat_value']

        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# ROUTE 3: BOROUGHS
# Returns a list of all NYC boroughs in the data
# --------------------------------------------------
@app.route('/api/boroughs')
def get_boroughs():
    try:
        conn   = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT pickup_borough as borough
            FROM trips
            WHERE pickup_borough IS NOT NULL
            AND pickup_borough != "Unknown"
            ORDER BY pickup_borough
        ''')
        rows = cursor.fetchall()
        conn.close()

        boroughs = [row['borough'] for row in rows]
        return jsonify({"success": True, "data": boroughs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# ROUTE 4: TRIPS WITH FILTERS
# --------------------------------------------------
@app.route('/api/trips')
def get_trips():
    try:
        # Read optional filter parameters from the URL
        borough     = request.args.get('borough', None)
        time_of_day = request.args.get('time_of_day', None)
        day         = request.args.get('day', None)
        limit       = int(request.args.get('limit', 100))
        offset      = int(request.args.get('offset', 0))

        # Build the query depending on which filters are active
        query  = '''
            SELECT
                pickup_borough, dropoff_borough,
                pickup_zone, dropoff_zone,
                fare_amount, trip_distance,
                trip_duration_mins, avg_speed_mph,
                tip_percentage, time_of_day,
                day_of_week, hour_of_day,
                passenger_count, total_amount
            FROM trips
            WHERE 1=1
        '''
        params = []

        if borough:
            query += ' AND pickup_borough = ?'
            params.append(borough)
        if time_of_day:
            query += ' AND time_of_day = ?'
            params.append(time_of_day)
        if day:
            query += ' AND day_of_week = ?'
            params.append(day)

        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Count total matching rows 
        count_query  = 'SELECT COUNT(*) as total FROM trips WHERE 1=1'
        count_params = []
        if borough:
            count_query += ' AND pickup_borough = ?'
            count_params.append(borough)
        if time_of_day:
            count_query += ' AND time_of_day = ?'
            count_params.append(time_of_day)
        if day:
            count_query += ' AND day_of_week = ?'
            count_params.append(day)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        conn.close()

        trips = [dict(row) for row in rows]
        return jsonify({
            "success": True,
            "total":   total,
            "limit":   limit,
            "offset":  offset,
            "data":    trips
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# ROUTE 5: TRIPS BY BOROUGH
# --------------------------------------------------
@app.route('/api/trips/by-borough')
def trips_by_borough():
    try:
        conn   = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                pickup_borough                       as borough,
                COUNT(*)                             as total_trips,
                ROUND(AVG(fare_amount), 2)           as avg_fare,
                ROUND(AVG(trip_distance), 2)         as avg_distance,
                ROUND(AVG(trip_duration_mins), 2)    as avg_duration,
                ROUND(AVG(tip_percentage), 2)        as avg_tip_pct
            FROM trips
            WHERE pickup_borough IS NOT NULL
            AND pickup_borough != "Unknown"
            GROUP BY pickup_borough
            ORDER BY total_trips DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        data = [dict(row) for row in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# ROUTE 6: TRIPS BY HOUR
# Returns how many trips happened each hour of the day
# --------------------------------------------------
@app.route('/api/trips/by-hour')
def trips_by_hour():
    try:
        borough = request.args.get('borough', None)

        query  = '''
            SELECT
                hour_of_day,
                COUNT(*)                          as total_trips,
                ROUND(AVG(fare_amount), 2)        as avg_fare,
                ROUND(AVG(trip_duration_mins), 2) as avg_duration
            FROM trips
            WHERE 1=1
        '''
        params = []
        if borough:
            query += ' AND pickup_borough = ?'
            params.append(borough)

        query += ' GROUP BY hour_of_day ORDER BY hour_of_day'

        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        data = [dict(row) for row in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# ROUTE 7: TRIPS BY DAY OF WEEK
# Returns how many trips happened on each day of the week
# --------------------------------------------------
@app.route('/api/trips/by-day')
def trips_by_day():
    try:
        conn   = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                day_of_week,
                COUNT(*)                         as total_trips,
                ROUND(AVG(fare_amount), 2)       as avg_fare,
                ROUND(AVG(trip_distance), 2)     as avg_distance,
                is_weekend
            FROM trips
            GROUP BY day_of_week
            ORDER BY total_trips DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        data = [dict(row) for row in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# ROUTE 8: ZONES
# --------------------------------------------------
@app.route('/api/zones')
def get_zones():
    try:
        borough = request.args.get('borough', None)

        query  = 'SELECT * FROM zones WHERE 1=1'
        params = []
        if borough:
            query += ' AND borough = ?'
            params.append(borough)
        query += ' ORDER BY borough, zone'

        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        data = [dict(row) for row in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# ROUTE 9: TOP ROUTES
# --------------------------------------------------
@app.route('/api/trips/top-routes')
def top_routes():
    try:
        limit  = int(request.args.get('limit', 10))
        conn   = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                pickup_zone,
                dropoff_zone,
                pickup_borough,
                dropoff_borough,
                COUNT(*)                         as total_trips,
                ROUND(AVG(fare_amount), 2)       as avg_fare,
                ROUND(AVG(trip_distance), 2)     as avg_distance
            FROM trips
            WHERE pickup_zone  IS NOT NULL
            AND   dropoff_zone IS NOT NULL
            GROUP BY pickup_zone, dropoff_zone
            ORDER BY total_trips DESC
            LIMIT ?
        ''', [limit])
        rows = cursor.fetchall()
        conn.close()

        data = [dict(row) for row in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
# --------------------------------------------------
# ROUTE: ZONE RANKINGS (Custom Algorithm)
# --------------------------------------------------
@app.route('/api/zone-rankings')
def zone_rankings():
    try:
        from algorithm import rank_zones
        ranked = rank_zones()
        return jsonify({"success": True, "data": ranked[:20]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# START THE SERVER
# --------------------------------------------------
if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run: python backend/load_database.py first!")
        exit(1)

    print("=" * 60)
    print("NYC TAXI EXPLORER API SERVER")
    print("=" * 60)
    print(f"  Database : {DB_PATH}")
    print(f"  URL      : http://localhost:5000")
    print(f"  Tip      : Press CTRL+C to stop the server")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)