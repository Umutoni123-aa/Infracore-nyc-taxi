# Infracore-nyc-taxi
# 🚕 NYC Taxi Explorer

Interactive dashboard analyzing 2.8 million NYC taxi trips from January 2024.

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
pip install Flask Flask-CORS pandas gunicorn

# Download data files to data/ folder:
# - yellow_tripdata_2024-01.parquet
# - taxi_zone_lookup.csv
# - taxi_zones.geojson

# Process data
python backend/clean_data.py
python backend/load_database.py

# Start server
python backend/api_server.py

# Open frontend/index.html in browser
```

## Key Statistics

- **2.8M trips** analyzed
- **$18.48** average fare
- **3.31 miles** average distance
- **15 minutes** average duration
- **11.5 mph** average speed
- **Manhattan** most popular borough

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/stats` | Summary statistics |
| `/api/boroughs` | Borough list |
| `/api/trips` | Trip data with filters |
| `/api/trips/by-borough` | Borough analytics |
| `/api/trips/by-hour` | Hourly patterns |

## Tech Stack

**Backend:** Flask, Pandas, SQLite  
**Frontend:** HTML, CSS, JavaScript, Chart.js

## Project Structure

```
Infracore-nyc-taxi/
├── backend/
│   ├── clean_data.py        # Data cleaning
│   ├── load_database.py     # Database setup
│   └── api_server.py        # Flask API
├── frontend/
│   └── index.html           # Dashboard
└── data/                    # Data files (ignored)
```

## 👥 Team              ## Emails

- Dedine Mukabucyana :  d.mukabucya@alustudent.com
- Milliam Mukamukiza :  m.mukamukiz@alustudent.com
- Nada Umutoni       :  u.nada@alustudent.com>

##  License

Educational project using NYC TLC open data.
