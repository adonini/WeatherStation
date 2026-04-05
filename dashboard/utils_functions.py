import dash_bootstrap_components as dbc
from dash import html
import numpy as np
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import xml.etree.ElementTree as ET
import logging
from configurations import precipitationtype_dict

logger = logging.getLogger('app.functions')


# function to define the card grid of the main content
# not used anymore
def make_card_grid(cards, cards_per_row=2):
    row = []
    #print(row)
    grid = []
    for card in cards:
        if len(row) < cards_per_row:
            #print(row)
            row.append(card)
        if len(row) == cards_per_row:
            grid.append(dbc.CardGroup(row, className="mb-4"))
            row = []
    grid.append(dbc.CardGroup(row))
    return grid


# function that will give us nice labels for a wind speed range in the wind rose
def speed_labels(bins, units):
    labels = []
    for left, right in zip(bins[:-1], bins[1:]):
        if left == bins[0]:
            labels.append('calm')
        elif np.isinf(right):
            labels.append(f'>{int(left+0.01)} {units}')
        else:
            labels.append(f'{int(left+0.01)} - {int(right-0.99)} {units}')
    return list(labels)


# function to generate iframe for windy app
def generate_iframe(src):
    return html.Iframe(
        src=src,
        width="100%",
        height="100%",
        style={"padding": 0, "margin": 0}
    )


# create separate tab for the windy card
def generate_tab(tab_id, label):
    return dbc.Tab(
        label=label,
        tab_id=tab_id,
        label_style={"textTransform": "capitalize"},
        active_label_style={"fontSize": "16px", "fontWeight": "bold", "fontStyle": "italic"}
    )


# function to convert the wind direction from deg to cardinal points
def convert_meteorological_deg2cardinal_dir(deg_measurement):
    """
    from
    http://snowfence.umn.edu/Components/winddirectionanddegrees.htm
    :param deg_measurement:
    :return:
    """
    if deg_measurement > 348.75 or deg_measurement <= 11.25:
        return "N"
    elif deg_measurement > 11.25 and deg_measurement <= 33.25:
        return "NNE"
    elif deg_measurement > 33.75 and deg_measurement <= 56.25:
        return "NE"
    elif deg_measurement > 56.25 and deg_measurement <= 78.75:
        return "ENE"
    elif deg_measurement > 78.75 and deg_measurement <= 101.25:
        return "E"
    elif deg_measurement > 101.25 and deg_measurement <= 123.75:
        return "ESE"
    elif deg_measurement > 123.75 and deg_measurement <= 146.25:
        return "SE"
    elif deg_measurement > 146.25 and deg_measurement <= 168.75:
        return "SSE"
    elif deg_measurement > 168.75 and deg_measurement <= 191.25:
        return "S"
    elif deg_measurement > 191.25 and deg_measurement <= 213.75:
        return "SSW"
    elif deg_measurement > 213.75 and deg_measurement <= 236.25:
        return "SW"
    elif deg_measurement > 236.25 and deg_measurement <= 258.75:
        return "WSW"
    elif deg_measurement > 258.75 and deg_measurement <= 281.25:
        return "W"
    elif deg_measurement > 281.25 and deg_measurement <= 303.75:
        return "WNW"
    elif deg_measurement > 303.75 and deg_measurement <= 326.25:
        return "NW"
    elif deg_measurement > 326.25 and deg_measurement <= 348.75:
        return "NNW"
    elif deg_measurement == 'n/a':
        return ''


def get_magic_values():
    """Retrieve cloud value, and TRAN9 value from the MAGIC website.
    Returns:
        tuple: A tuple containing three strings:
            - cloud_value: The cloud value.
            - tran9_value: The TRAN9 value.
    If there is a problem accessing the website or if the request times out, the function returns 'n/a' for all values.
    """
    url = "http://www.magic.iac.es/site/weather/index.html"
    try:
        response = requests.get(url, timeout=5)  # set a timeout of 5s to get a response
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the table row that contains the values
        cloud_row = soup.find("a", {"href": "javascript:siteWindowpyro()"}).parent.parent
        cloud_value = cloud_row.find_all("td")[1].text.strip()
        tran9_row = soup.find("a", {"href": "javascript:siteWindowlidar()"}).parent.parent
        tran9_value = tran9_row.find_all("td")[1].text.strip()
        return cloud_value, tran9_value
    except requests.exceptions.Timeout:
        logger.error('The request to the MAGIC website timed out.')
        cloud_value = 'n/a'
        tran9_value = 'n/a'
        return cloud_value, tran9_value
    except Exception:
        logger.warning('Unable to access MAGIC values!')
        cloud_value = 'n/a'
        tran9_value = 'n/a'
        return cloud_value, tran9_value


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
        logger.error('The request to the TNG feed timed out.')
        dust_value = 'n/a'
        return dust_value
    except Exception:
        logger.warning('Unable to access TNG values!')
        dust_value = 'n/a'
        return dust_value


# function to open and close the modals
def toggle_modal(n1, is_open):
    """Toggle the state of a modal.
    Args:
        n1 (bool): A boolean value representing whether to toggle the state of the modal.
        is_open (bool): A boolean value representing the current state of the modal.
    Returns:
        bool: If n1 is True or has a value of True, the function returns the opposite of is_open.
            Otherwise, it returns the value of is_open.
    This line checks if n1 is True or has a value of True. If n1 is True or has a value of True,
    it returns the opposite of is_open. If n1 is False and does not have a True value, it returns
    the value of is_open."""
    if n1:  # or n2:
        return not is_open
    return is_open


def get_value_or_nan(data, key):
    """Return rounded value or 'n/a' if missing"""
    value = data.get(key)
    return round(value, 2) if value is not None else None #'n/a'


def handle_data_gaps(timestamps, *data_lists, max_time_diff=120):
    """
    Handle data gaps in multiple lists of data with corresponding timestamps.

    Args:
        timestamps (list): A list of timestamp values.
        *data_lists (lists): Variable number of lists containing data corresponding to the timestamps.
        max_time_diff (float, optional): The maximum time difference allowed to consider data points as continuous. Defaults to 120 seconds.

    Returns:
        Tuple: A tuple containing the updated timestamp list and the updated data lists for the provided data.
    """
    new_data = [[] for _ in range(len(data_lists))]  # initialize empty lists, 3 values -> 3 lists
    new_timestamps = []  # initialize this with the first timestamp already
    prev_timestamp = timestamps[0]  # initialize the prev_timestamp with the timestamp of the first entry (which is the MOST RECENT!!)
    # Initialize each list with the first value
    new_timestamps.append(timestamps[0])
    for i in range(len(data_lists)):
        new_data[i].append(data_lists[i][0])
    for timestamp, *values in zip(timestamps[1:], *data_lists):
        time_difference = abs((timestamp - prev_timestamp).total_seconds())

        if time_difference >= max_time_diff:
            new_timestamps.append(None)
            for i in range(len(values)):
                new_data[i].append(None)
        new_timestamps.append(timestamp)
        for i, value in enumerate(values):
            new_data[i].append(value)

        prev_timestamp = timestamp
    return new_timestamps, *new_data


def handle_rain_alert(precip_alert, rain_alert_timer, time_now):
    """
    Handles the rain alert logic by starting, stopping, or maintaining the timer.
    Args:
        precip_alert (bool): Whether precipitation is currently detected.
        rain_alert_timer (dict): Dictionary storing rain alert state and start time.
        time_now (datetime): The current UTC timestamp.
    Returns:
        tuple: Updated (precip_alert, rain_alert_timer)
    """
    # Ensure necessary keys exist
    rain_alert_timer.setdefault('rain_active', False)

    # Start or reset the rain alert timer
    if precip_alert:
        if not rain_alert_timer['active']:
            # Start the timer if it's a new rain detection
            rain_alert_timer['active'] = True
            rain_alert_timer['start_time'] = time_now.isoformat()
            rain_alert_timer['rain_active'] = False  # Not active yet, waiting for 20s confirmation
            precip_alert = False  # Suppress casual rain readings initially
            logger.info('Rain detected, starting timer.')
        else:
            # Timer is running; check elapsed time
            timestamp_datetime = datetime.strptime(rain_alert_timer['start_time'], '%Y-%m-%dT%H:%M:%S.%f%z')
            elapsed_time = (time_now - timestamp_datetime).total_seconds()
            if elapsed_time >= 20:
                # 20s elapsed → Confirm rain alert as active
                rain_alert_timer['rain_active'] = True
                precip_alert = True  # Rain officially considered active
                logger.info('Rain alert is now active.')
            else:
                # Still in countdown period → suppress alert
                precip_alert = False
                logger.info(f'Rain alert countdown: {20 - elapsed_time:.2f}s remaining.')
    else:
        # No rain detected → Reset everything
        rain_alert_timer['active'] = False
        rain_alert_timer['start_time'] = None
        rain_alert_timer['rain_active'] = False  # Reset alert state
        logger.info('Rain stopped, resetting timer.')
    return precip_alert, rain_alert_timer


def safe_get(d, key):
    val = d.get(key)
    return round(val, 2) if isinstance(val, (int, float)) else None


def extract_live_values(latest_data):
    p_type_raw = latest_data.get('Precipitation_Type')

    p_type_label = None
    if p_type_raw is not None:
        p_type_label = precipitationtype_dict.get(str(int(p_type_raw)), "Unknown")

    return {
        "temp": get_value_or_nan(latest_data, 'Air_Temperature'),
        "hum": get_value_or_nan(latest_data, 'Relative_Humidity'),
        "press": get_value_or_nan(latest_data, 'Absolute_Air_Pressure'),
        "w_speed": get_value_or_nan(latest_data, 'Average_Wind_Speed'),
        "w10_speed": get_value_or_nan(latest_data, 'Mean_10_Wind_Speed'),
        "g_speed": get_value_or_nan(latest_data, 'Max_Wind'),
        "bright": get_value_or_nan(latest_data, 'Brightness'),
        "bright_lux": get_value_or_nan(latest_data, 'Brightness_lux'),
        "dew": get_value_or_nan(latest_data, 'Dew_Point_Temperature'),
        "w_dir": get_value_or_nan(latest_data, 'Mean_Wind_Direction'),
        "p_type_raw": p_type_raw,
        "p_type_label": p_type_label,
        "p_int": get_value_or_nan(latest_data, 'Precipitation_Intensity'),
        "p_acc": get_value_or_nan(latest_data, 'Precipitation_Amount'),
        "rad": get_value_or_nan(latest_data, 'Global_Radiation'),
    }


def compute_alert_flags(values):
    hum = values["hum"]
    g_speed = values["g_speed"]
    w10_speed = values["w10_speed"]
    p_int = values["p_int"]

    return {
        "humidity": hum is not None and hum >= 90,
        "wind": w10_speed is not None and w10_speed >= 36,
        "gust": g_speed is not None and g_speed >= 60,
        "rain_raw": p_int is not None and p_int > 0,
        "strong_wind": (
            (g_speed is not None and g_speed >= 85) or
            (w10_speed is not None and w10_speed >= 50)
        ),
        "humidity_warning": hum is not None and 80 <= hum < 90,
        "wind_warning": w10_speed is not None and 30 <= w10_speed < 36,
        "gust_warning": g_speed is not None and 50 <= g_speed < 60,
    }


def apply_rain_logic(values, flags, rain_alert_timer, time_now):
    rain_active_input = flags["rain_raw"]
    rain_confirmed, rain_alert_timer = handle_rain_alert(
        rain_active_input, rain_alert_timer, time_now
    )

    flags["rain"] = rain_confirmed

    if not rain_alert_timer.get("rain_active", False):
        values["p_type_display"] = "No Rain"
        values["p_int_display"] = 0
    else:
        values["p_type_display"] = values["p_type_label"]
        values["p_int_display"] = values["p_int"]

    return values, flags, rain_alert_timer
