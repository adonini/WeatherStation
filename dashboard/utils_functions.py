import dash_bootstrap_components as dbc
import numpy as np
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import xml.etree.ElementTree as ET
import logging


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


def combine_datetime(date_time_list):
    """
    Combines a list of dates and times into datetime objects.
    Args:
        date_time_list (list): a list of tuples, where each tuple contains a date string in the format YYYYMMDD
        and a time string in the format HHMMSS
    Returns:
        list: A list of datetime objects.
    """
    timestamps = []
    for date_str, time_str in date_time_list:
        try:
            dt_str = date_str + ' ' + time_str
            dt = datetime.strptime(dt_str, '%Y%m%d %H%M%S')
            timestamps.append(dt)
        except Exception as e:
            print(f'Error in entry {date_str}, {time_str}: {e}')
            logger.error(f'Error in timestamp entry {date_str}, {time_str}: {e}')
            timestamps.append(None)
    return timestamps


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


def get_value_or_nan(dict, key):
    """"Limit to two decimals the output with round"""
    return round(dict[key]['value'], 2) if dict[key]['value'] is not None else 'n/a'


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
