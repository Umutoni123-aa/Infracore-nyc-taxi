# Infracore-nyc-taxi

# 🚕 NYC Taxi Explorer

An interactive fullstack web application that explores 2.8 million NYC Yellow Taxi trips from January 2024. Built to uncover real patterns in how New York City moves — from rush hour surges to borough-level economic differences.

It processes raw NYC TLC taxi trip data, cleans and stores it in a relational database, and serves it through a REST API to an interactive frontend dashboard.

Video Walkthrough:
[]
Team participation sheet:
[https://docs.google.com/spreadsheets/d/18kW75lxI9qypNfLS9YEmKdMNFrf3Kbxuc84cB7COxuo/edit?gid=0#gid=0]
Documentation:
[https://docs.google.com/document/d/1qRC5_qiZFRpXds4WPGzhzCGR6XNvm_H7fYpCxO5y1Mw/edit?tab=t.0]

## Features

- **Interactive Charts** - Visualize trips by borough, hour, and day
- **Advanced Filters** - Filter by location, time, and day of week
- **Real-time Stats** - Fare, distance, duration, speed, and tip analytics
- **Top Routes** - Most popular pickup-dropoff combinations

## Quick Start

### Prerequisites

- Python 3.8+
- 1 GB free disk space

### Installation

```bash
# Clone repository
git clone https://github.com/Umutoni123-aa/Infracore-nyc-taxi.git
cd Infracore-nyc-taxi

# Install dependencies
pip install Flask Flask-CORS pandas gunicorn pyarrow

# Download data files to data/ folder:
# - yellow_tripdata_2024-01.parquet
# - taxi_zone_lookup.csv
# - taxi_zones.geojson
Download from: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

# Process data
python backend/clean_data.py
python backend/load_database.py

# Start server
python backend/api_server.py

# Open frontend/index.html in browser
```

Note: Make sure the API server is running before opening the dashboard!

## Custom Algorithm

We implemented a custom Insertion Sort algorithm to rank NYC taxi zones by a composite mobility score — without using any built-in sort functions.

Mobility Score Formula
score = (trip_count / 1000) + (avg_fare × 0.5) + (avg_distance × 2)
Each component captures a different dimension:

1. trip_count / 1000 — how busy the zone is (normalized)
2. avg_fare × 0.5 — economic activity in the zone
3. avg_distance × 2 — how far people travel from this zone

## Key Statistics

- **2.8M trips** analyzed
- **$18.48** average fare
- **3.31 miles** average distance
- **15 minutes** average duration
- **11.5 mph** average speed
- **Manhattan** most popular borough

## API Endpoints

| Endpoint                | Description            |
| ----------------------- | ---------------------- |
| `/api/stats`            | Summary statistics     |
| `/api/boroughs`         | Borough list           |
| `/api/trips`            | Trip data with filters |
| `/api/trips/by-borough` | Borough analytics      |
| `/api/trips/by-hour`    | Hourly patterns        |

## Tech Stack

**Backend:** Flask, Pandas, SQLite  
**Frontend:** HTML, CSS, JavaScript, Chart.js

## Project Structure

```
Infracore-nyc-taxi/
├── backend/
│   ├── algorithm.py         # Custom zone ranking algorithm
│   ├── api_server.py        # Flask API
│   ├── clean_data.py        # Data cleaning
│   └── load_database.py     # Database setup
├── frontend/
│   └── index.html           # Dashboard
├── .gitignore               # Excludes large data files
└── README.md                # This file

## 👥 Team              ## Emails

- Dedine Mukabucyana :  d.mukabucya@alustudent.com
- Milliam Mukamukiza :  m.mukamukiz@alustudent.com
- Nada Umutoni       :  u.nada@alustudent.com

##  License

Educational project using NYC TLC open data. Data sourced from the
(https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
```
