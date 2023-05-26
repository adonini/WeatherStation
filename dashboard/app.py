import matplotlib
import requests
import numpy as np
import pandas as pd
from pandas import json_normalize
import flask
import logging
from logging.handlers import TimedRotatingFileHandler
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
# from dash.exceptions import PreventUpdate
# import json
import pymongo
from pymongo import MongoClient
import plotly.graph_objects as go
from datetime import datetime, timedelta, time
from suntime import Sun, SunTimeException
from bs4 import BeautifulSoup
# from sklearn.linear_model import LinearRegression
from astropy.coordinates import EarthLocation
import astropy.units as u
from astroplan import Observer
from waitress import serve
matplotlib.use('Agg')

#---------------------------------------------------------------------------#
# Initialize the main logger
#---------------------------------------------------------------------------#
# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # override the default severity of logging
# Create handler: new file every day at 12:00 UTC
utc_time = time(12, 0, 0)
file_handler = TimedRotatingFileHandler('/var/log/lst-safetybroker/WS/dashboard/dashboard.log', when='D', interval=1, atTime=utc_time, backupCount=7, utc=True)
#file_handler = TimedRotatingFileHandler('./logs_dash/dashboard.log', when='D', interval=1, atTime=utc_time, backupCount=7, utc=True)
# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)
# Add handlers to the logger
logger.addHandler(file_handler)

#---------------------------------------------------------------------------#
# Connect to MongoDB
#---------------------------------------------------------------------------#
client = MongoClient("mongodb://127.0.0.1:27010")
mydb = client["WS"]
collection = mydb["Readings"]

server = flask.Flask(__name__)

#---------------------------------------------------------------------------#
# Define stuff
#---------------------------------------------------------------------------#
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"
# Set location for Roque de los Muchachos
location_lat = 28.7666636
location_long = -17.8833298

# Instantiate Dash and Exposing the Flask Server
# meta_tags arguments allow controlling the size of the app component through different devices size
app = dash.Dash(server=server, update_title=None, suppress_callback_exceptions=True, title='LST-1 Weather Station',
                external_stylesheets=[dbc.themes.SANDSTONE, FONT_AWESOME, dbc.icons.BOOTSTRAP, dbc.icons.FONT_AWESOME],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.5, minimum-scale=0.5'}],
                )

####################
# navbar = dbc.Navbar(
#     dbc.Container(
#         [
#             # Use row and col to control vertical alignment of logo / brand
#             dbc.Row(
#                 [
#                     dbc.Col(dbc.NavbarBrand("LST-1 Weather", className="fs-1 text-dark position-absolute  top-0 start-50 translate-middle-x"), width=10),
#                     dbc.Col(html.Img(src=CTA_LOGO, height="60px", className="position-absolute top-0 end-0"), width=2),
#                 ],
#                 #align="center",
#                 className="g-2 text-center mx-auto",
#             ),
#         ]
#     ),
#     className="bg-transparent"
# )

###################
#  Sidebar cards
##################
# fs-{size} text heading size
# w-{option} width relative to parent
# bg-{color} background color
card_summary = dbc.Card([
    dbc.CardHeader("Current values", className="card text-white bg-primary w-100 fs-5"),
    dbc.CardBody([
        dbc.ListGroup(id='live-values', flush=True),
    ], className="p-0 m-0"),  # removes the margin and the padding
    dbc.CardFooter(id="live-timestamp", children=[]),
])

card_info = dbc.Card([
    dbc.CardHeader("Info", className="card text-white bg-primary w-100 fs-5"),
    dbc.CardBody([
        html.Div([html.I(className="fas fa-clock"), " Time ", html.Span(id="current-time", style={'marginLeft': '10px'})]),
        html.Div([html.I(className="fas fa-calendar-day"), " Date ", html.Span(id="current-date", style={'marginLeft': '10px'})]),
        html.Hr(),
        html.Div([html.I(className="bi bi-sunrise-fill me-2"), " Sunrise ", html.Span(id='sunrise-time', style={'marginLeft': '10px'})]),
        html.Div([html.I(className="bi bi-sunset-fill me-2"), " Sunset ", html.Span(id='sunset-time', style={'marginLeft': '10px'})]),
        html.Hr(),
        html.Div([
            #html.P([html.I(className='fas fa-eye'), ' Visible ', html.Span(id='moon-visibility')]),
            #html.P([html.I(className='fas fa-moon mr-2'), ' Phase ', html.Span(id='moon-phase')]),
            html.P([html.I(className='fas fa-moon mr-2'), ' Illumination ', html.Span(id='moon-illumination', style={'marginLeft': '10px'})]),
            html.P([html.I(className='fas fa-arrow-up'), ' Rise ', html.Span(id='moon-rise', style={'marginLeft': '10px'})]),
            html.P([html.I(className='fas fa-arrow-down'), ' Set ', html.Span(id='moon-set', style={'marginLeft': '10px'})])
        ]),
    ]),
])

######################
# Sidebar definition
#####################
SIDEBAR_STYLE = {
    "text-align": "center",
    "padding": "2rem 1rem",
    "background-color": "#596568e3",
    "z-index": "5",
}

sidebar = html.Div([
    dbc.Nav(
        [html.Div(card_summary),
         dcc.Interval(id='interval-livevalues', interval=20000, n_intervals=0, disabled=False),
         html.Hr(),
         html.Div(card_info)],
        vertical=True,
    )],
    className="sticky-top overflow-scroll vh-100",
    style=SIDEBAR_STYLE,
)

######################
# # Card components
######################
# plots configuration
config = {
    'displaylogo': False,  # remove plotly logo
    'modeBarButtonsToRemove': ['resetScale'],
    'toImageButtonOptions': {'height': None, 'width': None},  # download image at the currently-rendered size
}

time_options = [{'label': '1 Hour', 'value': 1},
                {'label': '3 Hours', 'value': 3},
                {'label': '6 Hours', 'value': 6},
                {'label': '12 Hours', 'value': 12},
                {'label': '24 Hours', 'value': 24},
                {'label': '48 Hours', 'value': 48}]


def make_plot_card(value_name, dropdown_id, graph_id, timestamp_id):
    # Header
    header = dbc.Row([
        dbc.Col(html.H4(value_name), width=9),
        dbc.Col(dcc.Dropdown(
            id=dropdown_id,
            options=time_options,
            value=1,
            clearable=False,
            searchable=False,
            style={'color': 'black', 'align': 'center', 'width': '100px', 'float': 'right'},
        ), width=3, style={"display": "flex", "align-items": "center", "justify-content": "flex-end"})
    ], align="center")
    # Body
    body = html.Div(dbc.Spinner(
        size="md",
        color="primary",
        delay_show=1000,
        children=[dcc.Graph(id=graph_id, figure={}, style={"width": "100%", "height": "100%"}, config=config)]),  # width and height to 100% of the parent element
        #id=f"{graph_id}-loading",
    )
    return dbc.Card(
        [
            dbc.CardHeader(header, className="card text-white bg-primary", style={'width': '100%'}),
            dbc.CardBody(body, style={"maxHeight": 500, "width": "100%"}),
            dbc.CardFooter(id=timestamp_id, children=[]),
        ],
        className="m-2 shadow",
        style={"minWidth": "36rem"},
    )


cards = [
    make_plot_card("Wind Speed", "wind_hour_choice", "wind-graph", "wind-timestamp"),
    make_plot_card("Humidity", "hum_hour_choice", "humidity-graph", "hum-timestamp"),
    make_plot_card("Temperature", "temp_hour_choice", "temp-graph", "temp-timestamp"),
    make_plot_card("Wind Rose", "windrose_hour_choice", "wind-rose", "windrose-timestamp"),
    make_plot_card("Global Radiation", "rad_hour_choice", "radiation-graph", "rad-timestamp"),
    make_plot_card("Brightness", "brightness_hour_choice", "brightness-graph", "brightness-timestamp"),
]


def make_card_grid(cards_per_row=2):
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


######################
# # Define content
######################
# padding for the page content
CONTENT_STYLE = {
    #"margin-left": "2%",
    #"margin-right": "-2 rem",
    #"padding": "2rem 1rem",
    "min-width": "600px",
    #"overflow": "scroll",
    #"flex-grow": "1",
    "z-index": "5",
}

content = html.Div(children=[
    html.Div(dbc.Col(make_card_grid())),
    dcc.Interval(id='interval-component', interval=60000, n_intervals=0, disabled=False),  # 1min update
], className="p-2", style=CONTENT_STYLE)

######################
# # Set the layout
######################
navbar_menu = dbc.DropdownMenu([
    dbc.DropdownMenuItem("Other Weather Stations", header=True, className="text-center", style={'text-transform': 'uppercase'}),
    dbc.DropdownMenuItem("ORM Weather Info", href="http://catserver.ing.iac.es/weather/index.php?miniview=1", target="_blank", className="text-primary text-capitalize", external_link=True),
    dbc.DropdownMenuItem("MAGIC Weather Info", href="http://www.magic.iac.es/site/weather/index.html", className="text-primary text-capitalize", target="_blank", external_link=True),
    dbc.DropdownMenuItem("TNG Weather Info", href="https://tngweb.tng.iac.es/weather/current", className="text-primary text-capitalize", target="_blank", external_link=True),
    dbc.DropdownMenuItem("GTC Weather Info", href="https://atmosportal.gtc.iac.es/index2.php", className="text-primary text-capitalize", target="_blank", external_link=True),
    dbc.DropdownMenuItem("NOT Weather Info", href="http://www.not.iac.es/weather/", className="text-primary text-capitalize", target="_blank", external_link=True),
    dbc.DropdownMenuItem("Mercator Weather Info", href="http://www.mercator.iac.es/status/meteo/", className="text-primary text-capitalize", target="_blank", external_link=True),
    dbc.DropdownMenuItem("ING Weather Info", href="http://catserver.ing.iac.es/weather/", className="text-primary text-capitalize", target="_blank", external_link=True),
    dbc.DropdownMenuItem(divider=True),
    dbc.DropdownMenuItem("Links", header=True, className="text-center", style={'text-transform': 'uppercase'}),
    dbc.DropdownMenuItem("Windy", href="https://www.windy.com/?800h,28.207,-17.885,8,m:es4afFm", className="text-primary text-capitalize", target="_blank", external_link=True),
    dbc.DropdownMenuItem("AEMET Warnings", href="https://www.aemet.es/en/eltiempo/prediccion/avisos?w=hoy&p=6593&k=coo", className="text-primary text-capitalize", target="_blank", external_link=True),
    dbc.DropdownMenuItem("Mountain Forecast", href="https://www.mountain-forecast.com/peaks/Roque-de-los-Muchachos/forecasts/2423", className="text-primary text-capitalize", target="_blank", external_link=True),
], label="Menu", style={'zindex': '999'})

app.layout = html.Div([
    dbc.Row([
        dbc.Col(navbar_menu, width=1, align="center"),
        dbc.Col(html.Div(html.H1("LST-1 Weather Station", className="display-4 text-center")), width=9, align="center"),
        dbc.Col(html.Div(html.Img(src=app.get_asset_url('logo.png'), height="60px", className="position-absolute top-50 end-0 translate-middle-y")), align="center", className="position-relative", width=1),
    ], style={"max-height": "95px", "margin-top": "20px", 'zindex': '999'}, className='d-flex justify-content-between align-items-center break-text me-2 ms-1'),
    html.Hr(className="mt-sm-4"),
    dbc.Row([
        html.Div(sidebar, className="col-xl-2 col-lg-4 col-md-5 col-sm-12 m-0 ps-0"),
        html.Div(content, className="col-xl-10 col-lg-8 col-md-7 col-sm-12"),
        # dcc.Store inside the user's current browser session
        #dcc.Store(id='store-last-db-entry', data=[], storage_type='memory'),  # memory reset at every refresh
        # add an automatic refresh every day of everything
        dcc.Interval(
            id='interval-day-change',
            interval=24 * 60 * 60 * 1000,  # 1 day in milliseconds
            n_intervals=0
        )
    ]),
    html.Hr(),
    dbc.Row([
        html.Div([
            html.P([
                html.Small('Large Size Telescope', className="text-secondary"),
                html.Br(),
                html.A(html.Span('About', style={"font-size": "13px", "text-decoration": "none"}), href="https://www.lst1.iac.es/index.html", target="_blank", className="text-primary", style={"margin-top": "5px"})
            ])
        ])
    ])
], className="container-fluid")


##################
# Wind rose stuff
##################
# function that will give us nice labels for a wind speed range
def speed_labels(bins, units):
    labels = []
    for left, right in zip(bins[:-1], bins[1:]):
        if left == bins[0]:
            labels.append('calm'.format(right))
        elif np.isinf(right):
            labels.append('>{} {}'.format(left, units))
        else:
            labels.append('{} - {} {}'.format(left, right, units))

    return list(labels)


# Define our bins and labels for speed and wind
spd_bins = [-1, 0, 10, 20, 30, 40, 50, 60, np.inf]
spd_labels = speed_labels(spd_bins, units='km/h')
dir_bins = np.arange(-22.5 / 2, 360 + 22.5, 22.5)  # np.arange(-7.5, 370, 15)
dir_labels = (dir_bins[:-1] + dir_bins[1:]) / 2
# Mapping color for wind direction and speed
spd_colors_dir = ["#0072dd", "#00c420", "#eded00", "#be00d5", "#0072dd"]
spd_colors_speed = ["#ffffff",
                    "#b2f2ff",
                    "#33ddff",
                    "#00aaff",
                    "#0055ff",
                    "#0000ff",
                    "#aa00ff",
                    "#ff00ff",
                    "#cc0000",
                    "#ffaa00",
                    ]


##############
# Random stuff
##############
# decode precipitation type
precipitationtype_dict = {  0: 'None',
                            40: 'Precipitation present',
                            51: 'Light drizzle',
                            52: 'Moderate drizzle',
                            53: 'Heavy drizzle',
                            61: 'Light rain',
                            62: 'Moderate rain',
                            63: 'Heavy rain',
                            67: 'Light rain',
                            68: 'Moderate rain',
                            70: 'Snowfall',
                            71: 'Light snow',
                            72: 'Moderate snow',
                            73: 'Heavy snow',
                            74: 'Ice pallets',
                            89: 'Heavy hail',
                            }


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
        return "S"
    elif deg_measurement > 168.75 and deg_measurement <= 191.25:
        return "SSW"
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
    """Retrieve TNG dust value, cloud value, and TRAN9 value from the MAGIC astronomical observatory website.
    Returns:
        tuple: A tuple containing three strings:
            - tng_dust_value: The TNG dust value.
            - cloud_value: The cloud value.
            - tran9_value: The TRAN9 value.
    If there is a problem accessing the website or if the request times out, the function returns 'n/a' for all values.
    """
    url = "http://www.magic.iac.es/site/weather/index.html"
    try:
        response = requests.get(url, timeout=5)  # set a timeout of 5s to get a response
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the table row that contains the values
        tng_dust_row = soup.find("a", {"href": "javascript:siteWindowdust()"}).parent.parent
        tng_dust_value = tng_dust_row.find_all("td")[1].text.strip()
        cloud_row = soup.find("a", {"href": "javascript:siteWindowpyro()"}).parent.parent
        cloud_value = cloud_row.find_all("td")[1].text.strip()
        tran9_row = soup.find("a", {"href": "javascript:siteWindowlidar()"}).parent.parent
        tran9_value = tran9_row.find_all("td")[1].text.strip()
        return tng_dust_value, cloud_value, tran9_value
    except requests.exceptions.Timeout:
        logger.error('The request to the MAGIC website timed out.')
        tng_dust_value = 'n/a'
        cloud_value = 'n/a'
        tran9_value = 'n/a'
        return tng_dust_value, cloud_value, tran9_value
    except Exception:
        logger.warning('Unable to access MAGIC values!')
        tng_dust_value = 'n/a'
        cloud_value = 'n/a'
        tran9_value = 'n/a'
        return tng_dust_value, cloud_value, tran9_value


def create_list_group_item(title, value, unit,  timestamp, badge_color='green', row_color='default'):
    if value == 'n/a' or timestamp < (datetime.utcnow() - timedelta(minutes=5)):
        badge_color = 'secondary'
        row_color = 'secondary'
    return dbc.ListGroupItem(
        dbc.Row([
            dbc.Col(title, className="justify-content-between"),
            dbc.Col(dbc.Badge(f"{value} {unit}" if value != 'n/a' else value, color=badge_color), className="d-flex align-items-center justify-content-center")
        ]),
        color=row_color,
        className="rounded border-bottom position-relative"
    )


def create_list_group_item_alert(title, value, unit, badge_color='danger', row_color='danger'):
    """
    Create a ListGroupItem with title, value and unit Badge, and Modal (for certain titles).
    Args:
    title (str): Title of the ListGroupItem.
    value (str/int/float): Value of the item.
    unit (str): Unit of the value.
    badge_color (str): Color of the Badge element (Default: 'danger').
    row_color (str): Color of the ListGroupItem element (Default: 'danger').
    Returns:
    line (dbc.ListGroupItem): A Bootstrap ListGroupItem element.
    """
    if value == 'n/a':
        badge_color = 'secondary'
        row_color = 'secondary'
    return dbc.ListGroupItem([
        dbc.Row([
            dbc.Col(
                dbc.Stack([
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    html.Div(title),
                ], direction="horizontal", gap=1)),
            dbc.Col(dbc.Badge(f"{value} {unit}", color=badge_color), className="d-flex align-items-center justify-content-center"),
        ]),
    ], color=row_color, className="rounded border-bottom position-relative")


def get_value_or_nan(dict, key):
    """"Limit to two decimals the output with round"""
    return round(dict[key]['value'], 2) if dict[key]['value'] is not None else 'n/a'

######################
# Callback functions
######################
# Function to store the last entry in the db. Updates at refresh or every x sec
# @app.callback(
#     dash.dependencies.Output('store-last-db-entry', 'data'),
#     dash.dependencies.Input('interval-component', 'n_intervals'))
# def last_db_entry(n_intervals):
#     # Get the latest reading from the database
#     #print(type(collection.find_one(sort=[('added', pymongo.DESCENDING)])))
#     # make the object JSON serializable
#     last_entry = collection.find_one(sort=[('added', pymongo.DESCENDING)])
#     #last_entry['added'] = last_entry['added'].strftime('%Y-%m-%d %H:%M:%S')
#     result_json = json.dumps(last_entry, default=str)
#     #print(type(result_json))
#     return result_json
# @app.callback(
#     dash.dependencies.Output("sidebar-collapse", "is_open"),
#     [dash.dependencies.Input("sidebar-toggle-button", "n_clicks")],
#     [dash.dependencies.State("sidebar-collapse", "is_open")],
# )
# def toggle_sidebar(n_clicks, is_open):
#     if n_clicks:
#         return not is_open
#     return is_open


# Callback to update the time and date every 20sec
@app.callback(
    dash.dependencies.Output('current-time', 'children'),
    dash.dependencies.Output('current-date', 'children'),
    dash.dependencies.Input('interval-livevalues', 'n_intervals'))
def update_date_time(n_intervals):
    return f"{datetime.utcnow().time().strftime('%H:%M:%S %Z')} UTC", f"{datetime.utcnow().date().strftime('%d-%m-%Y %Z')}"


# callback to update moon data every day
@app.callback(
    #dash.dependencies.Output('moon-visibility', 'children'),
    #dash.dependencies.Output('moon-phase', 'children'),
    dash.dependencies.Output('moon-illumination', 'children'),
    dash.dependencies.Output('moon-rise', 'children'),
    dash.dependencies.Output('moon-set', 'children'),
    dash.dependencies.Input('interval-day-change', 'n_intervals')
)
def update_moon(n_intervals):
    elevation = 2200 * u.m
    location = EarthLocation(lat=location_lat * u.deg, lon=location_long * u.deg, height=elevation)
    # Get the current time in UTC
    now = datetime.utcnow()
    obs = Observer(location=location, timezone="UTC")
    # Calculate moon illumination
    moon_illumination = obs.moon_illumination(now) * 100
    # Determine the moon's rise and set times
    try:
        moon_rise_time = obs.moon_rise_time(now, which='nearest').strftime('%d-%m-%Y %H:%M:%S UTC')
    except Exception as e:
        logger.error(f"Couldn't calculate moon rise time! Error: {e}")
        moon_rise_time = 'n/a'

    try:
        moon_set_time = obs.moon_set_time(now, which='next').strftime('%d-%m-%Y %H:%M:%S UTC')
    except Exception as e:
        logger.error(f"Couldn't calculate moon setting time! Error: {e}")
        moon_set_time = 'n/a'

    data_formatter = '.2f'
    return f"{moon_illumination:>{data_formatter}} %", moon_rise_time, moon_set_time


# Function to update sunrise, sunset and moon data every day
@app.callback(
    Output('sunrise-time', 'children'),
    Output('sunset-time', 'children'),
    Input('interval-day-change', 'n_intervals')
)
def update_sun(n_intervals):
    try:
        # Create a Sun object
        sun = Sun(location_lat, location_long)
        # Get today's sunrise and sunset in UTC
        today_sr = sun.get_sunrise_time()
        today_ss = sun.get_sunset_time()
        return f"{today_sr.strftime('%H:%M')} UTC", f"{today_ss.strftime('%H:%M')} UTC"
    except SunTimeException as e:
        logger.error(f"Couldn't calculate sun rising and setting time! Error: {e}")
        return 'n/a', 'n/a'


# Define a function to update the live values every 20 seconds (depends from the interval)
@app.callback([Output('live-values', 'children'),
               Output('live-timestamp', 'children')],
              [Input('interval-livevalues', 'n_intervals'),
               #dash.dependencies.Input('store-last-db-entry', 'data')
               ]
              )
def update_live_values(n_intervals, n=100):
    # Get the latest reading from the database
    latest_data = collection.find_one(sort=[('added', pymongo.DESCENDING)])
    tng_dust_value, cloud_value, tran9_value = get_magic_values()

    # Get the WS timestamps
    time = latest_data['Time']['value']
    date = latest_data['Date']['value']
    try:
        dt_str = date + ' ' + time
        timestamps = datetime.strptime(dt_str, '%Y%m%d %H%M%S')
    except Exception as e:
        # if an exception is raised, try to get the second-to-last entry in the database
        logger.warning(f'Error in timestamp entry: {e}. MongoDb ID: {latest_data["_id"]}')
        logger.warning('Checking the second-to-last entry in the database.')
        latest_data = collection.find_one(sort=[('added', pymongo.DESCENDING)], skip=1)
        time = latest_data['Time']['value']
        date = latest_data['Date']['value']
        i = 2  # start with the third-to-last entry
        while True:
            try:
                dt_str = date + ' ' + time
                timestamps = datetime.strptime(dt_str, '%Y%m%d %H%M%S')
                break  # exit the loop if a valid timestamp is found
            except Exception as e:
                #print(f'Error in timestamp entry: {e}.')
                logger.error(f'Error in timestamp entry: {e}. MongoDb ID: {latest_data["_id"]}')
                logger.warning(f'Checking the {i}-to-last entry in the database.')
                latest_data = collection.find_one(sort=[('added', pymongo.DESCENDING)], skip=i)
                time = latest_data['Time']['value']
                date = latest_data['Date']['value']
                i += 1  # move to the next entry in the database
                if i > n:  # exit the loop if all entries have been checked
                    raise Exception("Unable to find a valid timestamp in the database.")

    # Control the values, if they can not be accessed, put n/a
    temp = get_value_or_nan(latest_data, 'Air Temperature')
    hum = get_value_or_nan(latest_data, 'Relative Humidity')
    press = get_value_or_nan(latest_data, 'Absolute Air Pressure')
    w_speed = get_value_or_nan(latest_data, 'Average Wind Speed')
    w10_speed = get_value_or_nan(latest_data, 'Mean 10 Wind Speed')
    g_speed = get_value_or_nan(latest_data, 'Max Wind')
    bright = get_value_or_nan(latest_data, 'Brightness')
    bright_lux = get_value_or_nan(latest_data, 'Brightness lux')
    dew = get_value_or_nan(latest_data, 'Dew Point Temperature')
    w_dir = get_value_or_nan(latest_data, 'Mean Wind Direction')
    p_type = get_value_or_nan(latest_data, 'Precipitation Type')
    if p_type != 'n/a':
        for key_p, value_p in precipitationtype_dict.items():
            if (p_type == int(key_p)):
                p_type = value_p
    p_int = get_value_or_nan(latest_data, 'Precipitation Intensity')
    rad = get_value_or_nan(latest_data, 'Global Radiation')

    # Format the live values as a list
    live_values = [
        create_list_group_item("Humidity", hum, ' %', timestamps),
        create_list_group_item("Wind Speed", w_speed, ' km/h', timestamps),
        create_list_group_item("Wind 10' Avg", w10_speed, ' km/h', timestamps),
        create_list_group_item("Wind Gusts", g_speed, ' km/h', timestamps),
        create_list_group_item("Wind Direction", w_dir, f" ° ({convert_meteorological_deg2cardinal_dir(w_dir)})", timestamps),
        create_list_group_item("Temperature", temp, ' °C', timestamps),
        create_list_group_item("Dew Point Temperature", dew, ' °C', timestamps),
        create_list_group_item("Brightness", bright_lux, ' lux', timestamps) if bright <= 1 else create_list_group_item("Brightness", bright, ' klux', timestamps),
        create_list_group_item("TNG Dust", tng_dust_value, ' µg/m3', timestamps),
        create_list_group_item("Precipitation", p_type, '', timestamps),
        create_list_group_item("Precipitation Intensity", p_int, ' mm/h', timestamps),
        create_list_group_item("Global Radiation", rad, ' W/m2', timestamps),
        create_list_group_item("Pressure", press, ' hPa', timestamps),
        create_list_group_item("MAGIC Cloudiness", cloud_value, '', timestamps),
        create_list_group_item("MAGIC Trans@9km", tran9_value, '', timestamps),
    ]

    # Check wind speed and change the background color accordingly
    if timestamps > (datetime.utcnow() - timedelta(minutes=5)):
        if w_speed != 'n/a':
            if w_speed >= 50:
                live_values[1] = create_list_group_item_alert("Wind Speed", w_speed, ' km/h')
            elif 40 <= w_speed < 50:
                live_values[1] = create_list_group_item_alert("Wind Speed", w_speed, ' km/h', badge_color='warning', row_color='warning')

        if w10_speed != 'n/a':
            if w10_speed >= 50:
                live_values[1] = create_list_group_item_alert("Wind 10′ Avg", w_speed, ' km/h')
            elif 40 <= w10_speed < 50:
                live_values[1] = create_list_group_item_alert("Wind 10′ Avg", w_speed, ' km/h', badge_color='warning', row_color='warning')

        # Check gusts speed and change the background color accordingly
        if g_speed != 'n/a':
            if g_speed >= 60:
                live_values[2] = create_list_group_item_alert("Wind Gusts", g_speed, ' km/h')
            elif 50 <= g_speed < 60:
                live_values[2] = create_list_group_item_alert("Wind Gusts", g_speed, ' km/h', badge_color='warning', row_color='warning')

        # Check humidity and change the background color accordingly
        if hum != 'n/a':
            if hum >= 90:
                live_values[0] = create_list_group_item_alert("Humidity", hum, ' %')
            elif 80 <= hum < 90:
                print(hum)
                live_values[0] = create_list_group_item_alert("Humidity", hum, ' %', badge_color='warning', row_color='warning')

    return live_values, dbc.Badge(f"Last update: {timestamps}", color='secondary' if timestamps < (datetime.utcnow() - timedelta(minutes=5)) else 'green', className="text-wrap")


# Define the callback function to update the temp graph
@app.callback([#Output('temp-graph-loading', 'children'),
               Output('temp-graph', 'figure'),
               Output('temp-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('temp_hour_choice', 'value')])
def update_temp_graph(n_intervals, time_range):
    # Define the projection to query only the required fields
    projection = {
        'added': 1,
        'Air Temperature.value': 1,
        'Dew Point Temperature.value': 1,
        'Time.value': 1,
        'Date.value': 1,
        '_id': 0
    }
    # Query the data from the database
    data = list(collection.find({
        'added': {'$gte': datetime.utcnow() - timedelta(hours=time_range)},
        # 'Air Temperature.value': {'$ne': None},
        # 'Dew Point Temperature.value': {'$ne': None},
        # 'Time.value': {'$ne': None},
        # 'Date.value': {'$ne': None}
        },
        projection, sort=[('added', pymongo.DESCENDING)]))

    if not data:
        # Query the latest data from the database
        last = collection.find_one({},
                                   projection,
                                   sort=[('added', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            data = list(collection.find({
                'added': {'$gte': last['added'] - timedelta(hours=time_range)},
                # 'Air Temperature.value': {'$ne': None},
                # 'Dew Point Temperature.value': {'$ne': None},
                # 'Time.value': {'$ne': None},
                # 'Date.value': {'$ne': None}
                },
                projection, sort=[('added', pymongo.DESCENDING)]))
    # Get the temperature values and the dew-point values
    temps = [d['Air Temperature']['value'] for d in data]
    dews = [d['Dew Point Temperature']['value'] for d in data]
    # create a list of tuple and get WS timestamps
    date_time = [(doc['Date']['value'], doc['Time']['value']) for doc in data]
    timestamps = combine_datetime(date_time)

    # Create the figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=temps,
                             name='Temperature',
                             line_color="#316395",
                             hovertemplate=('%{x}<br>' + 'Temperature: %{y:.2f} °C <br><extra></extra> ')
                             #line=dict(color='firebrick')
                             )
                  )

    # Add dew-point temp to the plot
    fig.add_trace(go.Scatter(x=timestamps, y=dews,
                             name='Dew Point',
                             line_color='firebrick',
                             hovertemplate=('%{x}<br>' + 'Dew Point: %{y:.2f} °C <br><extra></extra> ')
                             )
                  )
    fig.update_layout(yaxis_range=[-30, 30],
                      uirevision=True,
                      #width=620,
                      #height=400,
                      autosize=False,
                      yaxis_title='°C',
                      xaxis_tickangle=45,
                      margin_t=2,
                      template='plotly_white',
                      legend=dict(x=1, y=0.9),
                      modebar_add=["hovercompare", "v1hovermode"],
                      )
    fig.update_xaxes(showgrid=False)
    # Return the figure
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0] < (datetime.utcnow() - timedelta(minutes=5)) else 'green')


# Define the callback function to update the humidity graph
@app.callback([Output('humidity-graph', 'figure'),
               Output('hum-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('hum_hour_choice', 'value')])
def update_hum_graph(n_intervals, time_range):
    # Define the projection to query only the required fields
    projection = {
        'added': 1,
        'Relative Humidity.value': 1,
        'Time': 1,
        'Date': 1,
        '_id': 0
    }
    # Query the data from the database
    data = list(collection.find({
        'added': {'$gte': datetime.utcnow() - timedelta(hours=time_range)},
        # 'Relative Humidity.value': {'$ne': None},
        # 'Time.value': {'$ne': None},
        # 'Date.value': {'$ne': None}
        },  # filter out None values
        projection).sort('added', pymongo.DESCENDING))  # first value is the newest
    #print(data)
    if not data:
        # Query the latest data from the database
        last = collection.find_one({},
                                   projection,
                                   sort=[('added', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            data = list(collection.find({
                'added': {'$gte': last['added'] - timedelta(hours=time_range)},
                # 'Relative Humidity.value': {'$ne': None},
                # 'Time.value': {'$ne': None},
                # 'Date.value': {'$ne': None}
                },
                projection, sort=[('added', pymongo.DESCENDING)]))

    # Get the most recent value
    latest_data = data[0]['Relative Humidity']['value']
    # Get the humidity values
    hums = [d['Relative Humidity']['value'] for d in data]
    # Get the WS timestamps
    date_time = [(doc['Date']['value'], doc['Time']['value']) for doc in data]
    timestamps = combine_datetime(date_time)

    # Create the figure
    fig = go.Figure()
# aggiungere che se il valor di hum e NaN allora viene scartato assieme al timestamp per quella entry
    fig.add_trace(go.Scatter(x=timestamps, y=hums,
                             name='Humidity',
                             hoveron='points',
                             line_color="#316395",
                             hovertemplate=('%{x}<br>' + 'Humidity: %{y:.2f} %<br><extra></extra> ')
                             )
                  )
    fig.update_layout(yaxis_range=[0, 100],
                      uirevision=True,  # stay zoomed in with an update
                      #width=620,
                      #height=400,
                      autosize=False,
                      yaxis_title='%',
                      xaxis_tickangle=45,
                      margin_t=2,
                      template='plotly_white',
                      )
    fig.update_xaxes(showgrid=False)

    # Change graph color if above limit if timestamps are up to date
    if timestamps[0] > (datetime.utcnow() - timedelta(minutes=5)):
        if latest_data >= 90:
            fig.update_traces(fill='tonexty', line_color='red')
        if 80 <= latest_data < 90:
            fig.update_traces(fill='tonexty', line_color='orange')

    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0] < (datetime.utcnow() - timedelta(minutes=5)) else 'green')


# Define the callback function to update the wind graph
@app.callback([Output('wind-graph', 'figure'),
               Output('wind-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('wind_hour_choice', 'value')])
def update_wind_graph(n_intervals, time_range):
    projection = {
        'added': 1,
        'Average Wind Speed.value': 1,  # use Average
        'Max Wind.value': 1,
        'Mean 10 Wind Speed.value': 1,
        'Time.value': 1,
        'Date.value': 1,
        '_id': 0
    }
    # Query the data from the database
    data = list(collection.find({
        'added': {'$gte': datetime.utcnow() - timedelta(hours=time_range)},
        # 'Average Wind Speed.value': {'$ne': None},
        # 'Max Wind.value': {'$ne': None},
        # 'Time.value': {'$ne': None},
        # 'Date.value': {'$ne': None}
        },
        projection).sort('added', pymongo.DESCENDING))  # first value is the newest
    if not data:
        # Query the latest data from the database
        last = collection.find_one({},
                                   projection,
                                   sort=[('added', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            data = list(collection.find({
                'added': {'$gte': last['added'] - timedelta(hours=time_range)},
                # 'Average Wind Speed.value': {'$ne': None},
                # 'Max Wind.value': {'$ne': None},
                # 'Time.value': {'$ne': None},
                # 'Date.value': {'$ne': None}
                },
                projection, sort=[('added', pymongo.DESCENDING)]))
    # Create the figure
    fig = go.Figure()

    # Get the most recent value
    latest_wdata = data[0]['Average Wind Speed']['value']
    latest_w10data = data[0]['Mean 10 Wind Speed']['value']
    latest_gdata = data[0]['Max Wind']['value']
    # Get the wind and gusts values
    w_speed = [d.get('Average Wind Speed', {}).get('value') for d in data]
    w10_speed = [d.get('Mean 10 Wind Speed', {}).get('value') for d in data]  # [d['Mean 10 Wind Speed']['value'] for d in data]
    g_speed = [d.get('Max Wind', {}).get('value') for d in data]
    # Get the timestamps of the WS
    date_time = [(doc['Date']['value'], doc['Time']['value']) for doc in data]
    timestamps = combine_datetime(date_time)

    # Gust trace
    #if latest_gdata is not None:
    g_name = 'Wind Gusts'
    if latest_gdata >= 60:
        g_name = '<span style="color:red">&#x26a0; Wind Gusts</span>'
    fig.add_trace(go.Scatter(x=timestamps, y=g_speed,
                             name=g_name,
                             hoveron='points',
                             line_color='#86ce00',
                             hovertemplate=('%{x}<br>' + 'Wind Gusts: %{y:.2f} km/h <br><extra></extra> ')
                             )
                  )
    # Change gust graph color if above limit
    if latest_gdata >= 60:
        fig.update_traces(fill='tozeroy', fillcolor='rgba(254,0,206,0.1)', line_color='#fe00ce', opacity=0.1, selector=({'name': g_name}))
        # fill='tonexty' = fill to trace0 y
        # fill='tozeroy' = fill down to xaxis

    # Wind 10' trace
    #if latest_w10data is not None:
    w10_name = "Wind 10' Avg"
    if latest_w10data >= 50:
        w_name = "<span style='color:red'>&#x26a0; Wind 10' Avg</span>"
    fig.add_trace(go.Scatter(x=timestamps, y=w10_speed,
                             name=w10_name,
                             hoveron='points',
                             line_color="rgb(219,112,147)",
                             hovertemplate=("%{x}<br>" + "Wind 10' Avg: %{y:.2f} km/h <br><extra></extra> ")
                             )
                  )
    # Change wind graph color if above limit
    if latest_w10data >= 50:
        fig.update_traces(fill='tozeroy', fillcolor='rgba(255,0,0,0.1)', line_color='red', opacity=0.1, selector=({'name': w10_name}))

    # Wind 1' trace
    #if latest_wdata is not None:
    w_name = 'Wind speed'
    if latest_wdata >= 50:
        w_name = '<span style="color:red">&#x26a0; Wind speed</span>'
    fig.add_trace(go.Scatter(x=timestamps, y=w_speed,
                             name=w_name,
                             hoveron='points',
                             line_color="#316395",
                             hovertemplate=('%{x}<br>' + 'Wind Speed: %{y:.2f} km/h <br><extra></extra> ')
                             )
                  )
    # Change wind graph color if above limit
    if latest_wdata >= 50:
        fig.update_traces(fill='tozeroy', fillcolor='rgba(255,127,14,0.1)', line_color='#ff7f0e', opacity=0.1, selector=({'name': w_name}))

    # Trend trace
    # https://stackoverflow.com/questions/74485762/scikit-learn-linear-regression-using-datetime-values-and-forecasting
    #model = LinearRegression().fit(timestamps, w_speed)
    #y_hat = model.predict(w_speed)
    #fig.add_trace(go.Scatter(x=timestamps, y=y_hat,
    #                         name='Wind trend',
    #                         line_color="black"
    #                         )
    #              )

    fig.update_layout(yaxis_range=[0, 140],
                      uirevision=True,
                      #width=620,
                      #height=400,
                      autosize=False,
                      yaxis_title='km/h',
                      xaxis_tickangle=45,
                      margin_t=2,
                      template='plotly_white',
                      modebar_add=["hovercompare", "v1hovermode"],
                      legend=dict(x=1, y=0.9),
                      )
    fig.update_xaxes(showgrid=False)
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0] < (datetime.utcnow() - timedelta(minutes=5)) else 'green')


# Define the callback function to update the brightness graph
@app.callback([Output('brightness-graph', 'figure'),
               Output('brightness-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('brightness_hour_choice', 'value')])
def update_brightness_graph(n_intervals, time_range):
    projection = {
        'added': 1,
        'Brightness lux.value': 1,
        'Time.value': 1,
        'Date.value': 1,
        '_id': 0
    }
    # Query the data from the database
    data = list(collection.find({
        'added': {'$gte': datetime.utcnow() - timedelta(hours=time_range)},
        # 'Brightness lux.value': {'$ne': None},
        # 'Time.value': {'$ne': None},
        # 'Date.value': {'$ne': None}
        },
        projection, sort=[('added', pymongo.DESCENDING)]))
    if not data:
        # Query the latest data from the database
        last = collection.find_one({},
                                   projection,
                                   sort=[('added', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            data = list(collection.find({
                'added': {'$gte': last['added'] - timedelta(hours=time_range)}},
                projection, sort=[('added', pymongo.DESCENDING)]))

    # Get the brightness values
    press = [d['Brightness lux']['value'] for d in data]
    # create a list of tuple
    date_time = [(doc['Date']['value'], doc['Time']['value']) for doc in data]
    timestamps = combine_datetime(date_time)

    # Create the figure
    dict = {
        'data': [{'x': timestamps, 'y': press}],
        'layout': {
            #'title': f'brightness in the Last {time_range} Hours',
            'xaxis': {'tickangle': 45},
            'yaxis': {'title': 'lux'},
            #'width': 620,
            #'height': 400,
            'autosize': False,
            'margin': {'t': 2},
            'template': 'plotly_white',
        }
    }
    fig = go.Figure(dict)
    fig.update_layout(yaxis_range=[0, 160000],
                      uirevision=True,
                      )
    fig.update_traces(line_color="#316395", hovertemplate=('%{x}<br>' + 'Brightness: %{y:.2f} lux<br><extra></extra> '))
    fig.update_xaxes(showgrid=False)
    # Return the figure
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0] < (datetime.utcnow() - timedelta(minutes=5)) else 'green')


# could check package ROSELY too
# Define the callback function that updates the wind rose plot
@app.callback([Output('wind-rose', 'figure'),
               Output('windrose-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('windrose_hour_choice', 'value')]
              )
def update_wind_rose(n_intervals, time_range):
    # Fetch the wind data from the MongoDB database for the last x hours
    projection = {
        "_id": 0,
        "added": 1,
        "Average Wind Speed.value": 1,
        "Mean Wind Direction.value": 1,
        'Time.value': 1,
        'Date.value': 1,
    }
    datapoints = list(collection.find({
        "added": {"$gte": datetime.utcnow() - timedelta(hours=time_range)},
        # 'Average Wind Speed.value': {'$ne': None},
        # 'Mean Wind Direction.value': {'$ne': None},
        # 'Time.value': {'$ne': None},
        # 'Date.value': {'$ne': None}
        },
        projection, sort=[('added', pymongo.DESCENDING)]))

    if not datapoints:
        # Query the latest data from the database
        last = collection.find_one({},
                                   projection,
                                   sort=[('added', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            datapoints = list(collection.find({
                'added': {'$gte': last['added'] - timedelta(hours=time_range)},
                # 'Average Wind Speed.value': {'$ne': None},
                # 'Mean Wind Direction.value': {'$ne': None},
                # 'Time.value': {'$ne': None},
                # 'Date.value': {'$ne': None}
                },
                projection, sort=[('added', pymongo.DESCENDING)]))

    wind_data = json_normalize(datapoints).rename(columns={'Average Wind Speed.value': 'WindSpd',
                                                           'Mean Wind Direction.value': 'WindDir',
                                                           })

    # Get the WS timestamps
    # using zip() to iterate over both the Date.value and Time.value columns of the pd db simultaneously
    date_time_list = [(date, time) for date, time in zip(wind_data['Date.value'], wind_data['Time.value'])]
    timestamps = combine_datetime(date_time_list)

    # Determine the total number of observations and how many have calm conditions
    total_count = wind_data.shape[0]
    calm_count = wind_data.query("WindSpd == 0").shape[0]

    rose = (wind_data.assign(WindSpd_bins=lambda df:
            pd.cut(df['WindSpd'], bins=spd_bins, labels=spd_labels, right=True))
            .assign(WindDir_bins=lambda df:
                    pd.cut(df['WindDir'], bins=dir_bins, labels=dir_labels, right=False)
                    )
            .replace({'WindDir_bins': {360: 0}})
            .groupby(by=['WindSpd_bins', 'WindDir_bins'])
            .size()
            .unstack(level='WindSpd_bins')
            .fillna(0)
            .assign(calm=lambda df: calm_count / df.shape[0])
            .sort_index(axis=1)
            .applymap(lambda x: x / total_count * 100)
            )
    #print(rose)
    # Create the wind rose plot
    fig = go.Figure()
    for i, col in enumerate(rose.columns):
        fig.add_trace(
            go.Barpolar(
                r=rose[col],
                theta=rose.index.categories,
                name=col,
                marker_color=spd_colors_speed[i],
                hovertemplate="frequency: %{r:.2f}%<br>direction: %{theta:.2f} deg <br> %{text} <extra></extra> ",
            )
        )

    fig.update_layout(
        autosize=False,
        polar_angularaxis_rotation=90,
        polar_angularaxis_direction="clockwise",
        showlegend=True,
        dragmode=False,
        margin=dict(l=20, r=20, t=33, b=20),
        uirevision=True,
        #width=620,
        #height=400,
        #template='plotly_white',
    )
    fig.update_xaxes(showline=True, linewidth=1, linecolor="black", mirror=True)
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", mirror=True)
    fig.update_traces(
        text=[
            "North",
            "N-N-E",
            "N-E",
            "E-N-E",
            "East",
            "E-S-E",
            "S-E",
            "S-S-E",
            "South",
            "S-S-W",
            "S-W",
            "W-S-W",
            "West",
            "W-N-W",
            "N-W",
            "N-N-W",
        ]
    )
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0] < (datetime.utcnow() - timedelta(minutes=5)) else 'green')


# Define the callback function to update the radiation graph
@app.callback([Output('radiation-graph', 'figure'),
               Output('rad-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('rad_hour_choice', 'value')])
def update_radiation_graph(n_intervals, time_range):
    projection = {
        'added': 1,
        'Global Radiation.value': 1,
        'Time.value': 1,
        'Date.value': 1,
        '_id': 0
    }
    # Query the data from the database
    data = list(collection.find({
        'added': {'$gte': datetime.utcnow() - timedelta(hours=time_range)},
        # 'Global Radiation.value': {'$ne': None},
        # 'Time.value': {'$ne': None},
        # 'Date.value': {'$ne': None}
        },
        projection, sort=[('added', pymongo.DESCENDING)]))
    if not data:
        # Query the latest data from the database and avoid having None values
        last = collection.find_one({},
                                   projection,
                                   sort=[('added', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            data = list(collection.find({
                'added': {'$gte': last['added'] - timedelta(hours=time_range)},
                # 'Global Radiation.value': {'$ne': None},
                # 'Time.value': {'$ne': None},
                # 'Date.value': {'$ne': None}
                },
                projection, sort=[('added', pymongo.DESCENDING)]))
    # Get the global radiation values
    rad = [d['Global Radiation']['value'] for d in data]
    # Get the WS timestamps
    date_time = [(doc['Date']['value'], doc['Time']['value']) for doc in data]
    timestamps = combine_datetime(date_time)

    # Create the figure
    dict = {
        'data': [{'x': timestamps, 'y': rad}],
        'layout': {
            #'title': f'Global radiation in the Last {time_range} Hours',
            'xaxis': {'tickangle': 45},
            'yaxis': {'title': 'W/m^2'},
            #'width': 620,
            #'height': 400,
            'autosize': False,
            #"xaxis.autorange": True,
            'margin': {'t': 2},
            'template': 'plotly_white',
        }
    }
    fig = go.Figure(dict)
    fig.update_layout(yaxis_range=[0, 1300],
                      uirevision=True,
                      )
    fig.update_traces(line_color="#316395", hovertemplate=('%{x}<br>' + 'Global Radiation %{y:.2f} W/m^2<br><extra></extra> '))
    fig.update_xaxes(showgrid=False)
    # Return the figure
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0] < (datetime.utcnow() - timedelta(minutes=5)) else 'green')


# Run the app
if __name__ == '__main__':
    #app.run_server(debug=True) # development server
    serve(app.server, host='0.0.0.0', port=5010, threads=100, _quiet=True)
