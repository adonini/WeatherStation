from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import pymongo
from asyncua import Client
import asyncio
from dotenv import load_dotenv
import os
import requests
import xml.etree.ElementTree as ET


# Load environment variables from the .env
load_dotenv(".env_run_info")


# functions
def get_tng_dust_value():
    try:
        # URL of the XML feed
        xml_url = "https://tngweb.tng.iac.es/api/meteo/weather/feed.xml"
        # Make a request with a timeout of 5 seconds
        response = requests.get(xml_url, timeout=5)
        xml_data = response.text
        # Parse the XML data
        root = ET.fromstring(xml_data)
        # Find the Dust element and extract its value
        namespace = {"tngw": "http://www.tng.iac.es/weather/current/rss/tngweather"}
        dust_element = root.find(".//tngw:dustTotal", namespace)
        dust_value = dust_element.text if dust_element is not None else 'n/a'
        # Round the Dust value to two decimal places
        if dust_value != 'n/a':
            dust_value = round(float(dust_value), 2)
        return dust_value
    except requests.exceptions.Timeout:
        print('The request to the TNG feed timed out.')
        dust_value = 'n/a'
        return dust_value
    except Exception:
        print('Unable to access TNG values!')
        dust_value = 'n/a'
        return dust_value


# WS opcua server
host_ws_op = os.environ.get('OPCUA_WS_HOST', 'localhost')
port_ws_op = os.environ.get('OPCUA_WS_PORT')
url_ws_op = "opc.tcp://" + host_ws_op + ":" + port_ws_op
node_wind = "ns=" + os.environ.get('NS') + ";s=" + os.environ.get('WIND10_NAME')


async def connect_to_opcua_server(url, node_id):
    try:
        async with Client(url=url) as client:
            node_var = client.get_node(node_id)
            var = await node_var.read_value()
            return var
    except Exception as e:
        print(f"Can not connect to WS OPCUA. Error: {e}")
        return 'N/A'

#  connection to WS mongo
host_ws_db = os.environ.get('WS_DB_HOST', 'localhost')
port_ws_db = os.environ.get('WS_DB_PORT')
uri_ws = "mongodb://" + host_ws_db + ":" + port_ws_db
dbName_ws = os.environ.get('WS_DB_NAME')
collectionName_ws = os.environ.get('WS_COLL_NAME')

client_ws = pymongo.MongoClient(uri_ws)
db_ws = client_ws[dbName_ws]
collection_ws = db_ws[collectionName_ws]

#  connection to caco mongo
host_caco_db = os.environ.get('CACO_DB_HOST', 'localhost')
port_caco_db = os.environ.get('CACO_DB_PORT')
uri_caco = "mongodb://" + host_caco_db + ":" + port_caco_db
dbName_caco = os.environ.get('CACO_DB_NAME')
collectionName_tib = os.environ.get('TIB_COLL_NAME')
collectionName_clusco = os.environ.get('CLUSCO_COLL_NAME')
collectionName_evb = os.environ.get('EVB_COLL_NAME')
collectionName_ecc = os.environ.get('ECC_COLL_NAME')

client_caco = MongoClient(uri_caco)
db_caco = client_caco[dbName_caco]
collection_tib = db_caco[collectionName_tib]
collection_clusco = db_caco[collectionName_clusco]
collection_evb = db_caco[collectionName_evb]
collection_ecc = db_caco[collectionName_ecc]

current_datetime = datetime.now(timezone.utc)
current_time = current_datetime.strftime("%H:%M:%S")
# print(current_datetime)

######## WEATHER SECTION ############
# connect to OPCUA and retrieve wind 10' avg
opcua_var = asyncio.run(connect_to_opcua_server(url_ws_op, node_wind))
if opcua_var == 'N/A':
    print("WARNING!!!! Error retrieving OPC UA variable.")

# Move to the WS DB and find the most recent doc
most_recent_doc = collection_ws.find_one({}, sort=[("_id", pymongo.DESCENDING)])
# Extract date and time values from the document
date_str = most_recent_doc["Date"]["value"]
time_str = most_recent_doc["Time"]["value"]

datetime_str = f"{date_str} {time_str[:2]}:{time_str[2:4]}"
# print(datetime_str)
reading_datetime = datetime.strptime(datetime_str, "%Y%m%d %H:%M").replace(tzinfo=timezone.utc)

# Check that the last entry is not older than 1 minute. Times are in UTC
time_difference_ws = (current_datetime - reading_datetime).total_seconds()
if time_difference_ws <= 120:
    relative_humidity = round(float(most_recent_doc["Relative Humidity"]["value"]), 2)
    air_temperature = round(float(most_recent_doc["Air Temperature"]["value"]), 2)
    max_wind = round(float(most_recent_doc["Max Wind"]["value"]), 2)
    #mean_wind_speed = round(float(most_recent_doc["Mean Wind Speed"]["value"]), 2)

    weather_string = f"Weather: Temperature: {air_temperature} °C | Humidity {relative_humidity} % | Wind 10' Avg: {opcua_var} km/h | Wind Gusts: {max_wind} km/h | TNG Dust: {get_tng_dust_value()} ug/m3"
    # print(weather_string)
else:
    weather_string = "N/A"
    print("WARNING: Weather timestamp is older than 2 minutes!")


######### CAMERA SECTION #########
time_threshold = current_datetime - timedelta(minutes=10)

### TIB ###
tib_queries = [
    {"name": "TIB_Rates_LocalRate"},  # "date": {"$gte": time_threshold}},
    {"name": "TIB_Rates_CameraRate"},  # "date": {"$gte": time_threshold}},
    {"name": "TIB_Rates_BUSYRate"},  # "date": {"$gte": time_threshold}},
    {"name": "TIB_Rates_CalibrationRate"},  # "date": {"$gte": time_threshold}},
    {"name": "TIB_Rates_PedestalRate"},  # "date": {"$gte": time_threshold}},
]
tib_avg_values = {
    "TIB_Rates_LocalRate": "N/A",
    "TIB_Rates_CameraRate": "N/A",
    "TIB_Rates_BUSYRate": "N/A",
    "TIB_Rates_CalibrationRate": "N/A",
    "TIB_Rates_PedestalRate": "N/A",
}
clusco_query = {"name": "clusco_mean_dc", "date": {"$gte": time_threshold}}
evb_query = {
    "name": "RunNumber",
    "date": {"$gte": current_datetime - timedelta(minutes=12)},
}

# Iterate over the queries and retrieve the most recent entry for each (already considered the ones not older than 1min)
for query in tib_queries:
    # print(query)
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
# print(tib_string)

### ECC ###
ecc_queries = [
    {
        "name": "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_01",
        "date": {"$gte": time_threshold},
    },
    {
        "name": "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_02",
        "date": {"$gte": time_threshold},
    },
    {
        "name": "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_03",
        "date": {"$gte": time_threshold},
    },
    {
        "name": "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_06",
        "date": {"$gte": time_threshold},
    },
    {
        "name": "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_07",
        "date": {"$gte": time_threshold},
    },
    {
        "name": "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_08",
        "date": {"$gte": time_threshold},
    },
    {
        "name": "ECC_Monitoring_Sensors_HumiditySensors_HumiditySensor",
        "date": {"$gte": time_threshold},
    },
]

ecc_avg_values = {
    "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_01": "N/A",
    "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_02": "N/A",
    "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_03": "N/A",
    "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_06": "N/A",
    "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_07": "N/A",
    "ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_08": "N/A",
    "ECC_Monitoring_Sensors_HumiditySensors_HumiditySensor": "N/A",
}

for query in ecc_queries:
    # print(query)
    entry = collection_ecc.find_one(query, sort=[("date", pymongo.DESCENDING)])

    if entry:
        avg_value = entry.get("avg", {})
        ecc_avg_values[query["name"]] = round(float(avg_value), 2)
    else:
        print(f"No entry found in the last 10' for {query.get('name')}")


ecc_string = f'Air Modules Right 1: {ecc_avg_values["ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_01"]}°C | \
Air Modules Right 2: {ecc_avg_values["ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_02"]}°C | \
Air Modules Left: {ecc_avg_values["ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_03"]}°C | \
Air Front Right: {ecc_avg_values["ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_06"]}°C | \
Air Front Left: {ecc_avg_values["ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_07"]}°C | \
Air Backplanes: {ecc_avg_values["ECC_Monitoring_Sensors_TemperatureSensors_TemperatureSensor_08"]}°C | \
Camera Humidity: {ecc_avg_values["ECC_Monitoring_Sensors_HumiditySensors_HumiditySensor"]}%'

### CLUSCO ###
clusco_last_entry = collection_clusco.find_one(
    clusco_query, sort=[("date", pymongo.DESCENDING)]
)
if clusco_last_entry:
    avg_value_clusco = round(float(clusco_last_entry.get("avg", "N/A")), 2)
else:
    avg_value_clusco = "N/A"
    print("")
    print("WARNING!! No entry found in the last 10' for clusco mean DC")
clusco_string = f"Mean Anode Current: {avg_value_clusco} uA"
# print(clusco_string)

### EVB ###
evb_last_entry = collection_evb.find_one(evb_query, sort=[("date", pymongo.DESCENDING)])
if evb_last_entry:
    avg_value_evb = int(evb_last_entry.get("avg"))
else:
    avg_value_evb = "N/A"
    print("WARNING!! No entry found in the last 10' for EVB Run number")
evb_string = f"Run number {avg_value_evb}"
# print(evb_string)

# Combine all the strings into the final result
final_result = f"{current_time} {evb_string}, Wobble ..., Zd ...deg, Az ...deg \n {weather_string} \n {tib_string} \n {clusco_string} \n RTA sqrt(TS): ..."
print("")
print("Please, always check that the printed values are correct!!!")
print("")
print(final_result)
print("")
print(ecc_string)

# Close the MongoDB connection
client_caco.close()
client_ws.close()
