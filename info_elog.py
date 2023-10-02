from pymongo import MongoClient
from datetime import datetime, timedelta
import pymongo


#  connection to WS mongo
uri_ws = 'mongodb://tcs05-int:27010/'
#uri_ws = 'mongodb://localhost:27010/'
dbName_ws = 'WS'
collectionName_ws = 'Readings'

client_ws = pymongo.MongoClient(uri_ws)
db_ws = client_ws[dbName_ws]
collection_ws = db_ws[collectionName_ws]

#  connection to caco mongo
uri_caco = 'mongodb://lst101-int:27018/'
#uri_caco = 'mongodb://localhost:27018/'
dbName_caco = 'CACO'
collectionName_tib = 'TIB_min'
collectionName_clusco = 'CLUSCO_min'
collectionName_evb = 'EVB_min'

client_caco = MongoClient(uri_caco)
db_caco = client_caco[dbName_caco]
collection_tib = db_caco[collectionName_tib]
collection_clusco = db_caco[collectionName_clusco]
collection_evb = db_caco[collectionName_evb]

current_datetime = datetime.utcnow()
current_time = current_datetime.strftime("%H:%M:%S")
#print(current_datetime)

######## WEATHER SECTION ############
#find the most recent doc
most_recent_doc = collection_ws.find_one({}, sort=[('_id', pymongo.DESCENDING)])
# Extract date and time values from the document
date_str = most_recent_doc['Date']['value']
time_str = most_recent_doc['Time']['value']

datetime_str = f"{date_str} {time_str[:2]}:{time_str[2:4]}"
#print(datetime_str)
reading_datetime = datetime.strptime(datetime_str, '%Y%m%d %H:%M')

# Check that the last entry is not older than 1 minute. Times are in UTC
time_difference_ws = (current_datetime - reading_datetime).total_seconds()

if time_difference_ws <= 60:
    relative_humidity = round(float(most_recent_doc['Relative Humidity']['value']), 2)
    air_temperature = round(float(most_recent_doc['Air Temperature']['value']), 2)
    max_wind = round(float(most_recent_doc['Max Wind']['value']), 2)
    mean_wind_speed = round(float(most_recent_doc['Mean Wind Speed']['value']), 2)

    # Create the weather string
    weather_string = f"Weather: Temperature: {air_temperature} °C | Humidity {relative_humidity} % | Wind 10' Avg: {mean_wind_speed} km/h | Wind Gusts: {max_wind} km/h"
    #print(weather_string)
else:
    print("WARNING: Weather timestamp is older than 1 minute!")


######### CAMERA SECTION #########

time_threshold = current_datetime - timedelta(minutes=10)
tib_queries = [{"name": "TIB_Rates_LocalRate", "date": {"$gte": time_threshold}},
               {"name": "TIB_Rates_CameraRate", "date": {"$gte": time_threshold}},
               {"name": "TIB_Rates_BUSYRate", "date": {"$gte": time_threshold}},
               {"name": "TIB_Rates_CalibrationRate", "date": {"$gte": time_threshold}},
               {"name": "TIB_Rates_PedestalRate", "date": {"$gte": time_threshold}},
               ]
tib_avg_values = {
    "TIB_Rates_LocalRate": "N/A",
    "TIB_Rates_CameraRate": "N/A",
    "TIB_Rates_BUSYRate": "N/A",
    "TIB_Rates_CalibrationRate": "N/A",
    "TIB_Rates_PedestalRate": "N/A",
}
clusco_query = {"name": "clusco_mean_dc", "date": {"$gte": time_threshold}}
evb_query = {"name": "RunNumber", "date": {"$gte": current_datetime - timedelta(minutes=10)}}

# Iterate over the queries and retrieve the most recent entry for each (already considered the ones not older than 1min)
for query in tib_queries:
    #print(query)
    entry = collection_tib.find_one(query, sort=[("date", pymongo.DESCENDING)])

    if entry:
        avg_value = entry.get("avg", {})
        tib_avg_values[query["name"]] = round(float(avg_value), 2)
    else:
        print(f"No entry found in the last 10' for {query.get('name')}")
tib_string = f'Rates: Local Rate: {tib_avg_values["TIB_Rates_LocalRate"]} Hz | \
Camera Rate: {tib_avg_values["TIB_Rates_CameraRate"]} Hz | \
Busy Rate: {tib_avg_values["TIB_Rates_BUSYRate"]} Hz | \
Calibration Rate: {tib_avg_values["TIB_Rates_CalibrationRate"]} Hz | \
Pedestal Rate: {tib_avg_values["TIB_Rates_PedestalRate"]} Hz |'
#print(tib_string)

clusco_last_entry = collection_clusco.find_one(clusco_query, sort=[("date", pymongo.DESCENDING)])
if clusco_last_entry:
    avg_value_clusco = round(float(clusco_last_entry.get("avg", "N/A")), 2)
else:
    avg_value_clusco = "N/A"
    print("No entry found in the last 10' for clusco mean DC")
clusco_string = f"Mean Anode Current: {avg_value_clusco} uA"
#print(clusco_string)

evb_last_entry = collection_evb.find_one(evb_query, sort=[("date", pymongo.DESCENDING)])
if evb_last_entry:
    avg_value_evb = int(evb_last_entry.get("avg"))
else:
    avg_value_evb = "N/A"
    print("No entry found in the last 10' for EVB Run number")
evb_string = f"Run number {avg_value_evb}"
#print(evb_string)

# Combine all the strings into the final result
final_result = f"{current_time} {evb_string} Wobble ... Zd ...deg Az ...deg \n {weather_string} \n {tib_string} \n {clusco_string}"
print("")
print(final_result)

# Close the MongoDB connection
client_caco.close()
client_ws.close()
