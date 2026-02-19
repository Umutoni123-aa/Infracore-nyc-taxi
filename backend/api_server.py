#!/usr/bin/env python3
# ==================================================
# NYC TAXI API SERVER
# File: backend/api_server.py
# Run: python backend/api_server.py
# ==================================================

import sqlite3
import json
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = 'data/nyc_taxi.db'


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def build_filter_clause(borough=None, time_of_day=None, day=None):
    """Returns (where_clause_string, params_list)."""
    clause = ' WHERE 1=1'
    params = []
    if borough:
        clause += ' AND pickup_borough = ?'
        params.append(borough)
    if time_of_day:
        clause += ' AND time_of_day = ?'
        params.append(time_of_day)
    if day:
        clause += ' AND day_of_week = ?'
        params.append(day)
    return clause, params


def bubble_sort_boroughs(data):
    n = len(data)
    for i in range(n):
        for j in range(n - 1 - i):
            if data[j]['total_trips'] < data[j + 1]['total_trips']:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data


# --------------------------------------------------
# ROOT
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
            "/api/trips/top-routes",
            "/api/zones"
        ]
    })


# --------------------------------------------------
# SUMMARY STATS
# --------------------------------------------------
@app.route('/api/stats')
def get_stats():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT stat_name, stat_value FROM summary_stats')
        rows = cursor.fetchall()
        conn.close()

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
# BOROUGHS
# --------------------------------------------------
@app.route('/api/boroughs')
def get_boroughs():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT pickup_borough AS borough
            FROM trips
            WHERE pickup_borough IS NOT NULL
            AND pickup_borough != "Unknown"
            ORDER BY pickup_borough
        ''')
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "data": [r['borough'] for r in rows]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# TRIPS WITH FILTERS
# --------------------------------------------------
@app.route('/api/trips')
def get_trips():
    try:
        borough = request.args.get('borough', None)
        time_of_day = request.args.get('time_of_day', None)
        day = request.args.get('day', None)
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        where, params = build_filter_clause(borough, time_of_day, day)

        query = f'''
            SELECT
                pickup_borough, dropoff_borough,
                pickup_zone, dropoff_zone,
                fare_amount, trip_distance,
                trip_duration_mins, avg_speed_mph,
                tip_percentage, time_of_day,
                day_of_week, hour_of_day,
                passenger_count, total_amount
            FROM trips
            {where}
            LIMIT ? OFFSET ?
        '''
        params_with_page = params + [limit, offset]
        count_query = f'SELECT COUNT(*) AS total FROM trips {where}'

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params_with_page)
        rows = cursor.fetchall()

        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        conn.close()

        return jsonify({
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# TRIPS BY BOROUGH
# --------------------------------------------------
@app.route('/api/trips/by-borough')
def trips_by_borough():
    try:
        borough = request.args.get('borough', None)
        time_of_day = request.args.get('time_of_day', None)
        day = request.args.get('day', None)

        where, params = build_filter_clause(borough, time_of_day, day)
        where += ' AND pickup_borough IS NOT NULL AND pickup_borough != "Unknown"'

        query = f'''
            SELECT
                pickup_borough AS borough,
                COUNT(*) AS total_trips,
                ROUND(AVG(fare_amount), 2) AS avg_fare,
                ROUND(AVG(trip_distance), 2) AS avg_distance,
                ROUND(AVG(trip_duration_mins), 2) AS avg_duration,
                ROUND(AVG(tip_percentage), 2) AS avg_tip_pct
            FROM trips
            {where}
            GROUP BY pickup_borough
            ORDER BY total_trips DESC
        '''

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        data = bubble_sort_boroughs([dict(r) for r in rows])
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# TRIPS BY HOUR
# --------------------------------------------------
@app.route('/api/trips/by-hour')
def trips_by_hour():
    try:
        borough = request.args.get('borough', None)
        time_of_day = request.args.get('time_of_day', None)
        day = request.args.get('day', None)

        where, params = build_filter_clause(borough, time_of_day, day)

        query = f'''
            SELECT
                hour_of_day,
                COUNT(*) AS total_trips,
                ROUND(AVG(fare_amount), 2) AS avg_fare,
                ROUND(AVG(trip_duration_mins), 2) AS avg_duration
            FROM trips
            {where}
            GROUP BY hour_of_day
            ORDER BY hour_of_day
        '''

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return jsonify({"success": True, "data": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# TRIPS BY DAY
# --------------------------------------------------
@app.route('/api/trips/by-day')
def trips_by_day():
    try:
        borough = request.args.get('borough', None)
        time_of_day = request.args.get('time_of_day', None)
        day = request.args.get('day', None)

        where, params = build_filter_clause(borough, time_of_day, day)

        query = f'''
            SELECT
                day_of_week,
                COUNT(*) AS total_trips,
                ROUND(AVG(fare_amount), 2) AS avg_fare,
                ROUND(AVG(trip_distance), 2) AS avg_distance,
                MAX(is_weekend) AS is_weekend
            FROM trips
            {where}
            GROUP BY day_of_week
            ORDER BY total_trips DESC
        '''

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return jsonify({"success": True, "data": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# TOP ROUTES
# --------------------------------------------------
@app.route('/api/trips/top-routes')
def top_routes():
    try:
        borough = request.args.get('borough', None)
        time_of_day = request.args.get('time_of_day', None)
        day = request.args.get('day', None)
        limit = int(request.args.get('limit', 10))

        where, params = build_filter_clause(borough, time_of_day, day)
        where += ' AND pickup_zone IS NOT NULL AND dropoff_zone IS NOT NULL'

        query = f'''
            SELECT
                pickup_zone,
                dropoff_zone,
                pickup_borough,
                dropoff_borough,
                COUNT(*) AS total_trips,
                ROUND(AVG(fare_amount), 2) AS avg_fare,
                ROUND(AVG(trip_distance), 2) AS avg_distance
            FROM trips
            {where}
            GROUP BY pickup_zone, dropoff_zone
            ORDER BY total_trips DESC
            LIMIT ?
        '''
        params.append(limit)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return jsonify({"success": True, "data": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# ZONES
# --------------------------------------------------
@app.route('/api/zones')
def get_zones():
    try:
        borough = request.args.get('borough', None)
        query = 'SELECT * FROM zones WHERE 1=1'
        params = []
        if borough:
            query += ' AND borough = ?'
            params.append(borough)
        query += ' ORDER BY borough, zone'

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return jsonify({"success": True, "data": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --------------------------------------------------
# RUN
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
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)