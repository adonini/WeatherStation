from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import pymongo
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("../.env")

# MongoDB connection
host_ws_db = os.environ.get('DB_HOST', 'localhost')
port_ws_db = os.environ.get('DB_PORT')
uri_ws = f"mongodb://{host_ws_db}:{port_ws_db}"
dbName_ws = os.environ.get('DB_NAME')
collectionName_ws = os.environ.get('DB_COLL')

client_ws = pymongo.MongoClient(uri_ws)
db_ws = client_ws[dbName_ws]
collection_ws = db_ws[collectionName_ws]

# # Create indexes for Date and Time fields to improve query performance
# if not collection_ws.index_information().get("Date.value"):
#     collection_ws.create_index([("Date.value", pymongo.ASCENDING)])
# if not collection_ws.index_information().get("Time.value"):
#     collection_ws.create_index([("Time.value", pymongo.ASCENDING)])

# FastAPI app initialization
app = FastAPI()

# Define available weather parameters and their short names
PARAM_MAP = {
    "temp": "Air Temperature",
    "hum": "Relative Humidity",
    "pres": "Absolute Air Pressure",
    "abs_hum": "Absolute Humidity",
    "avg_wind": "Average Wind Speed",
    "mean_wind": "Mean Wind Speed",
    "wind_dir": "Mean Wind Direction",
    "gust": "Max Wind",
    "bright": "Brightness",
    "bright_lux": "Brightness lux",
    "dew_point": "Dew Point Temperature",
    "glob_rad": "Global Radiation",
    "heat_idx": "Heat Index Temperature",
    "wind_chill": "Wind Chill Temperature",
    "precip_status": "Precipitation Status",
    "precip_amt": "Precipitation Amount",
    "precip_int": "Precipitation Intensity",
    "precip_type": "Precipitation Type",
    "wind_10": "Mean 10 Wind Speed"
}

AVAILABLE_PARAMS = list(PARAM_MAP.keys()) + ["all"]


# Helper function to parse date/time strings
def parse_datetime(dt_str):
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.strptime(dt_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)


# Endpoint to list available parameters
@app.get("/parameters")
def get_available_parameters():
    """
    Endpoint to list available weather parameters.
    Returns a list of parameters as a JSON object.
    """
    return {"parameters": list(PARAM_MAP.keys())}


# Endpoint to retrieve weather data
class WeatherRequest(BaseModel):
    start: str
    end: Optional[str] = None
    params: List[str]
    output: Optional[str] = "weather_data.csv"


@app.post("/weather")
def get_weather_data(request: WeatherRequest):
    start_dt = parse_datetime(request.start)
    end_dt = parse_datetime(request.end) if request.end else start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    # MongoDB query with better filters to avoid duplicates
    query = {
        "$and": [
            {"Date.value": {"$gte": start_dt.strftime('%Y%m%d'), "$lte": end_dt.strftime('%Y%m%d')}},
            {"Time.value": {"$gte": start_dt.strftime('%H%M%S'), "$lte": end_dt.strftime('%H%M%S')}}
        ]
    }

    # Make sure to sort the query to avoid any unordered results
    results = collection_ws.find(query, sort=[("Date.value", pymongo.ASCENDING), ("Time.value", pymongo.ASCENDING)])
    result_count = collection_ws.count_documents(query)

    # Avoid duplicate entries by keeping track of seen datetime values
    seen_datetimes = set()
    weather_data = []

    for doc in results:
        date_str = doc["Date"]["value"]
        time_str = doc["Time"]["value"]
        datetime_str = f"{date_str} {time_str[:2]}:{time_str[2:4]}"
        reading_datetime = datetime.strptime(datetime_str, "%Y%m%d %H:%M").replace(tzinfo=timezone.utc)

        # Skip duplicates based on DateTime
        if reading_datetime in seen_datetimes:
            continue
        seen_datetimes.add(reading_datetime)

        entry = {"DateTime": reading_datetime.strftime("%Y-%m-%d %H:%M:%S")}

        for short_name, full_name in PARAM_MAP.items():
            if "all" in request.params or short_name in request.params:
                if full_name in doc:
                    entry[short_name] = round(float(doc[full_name]["value"]), 2)

        weather_data.append(entry)

    if not weather_data:
        raise HTTPException(status_code=404, detail="No data found for the given parameters and time range.")
    return weather_data


# Additional endpoint for API usage help
@app.get("/help")
def get_help():
    return {
        "message": "Welcome to the Weather Data API! Here are the available endpoints:\n"
                   "/parameters: Lists all available weather parameters.\n"
                   "/weather: Retrieve weather data within a specified date/time range using a POST request.\n\n"
                   "To retrieve weather data, use the following format:\n"
                   "POST /weather with a JSON body containing 'start', 'end', 'params', and 'output'.\n\n"
                   "Example:\n"
                   "POST /weather\n"
                   "Request body: {\n"
                   "  'start': '2025-03-25 00:00:00',\n"
                   "  'end': '2025-03-25 23:59:59',\n"
                   "  'params': ['temp', 'hum'],\n"
                   "  'output': 'weather_data.csv'\n"
                   "}"
    }
