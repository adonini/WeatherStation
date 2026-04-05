import matplotlib
import pandas as pd
import flask
import uuid
import logging
import dash
import dash_bootstrap_components as dbc
import pymongo
from pymongo import MongoClient
import plotly.graph_objects as go
from datetime import datetime, timedelta, time, timezone
from suntime import Sun, SunTimeException
from astropy.coordinates import EarthLocation
import astropy.units as u
from astroplan import Observer
import os
from dotenv import load_dotenv
from waitress import serve
from logging.handlers import TimedRotatingFileHandler
from dash import dcc, html, Input, Output, State
from utils_functions import (convert_meteorological_deg2cardinal_dir, get_magic_values,
                             get_tng_dust_value, toggle_modal, handle_data_gaps,
                             extract_live_values, compute_alert_flags, apply_rain_logic)
from configurations import (location_lst, spd_colors_speed, alert_states_default,
                            rain_alert_timer, min_alert_interval)
from sidebar import sidebar, create_list_group_item, create_list_group_item_alert
from content import (content, dir_bins_local, dir_labels_local, spd_bins, spd_labels,
                     alert_messages, satellite_tab, cloud_tab, thunder_tab,
                     rain_tab)
from navbar import navbar


matplotlib.use('Agg')
load_dotenv('../.env')
log_path = os.environ.get('DASH_LOG_PATH')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT')
db_name = os.environ.get('DB_NAME')
db_coll = "weather"

#---------------------------------------------------------------------------#
# Initialize the main logger
#---------------------------------------------------------------------------#
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)  # override the default severity of logging
# Create handler: new file every day at 08:00 UTC
utc_time = time(8, 0, 0)
file_handler = TimedRotatingFileHandler(log_path + 'dashboard.log', when='D', interval=1, atTime=utc_time, backupCount=7, utc=True)
# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)
# Add handlers to the logger
logger.addHandler(file_handler)

#---------------------------------------------------------------------------#
# Connect to MongoDB
#---------------------------------------------------------------------------#
try:
    client = MongoClient("mongodb://" + db_host + ":" + db_port)
    mydb = client[db_name]
    collection = mydb[db_coll]
except Exception:
    logger.exception("Failed to connect to MongoDB.")


# Instantiate Dash and Exposing the Flask Server
# meta_tags arguments allow controlling the size of the app component through different devices size
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"
server = flask.Flask(__name__)
app = dash.Dash(server=server, update_title=None, suppress_callback_exceptions=True, title='LST-1 Weather Station',
                external_stylesheets=[dbc.themes.SANDSTONE, FONT_AWESOME, dbc.icons.BOOTSTRAP, dbc.icons.FONT_AWESOME],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.5, minimum-scale=0.5'},
                           {'http-equiv': 'refresh', 'content': '840'}],  # automatic refresh of the html page every 14min to avoid stalling in case server is down
                )


##########################
# Helper functions
##########################
def build_alert_message(flags):
    wind_combined = flags["wind"] or flags["gust"]

    if flags["strong_wind"]:
        return alert_messages.get((True, False, False, True), '')

    key = (flags["humidity"], wind_combined, flags["rain"])
    return alert_messages.get(key, "Combination not found in alert messages")


def any_alert_active(flags):
    return any([
        flags["humidity"],
        flags["wind"],
        flags["gust"],
        flags["rain"],
        flags["strong_wind"],
    ])


def build_live_values(values, timestamps, cloud_value, tran9_value, tng_dust_value):
    bright = values["bright"]
    bright_lux = values["bright_lux"]

    return [
        create_list_group_item("Humidity", values["hum"], ' %', timestamps),
        create_list_group_item("Wind 1' Avg", values["w_speed"], ' km/h', timestamps),
        create_list_group_item("Wind 10' Avg", values["w10_speed"], ' km/h', timestamps),
        create_list_group_item("Wind Gusts", values["g_speed"], ' km/h', timestamps),
        create_list_group_item("Wind Direction", values["w_dir"], f" ° ({convert_meteorological_deg2cardinal_dir(values['w_dir'])})", timestamps),
        create_list_group_item("Temperature", values["temp"], ' °C', timestamps),
        create_list_group_item("TNG Dust", tng_dust_value, ' µg/m3', timestamps),
        create_list_group_item("Rain", values["p_type_display"], '', timestamps),
        create_list_group_item("Rain Intensity", values["p_int_display"], ' mm/h', timestamps),
        create_list_group_item("Acc. Rain", values["p_acc"], ' mm/d', timestamps),
        create_list_group_item("MAGIC Cloudiness", cloud_value, '', timestamps),
        create_list_group_item("MAGIC Trans@9km", tran9_value, '', timestamps),
        create_list_group_item("Dew Point Temperature", values["dew"], ' °C', timestamps),
        create_list_group_item("Global Radiation", values["rad"], ' W/m2', timestamps),
        create_list_group_item("Pressure", values["press"], ' hPa', timestamps),
        create_list_group_item("Brightness", bright_lux, ' lux', timestamps)
        if bright is not None and bright <= 1
        else create_list_group_item("Brightness", bright, ' klux', timestamps),
    ]


def apply_live_value_alert_styles(live_values, values, flags):
    if flags["humidity"]:
        live_values[0] = create_list_group_item_alert("Humidity", values["hum"], ' %')
    elif flags["humidity_warning"]:
        live_values[0] = create_list_group_item_alert(
            "Humidity", values["hum"], ' %',
            badge_color='warning', row_color='warning'
        )

    if flags["wind"]:
        live_values[2] = create_list_group_item_alert("Wind 10' Avg", values["w10_speed"], ' km/h')
    elif flags["wind_warning"]:
        live_values[2] = create_list_group_item_alert(
            "Wind 10' Avg", values["w10_speed"], ' km/h',
            badge_color='warning', row_color='warning'
        )

    if flags["gust"]:
        live_values[3] = create_list_group_item_alert("Wind Gusts", values["g_speed"], ' km/h')
    elif flags["gust_warning"]:
        live_values[3] = create_list_group_item_alert(
            "Wind Gusts", values["g_speed"], ' km/h',
            badge_color='warning', row_color='warning'
        )

    if flags["rain"]:
        live_values[7] = create_list_group_item_alert("Rain", values["p_type_display"], '')
        live_values[8] = create_list_group_item_alert("Rain Intensity", values["p_int_display"], ' mm/h')

    return live_values


def update_audio_state(alert_states, flags, time_now):
    audio_triggers = []
    new_trigger = False

    audio_conditions = {
        "humidity": flags["humidity"],
        "wind": flags["wind"] or flags["gust"],
        "rain": flags["rain"],
    }

    for alert_type, is_active in audio_conditions.items():
        state = alert_states[alert_type]

        if is_active and not state['active']:
            state['active'] = True
            state['timestamp'] = time_now.isoformat()
            audio_triggers.append(alert_type)
            new_trigger = True

        elif not is_active and state['active']:
            state['active'] = False
            state['timestamp'] = None

        elif is_active and state['active']:
            timestamp_datetime = datetime.strptime(
                state['timestamp'], '%Y-%m-%dT%H:%M:%S.%f%z'
            )
            elapsed_time = (time_now - timestamp_datetime).total_seconds()

            if elapsed_time >= min_alert_interval[alert_type]:
                audio_triggers.append(alert_type)
                state['timestamp'] = time_now.isoformat()

    if new_trigger:
        for alert_type in audio_conditions:
            if alert_states[alert_type]['active']:
                alert_states[alert_type]['timestamp'] = time_now.isoformat()

    return alert_states, audio_triggers


######################
# Set the page layout
######################
app.layout = html.Div([
    dcc.Store(id='alert-store', data=alert_states_default),  # Store to keep alert states, initialized with the default one
    dcc.Store(id='audio-triggers', data=[]),
    dcc.Store(id='rain-store', data=rain_alert_timer),  # store to keep rain alerts, initialized with the default one
    html.Audio(id='audio-element', controls=False, autoPlay=True, style={'display': 'none'}),
    navbar,
    html.Hr(className="mt-0"),
    dbc.Row([
        dbc.Col(sidebar, className="col-12 col-s p-0"),
        dbc.Col([
            html.Div(id="red-alert",
                     style={"margin-bottom": "5px", "background-color": "red", "color": "white", "font-size": "28px", "text-align": "center", "padding": "10px", "height": "auto"},
                     hidden=True),  # Initially hidden, pops up only with non safe weather conditions
            content],
            className="justify-content-around col-12 col-c"),
        dcc.Interval(
            id='interval-day-change',
            interval=24 * 60 * 60 * 1000,  # 1 day in milliseconds, maybe not needed this interval.
            n_intervals=0
        )
    ]),
    #html.Hr(className="m-0"),
    dbc.Row([
        html.Div([
            html.P([
                html.Small('Large Size Telescope', className="text-secondary"),
                html.Br(),
                html.A(html.Span('About', style={"font-size": "13px", "text-decoration": "none"}), href="https://www.lst1.iac.es/index.html", target="_blank", className="text-primary", style={"margin-top": "5px"})
            ])
        ])
    ])
], className="container-fluid dbc")


######################
# Callback functions
######################
# Callback to update the time and date every 20sec
@app.callback(
    [Output('current-time', 'children'),
     Output('current-date', 'children')],
    [Input('interval-livevalues', 'n_intervals')]
)
def update_date_time(n_intervals):
    utc_now = datetime.now(timezone.utc)
    return f"{utc_now.time().strftime('%H:%M:%S %Z')} UTC", f"{utc_now.date().strftime('%d-%m-%Y %Z')}"


# callback to update moon data every day
@app.callback(
    #dash.dependencies.Output('moon-visibility', 'children'),
    #dash.dependencies.Output('moon-phase', 'children'),
    [Output('moon-illumination', 'children'),
     Output('moon-rise', 'children'),
     Output('moon-set', 'children')],
    [Input('interval-day-change', 'n_intervals')]
)
def update_moon(n_intervals):
    location = EarthLocation(lat=location_lst[0] * u.deg, lon=location_lst[1] * u.deg, height=location_lst[2] * u.m)
    now = datetime.now(timezone.utc)
    obs = Observer(location=location, timezone="UTC")
    moon_illumination = obs.moon_illumination(now) * 100
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


# update sunrise, sunset and moon data every day
@app.callback(
    [Output('sunrise-time', 'children'),
     Output('sunset-time', 'children')],
    [Input('interval-day-change', 'n_intervals')]
)
def update_sun(n_intervals):
    try:
        # Create a Sun object
        sun = Sun(location_lst[0], location_lst[1])
        # Get today's sunrise and sunset in UTC
        today_sr = sun.get_sunrise_time()
        today_ss = sun.get_sunset_time()
        return f"{today_sr.strftime('%H:%M')} UTC", f"{today_ss.strftime('%H:%M')} UTC"
    except SunTimeException as e:
        logger.error(f"Couldn't calculate sun rising and setting time! Error: {e}")
        return 'n/a', 'n/a'


# update the live values every 20 seconds
@app.callback([Output('live-values', 'children'),
               Output('live-timestamp', 'children'),
               Output('red-alert', 'hidden'),
               Output('red-alert', 'children'),
               Output('alert-store', 'data'),
               Output('audio-triggers', 'data'),
               Output('rain-store', 'data')],
              [Input('interval-livevalues', 'n_intervals')],
              [State('alert-store', 'data'),
               State('rain-store', 'data')])
def update_live_values(n_intervals, alert_states_store, rain_timer):
    alert_states = alert_states_store
    rain_alert_timer = rain_timer

    time_now = datetime.now(timezone.utc)
    latest_data = collection.find_one(sort=[('timestamp', pymongo.DESCENDING)])

    if not latest_data:
        return [], dbc.Badge("No data", color="secondary"), True, "", alert_states, [], rain_alert_timer

    timestamps = latest_data['timestamp']
    cloud_value, tran9_value = get_magic_values()
    tng_dust_value = get_tng_dust_value()

    values = extract_live_values(latest_data)
    flags = compute_alert_flags(values)
    values, flags, rain_alert_timer = apply_rain_logic(values, flags, rain_alert_timer, time_now)

    is_alert = any_alert_active(flags)
    message = build_alert_message(flags)

    live_values = build_live_values(values, timestamps, cloud_value, tran9_value, tng_dust_value)

    if timestamps.replace(tzinfo=timezone.utc) > (time_now - timedelta(minutes=2)):
        live_values = apply_live_value_alert_styles(live_values, values, flags)

    alert_states, audio_triggers = update_audio_state(alert_states, flags, time_now)

    badge = dbc.Badge(
        f"Last update: {timestamps.strftime('%Y-%m-%d %H:%M:%S')}",
        color='secondary' if timestamps.replace(tzinfo=timezone.utc) < (time_now - timedelta(minutes=2)) else 'green',
        className="text-wrap fw-light"
    )

    return [live_values,
            badge,
            not is_alert,
            message,
            alert_states,
            audio_triggers,
            rain_alert_timer
            ]


# callback to play alert audio
@app.callback(Output('audio-element', 'src'),
              Input('audio-triggers', 'data'))
def play_audio(audio_triggers):
    try:
        if not audio_triggers:
            logger.info('No audio triggers. Skipping audio playback.')
            return None
        logger.info('Playing alert and update each timestamp of active alerts')
        audio_file = "assets/general_alert.wav"
        return audio_file
    except Exception as e:
        logger.error(f'Error setting audio source: {str(e)}')
        return None


# callback  to update the temp graph
@app.callback([Output('temp-graph', 'figure'),
               Output('temp-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('temp_hour_choice', 'value'),
               Input('Temperature-refresh-button', 'n_clicks')])
def update_temp_graph(n_intervals, time_range, refresh_clicks):
    # Define the projection to query only the required fields
    projection = {
        'timestamp': 1,
        'Air_Temperature': 1,
        'Dew_Point_Temperature': 1,
        '_id': 0
    }
    utc_now = datetime.now(timezone.utc)
    data = list(collection.find({'timestamp': {'$gte': utc_now - timedelta(hours=time_range)}},
                                projection, sort=[('timestamp', pymongo.DESCENDING)]))

    if not data:
        # Query the latest data from the database
        last = collection.find_one({},
                                   projection,
                                   sort=[('timestamp', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            data = list(collection.find({'timestamp': {'$gte': last['timestamp'] - timedelta(hours=time_range)}},
                                        projection, sort=[('timestamp', pymongo.DESCENDING)]))
    # Get the temperature values and the dew-point values
    temps = [d.get('Air_Temperature') for d in data]
    dews = [d.get('Dew_Point_Temperature') for d in data]
    timestamps = [doc['timestamp'] for doc in data]

    # correct for data missing for >2min so that no line in connecting the dots is shown in that case
    new_timestamps, new_temps, new_dews = handle_data_gaps(timestamps, temps, dews)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=new_timestamps, y=new_temps,
                             name='Temperature',
                             line_color="#316395",
                             hovertemplate=('%{x}<br>' + 'Temperature: %{y:.2f} °C <br><extra></extra> '),
                             connectgaps=False))

    # Add dew-point temp to the plot
    fig.add_trace(go.Scatter(x=new_timestamps, y=new_dews,
                             name='Dew Point',
                             line_color='firebrick',
                             line_dash='dot',
                             hovertemplate=('%{x}<br>' + 'Dew Point: %{y:.2f} °C <br><extra></extra> '),
                             connectgaps=False,
                             )
                  )
    fig.update_layout(yaxis_range=[-30, 30],
                      uirevision=True,
                      autosize=True,
                      yaxis_title='Temperature [°C]',
                      xaxis_tickangle=45,
                      margin_t=20,
                      margin_r=20,
                      template='plotly_white',
                      legend=dict(orientation="h", yanchor="bottom",
                                  y=1.02, xanchor="right", x=1),
                      modebar_add=["hovercompare", "v1hovermode"],
                      modebar_orientation="v",
                      )
    fig.update_xaxes(showgrid=False)

    # Check if the refresh button was clicked
    ctx = dash.callback_context
    button_id = 'Temperature-refresh-button'
    if button_id in ctx.triggered[0]['prop_id']:
        # Reset the zoom by setting 'uirevision' to a unique value
        fig.update_layout(uirevision=str(uuid.uuid4()))
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0].replace(tzinfo=timezone.utc) < (utc_now - timedelta(minutes=5)) else 'green', className="fw-light")


# callback to update the humidity graph
@app.callback([Output('humidity-graph', 'figure'),
               Output('hum-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('hum_hour_choice', 'value'),
               Input('Humidity-refresh-button', 'n_clicks')])
def update_hum_graph(n_intervals, time_range, refresh_clicks):
    projection = {
        'timestamp': 1,
        'Relative_Humidity': 1,
        '_id': 0
    }
    utc_now = datetime.now(timezone.utc)
    data = list(collection.find({'timestamp': {'$gte': utc_now - timedelta(hours=time_range)}},
                                projection).sort('timestamp', pymongo.DESCENDING))  # first value is the newest
    if not data:
        # Query the latest data from the database
        last = collection.find_one({},
                                   projection,
                                   sort=[('timestamp', pymongo.DESCENDING)])
        if last:
            # Retrieve all the data starting from the latest data
            data = list(collection.find({'timestamp': {'$gte': last['timestamp'] - timedelta(hours=time_range)}},
                                        projection, sort=[('timestamp', pymongo.DESCENDING)]))

    # Get the most recent value
    latest_data = data[0].get('Relative_Humidity')
    hums = [d.get('Relative_Humidity') for d in data]
    timestamps = [doc['timestamp'] for doc in data]

    # correct for data missing for >2min so that no line in connecting the dots in that case
    new_timestamps, new_hums = handle_data_gaps(timestamps, hums)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=new_timestamps, y=new_hums,
                             name='Humidity',
                             hoveron='points',
                             line_color="#316395",
                             hovertemplate=('%{x}<br>' + 'Humidity: %{y:.2f} %<br><extra></extra> '),
                             connectgaps=False,
                             )
                  )

    yaxis_tickvals = [0, 20, 40, 60, 80, 90, 100]
    yaxis_ticktext = [str(val) for val in yaxis_tickvals]
    fig.update_layout(yaxis_range=[0, 100],
                      uirevision=True,  # stay zoomed in with an update
                      autosize=True,
                      yaxis_title='Humidity [%]',
                      xaxis_tickangle=45,
                      margin_t=20,
                      margin_r=20,
                      modebar_orientation="v",
                      template='plotly_white',
                      yaxis_ticks="outside",
                      yaxis_tickmode="array",
                      yaxis_tickvals=yaxis_tickvals,
                      yaxis_ticktext=yaxis_ticktext,
                      )
    fig.update_xaxes(showgrid=False)

    # Change graph color if above limit if timestamps are up to date
    latest_ts = timestamps[0].replace(tzinfo=timezone.utc)
    if latest_ts and latest_ts > (utc_now - timedelta(minutes=5)):
        if latest_data >= 90:
            fig.update_traces(fill='tonexty', line_color='red')
        if 80 <= latest_data < 90:
            fig.update_traces(fill='tonexty', line_color='orange')

    # Check if the refresh button was clicked
    ctx = dash.callback_context
    button_id = 'Humidity-refresh-button'
    if button_id in ctx.triggered[0]['prop_id']:
        # Reset the zoom by setting 'uirevision' to a unique value
        fig.update_layout(uirevision=str(uuid.uuid4()))
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0].replace(tzinfo=timezone.utc) < (utc_now - timedelta(minutes=5)) else 'green', className="fw-light")


# callback to update the wind graph
@app.callback([Output('wind-graph', 'figure'),
               Output('wind-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('wind_hour_choice', 'value'),
               Input('Wind Speed-refresh-button', 'n_clicks')])
def update_wind_graph(n_intervals, time_range, refresh_clicks):
    projection = {
        'timestamp': 1,
        'Average_Wind_Speed': 1,
        'Max_Wind': 1,
        'Mean_10_Wind_Speed': 1,
        '_id': 0
    }
    utc_now = datetime.now(timezone.utc)
    # Query the data from the database
    data = list(collection.find({'timestamp': {'$gte': utc_now - timedelta(hours=time_range)}},
                                projection).sort('timestamp', pymongo.DESCENDING))  # first value is the newest
    if not data:
        # Query the latest data from the database
        last = collection.find_one({},
                                   projection,
                                   sort=[('timestamp', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            data = list(collection.find({'timestamp': {'$gte': last['timestamp'] - timedelta(hours=time_range)}},
                                        projection, sort=[('timestamp', pymongo.DESCENDING)]))

    fig = go.Figure()

    # Get the most recent value
    latest_w10data = data[0].get('Mean_10_Wind_Speed')
    latest_gdata = data[0].get('Max_Wind')
    # Get the wind and gusts values
    w_speed = [d.get('Average_Wind_Speed') for d in data]
    w10_speed = [d.get('Mean_10_Wind_Speed') for d in data]
    g_speed = [d.get('Max_Wind') for d in data]

    timestamps = [doc['timestamp'] for doc in data]

    # correct for data missing for >2min so that no line in connecting the dots in that case
    new_timestamps, new_w_speed, new_w10_speed, new_g_speed = handle_data_gaps(timestamps, w_speed, w10_speed, g_speed)

    # Wind 1' trace
    w_name = "Wind 1' Avg"
    fig.add_trace(go.Scatter(x=new_timestamps, y=new_w_speed,
                             name=w_name,
                             hoveron='points',
                             line_color="#316395",
                             hovertemplate=("%{x}<br>" + "Wind 1' Avg: %{y:.2f} km/h <br><extra></extra> "),
                             connectgaps=False))

    # Gust trace
    g_name = 'Wind Gusts'
    if latest_gdata >= 60:
        g_name = '<span style="color:red">&#x26a0; Wind Gusts</span>'
    fig.add_trace(go.Scatter(x=new_timestamps, y=new_g_speed,
                             name=g_name,
                             hoveron='points',
                             line_color='#86ce00',
                             hovertemplate=('%{x}<br>' + 'Wind Gusts: %{y:.2f} km/h <br><extra></extra> '),
                             connectgaps=False,
                             )
                  )
    # Change gust graph color if above limit
    if latest_gdata >= 60:
        fig.update_traces(fill='tozeroy', fillcolor='rgba(254,0,206,0.1)', line_color='#fe00ce', opacity=0.1, selector=({'name': g_name}))
        # fill='tonexty' = fill to trace0 y
        # fill='tozeroy' = fill down to xaxis

    # Wind 10' trace
    w10_name = "Wind 10' Avg"
    if latest_w10data >= 36:
        w10_name = '<span style="color:red">&#x26a0; Wind 10\' Avg </span>'
    fig.add_trace(go.Scatter(x=new_timestamps, y=new_w10_speed,
                             name=w10_name,
                             hoveron='points',
                             line_color="rgb(219,112,147)",
                             hovertemplate=("%{x}<br>" + "Wind 10' Avg: %{y:.2f} km/h <br><extra></extra> "),
                             connectgaps=False,
                             )
                  )
    # Change wind 10' graph color if above limit
    if latest_w10data >= 36:
        fig.update_traces(fill='tozeroy', fillcolor='rgba(255,0,0,0.1)', line_color='red', opacity=0.1, selector=({'name': w10_name}))

    yaxis_tickvals = [0, 20, 36, 40, 60, 80, 100, 120, 140]
    yaxis_ticktext = [str(val) for val in yaxis_tickvals]
    fig.update_layout(yaxis_range=[0, 140],
                      uirevision=True,
                      autosize=True,
                      yaxis_title='Wind speed [km/h]',
                      xaxis_tickangle=45,
                      margin_t=20,
                      margin_r=20,
                      template='plotly_white',
                      modebar_add=["hovercompare", "v1hovermode"],
                      modebar_orientation="v",
                      legend=dict(orientation="h", yanchor="bottom",
                                  y=1.02, xanchor="right", x=1),
                      yaxis_ticks="outside",
                      yaxis_tickmode="array",
                      yaxis_tickvals=yaxis_tickvals,
                      yaxis_ticktext=yaxis_ticktext,
                      )
    fig.update_xaxes(showgrid=False)

    # Check if the refresh button was clicked
    ctx = dash.callback_context
    button_id = 'Wind Speed-refresh-button'
    if button_id in ctx.triggered[0]['prop_id']:
        # Reset the zoom by setting 'uirevision' to a unique value
        fig.update_layout(uirevision=str(uuid.uuid4()))
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0].replace(tzinfo=timezone.utc) < (utc_now - timedelta(minutes=5)) else 'green', className="fw-light")


# could check package ROSELY too
# https://gist.github.com/phobson/41b41bdd157a2bcf6e14
# Define the callback function that updates the wind rose plot
@app.callback([Output('wind-rose', 'figure'),
               Output('windrose-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('windrose_hour_choice', 'value'),
               Input('Wind Rose-refresh-button', 'n_clicks')]
              )
def update_wind_rose(n_intervals, time_range, refresh_clicks):
    # Fetch the wind data from the MongoDB database for the last x hours
    projection = {
        "_id": 0,
        "timestamp": 1,
        "Mean_10_Wind_Speed": 1,
        "Mean_Wind_Direction": 1,
    }
    utc_now = datetime.now(timezone.utc)
    datapoints = list(collection.find({"timestamp": {"$gte": utc_now - timedelta(hours=time_range)}},
                                      projection, sort=[('timestamp', pymongo.DESCENDING)]))

    if not datapoints:
        # Query the latest data from the database
        last = collection.find_one({},
                                   projection,
                                   sort=[('timestamp', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            datapoints = list(collection.find({'timestamp': {'$gte': last['timestamp'] - timedelta(hours=time_range)}},
                                              projection, sort=[('timestamp', pymongo.DESCENDING)]))

    wind_data = pd.DataFrame(datapoints).rename(columns={
        'Mean_10_Wind_Speed': 'WindSpd',
        'Mean_Wind_Direction': 'WindDir'})
    timestamps = wind_data['timestamp'].tolist()

    # Drop rows with missing values
    wind_data = wind_data.dropna(subset=['WindSpd', 'WindDir'])

    if wind_data.empty:
        return go.Figure(), dbc.Badge("No valid data", color="secondary", className="fw-light")

    # Normalize directions so 348.75..360 wraps into the North bin
    wind_data["WindDirAdj"] = wind_data["WindDir"].where(
        wind_data["WindDir"] < 348.75,
        wind_data["WindDir"] - 360
    )

    wind_data["WindSpd_bins"] = pd.cut(
        wind_data["WindSpd"],
        bins=spd_bins,
        labels=spd_labels,
        right=True
    )

    wind_data["WindDir_bins"] = pd.cut(
        wind_data["WindDirAdj"],
        bins=dir_bins_local,
        labels=dir_labels_local,
        right=False,
        include_lowest=True
    )

    # Determine the total number of observations and how many have calm conditions
    total_count = wind_data.shape[0]
    calm_count = wind_data.query("WindSpd < 1").shape[0]

    rose = (
        wind_data
        .groupby(by=['WindSpd_bins', 'WindDir_bins'], observed=False)
        .size()
        .unstack(level='WindSpd_bins')
        .fillna(0)
        .assign(calm=lambda df: calm_count / df.shape[0])
        .sort_index(axis=1)
    )

    rose = rose / total_count * 100

    fig = go.Figure()
    #print(rose.columns)
    for i, col in enumerate(rose.columns):
        fig.add_trace(
            go.Barpolar(
                r=rose[col],
                theta=rose.index.categories,
                name=col,
                marker_color=spd_colors_speed[i],
                marker_line_color="darkgray",
                marker_line_width=1,
                #opacity=0.8,
                hovertemplate=("Frequency: %{r:.2f}%<br>"
                               "Direction: %{theta:.1f} deg (%{text})<br>"
                               "Speed: %{customdata}<extra></extra>"),
                customdata=[col] * len(rose.index.categories),
            )
        )

    fig.update_layout(
        autosize=True,
        polar_angularaxis_direction="clockwise",
        showlegend=True,
        dragmode=False,
        margin=dict(l=35, r=0, t=20, b=20),
        uirevision=True,
        #polar=dict(radialaxis=dict(showticklabels=False)),
        polar_radialaxis_ticksuffix='%',
        polar_radialaxis_showline=False,
        polar_radialaxis_tickangle=45,
        polar_radialaxis_ticks="",
        polar_angularaxis_rotation=90,
        polar_angularaxis_showline=True,
        polar_angularaxis_ticks="",
        polar_radialaxis_gridcolor='lightgray',
        polar_angularaxis_linecolor='lightgray',
        legend=dict(title="<b>Beaufort scale<b>", y=0.9),
        template=None,
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

    # Check if the refresh button was clicked
    ctx = dash.callback_context
    button_id = 'Wind Rose-refresh-button'
    if button_id in ctx.triggered[0]['prop_id']:
        # Reset the zoom by setting 'uirevision' to a unique value
        fig.update_layout(uirevision=str(uuid.uuid4()))
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0].replace(tzinfo=timezone.utc) < (utc_now - timedelta(minutes=5)) else 'green', className="fw-light")


# Define the callback function to update the radiation graph
@app.callback([Output('radiation-graph', 'figure'),
               Output('rad-timestamp', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('rad_hour_choice', 'value'),
               Input('Global Radiation-refresh-button', 'n_clicks')])
def update_radiation_graph(n_intervals, time_range, refresh_clicks):
    projection = {
        'timestamp': 1,
        'Global_Radiation': 1,
        '_id': 0
    }
    utc_now = datetime.now(timezone.utc)
    # Query the data from the database
    data = list(collection.find({'timestamp': {'$gte': utc_now - timedelta(hours=time_range)}},
                                projection, sort=[('timestamp', pymongo.DESCENDING)]))
    if not data:
        # Query the latest data from the database and avoid having None values
        last = collection.find_one({},
                                   projection,
                                   sort=[('timestamp', pymongo.DESCENDING)]
                                   )
        if last:
            # Retrieve all the data starting from the latest data
            data = list(collection.find({'timestamp': {'$gte': last['timestamp'] - timedelta(hours=time_range)}},
                                        projection, sort=[('timestamp', pymongo.DESCENDING)]))
    # Get the global radiation values
    rad = [d.get('Global_Radiation') for d in data]
    timestamps = [doc['timestamp'] for doc in data]

    # correct for data missing for >2min so that no line in connecting the dots in that case
    new_timestamps, new_rad = handle_data_gaps(timestamps, rad)

    # Create the figure
    dict = {
        'data': [{'x': new_timestamps, 'y': new_rad}],
        'layout': {
            #'title': f'Global radiation in the Last {time_range} Hours',
            'xaxis': {'tickangle': 45},
            'yaxis': {'title': 'Global radiation [W/m^2]'},
            #'width': 620,
            #'height': 400,
            'autosize': True,
            #"xaxis.autorange": True,
            'margin': {'t': 20, 'r': 20},
            'template': 'plotly_white',
        }
    }
    fig = go.Figure(dict)
    fig.update_layout(yaxis_range=[0, 1300],
                      uirevision=True,
                      modebar_orientation="v",
                      )
    fig.update_traces(line_color="#316395", hovertemplate=('%{x}<br>' + 'Global Radiation: %{y:.2f} W/m^2<br><extra></extra> '), connectgaps=False)
    fig.update_xaxes(showgrid=False)

    # Check if the refresh button was clicked
    ctx = dash.callback_context
    button_id = 'Global Radiation-refresh-button'
    if button_id in ctx.triggered[0]['prop_id']:
        # Reset the zoom by setting 'uirevision' to a unique value
        fig.update_layout(uirevision=str(uuid.uuid4()))
    return fig, dbc.Badge(f"Last update: {timestamps[0]}", color='secondary' if timestamps[0].replace(tzinfo=timezone.utc) < (utc_now - timedelta(minutes=5)) else 'green', className="fw-light")


# Modals updates
app.callback(
    Output("modal_Humidity", "is_open"),
    Input("open_Humidity", "n_clicks"),
    #Input("close_Humidity", "n_clicks"),
    State("modal_Humidity", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Wind 1' Avg", "is_open"),
    Input("open_Wind 1' Avg", "n_clicks"),
    #Input("close_Wind Speed", "n_clicks"),
    State("modal_Wind 1' Avg", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Wind 10' Avg", "is_open"),
    Input("open_Wind 10' Avg", "n_clicks"),
    #Input("close_Wind 10' Avg", "n_clicks"),
    State("modal_Wind 10' Avg", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Wind Gusts", "is_open"),
    Input("open_Wind Gusts", "n_clicks"),
    #Input("close_Max Wind Speed", "n_clicks"),
    State("modal_Wind Gusts", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Wind Direction", "is_open"),
    Input("open_Wind Direction", "n_clicks"),
    #Input("close_Wind Direction", "n_clicks"),
    State("modal_Wind Direction", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Temperature", "is_open"),
    Input("open_Temperature", "n_clicks"),
    #Input("close_Air Temperature", "n_clicks"),
    State("modal_Temperature", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Brightness", "is_open"),
    Input("open_Brightness", "n_clicks"),
    #Input("close_Brightness", "n_clicks"),
    State("modal_Brightness", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Global Radiation", "is_open"),
    Input("open_Global Radiation", "n_clicks"),
    #Input("close_Global Radiation", "n_clicks"),
    State("modal_Global Radiation", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Rain", "is_open"),
    Input("open_Rain", "n_clicks"),
    State("modal_Rain", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Pressure", "is_open"),
    Input("open_Pressure", "n_clicks"),
    State("modal_Pressure", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_Wind Rose", "is_open"),
    Input("Wind Rose-info-icon", "n_clicks"),
    State("modal_Wind Rose", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_summary", "is_open"),
    Input("summary-info-icon", "n_clicks"),
    State("modal_summary", "is_open"),
)(toggle_modal)

app.callback(
    Output("modal_windy", "is_open"),
    Input("windy-info-icon", "n_clicks"),
    State("modal_windy", "is_open"),
)(toggle_modal)


# callback to enable or disable the intervals based on their respective states in case a modal is open
@app.callback(
    [Output('interval-component', 'disabled'),
     Output('interval-livevalues', 'disabled')],
    [Input("modal_Wind 1' Avg", "is_open"),
     Input("modal_Humidity", "is_open"),
     Input("modal_Wind 10' Avg", "is_open"),
     Input("modal_Wind Gusts", "is_open"),
     Input("modal_Wind Direction", "is_open"),
     Input("modal_Temperature", "is_open"),
     Input("modal_Brightness", "is_open"),
     Input("modal_Global Radiation", "is_open"),
     Input("modal_Rain", "is_open"),
     Input("modal_Pressure", "is_open"),
     Input("modal_Wind Rose", "is_open"),
     Input("modal_summary", "is_open"),
     Input("modal_windy", "is_open")],
    [State('interval-component', 'disabled'),
     State('interval-livevalues', 'disabled')],
)
def update_intervals(is_open_wind_speed, is_open_humidity, is_open_wind_avg, is_open_Wind_Gusts, is_open_wind_direction,
                     is_open_temperature, is_open_brightness, is_open_global_radiation, is_open_Rain,
                     is_open_pressure, is_open_windrose, is_open_summary, is_open_windy, interval1_disabled, interval2_disabled):
    if any([is_open_wind_speed, is_open_humidity, is_open_wind_avg, is_open_Wind_Gusts, is_open_wind_direction,
            is_open_temperature, is_open_brightness, is_open_global_radiation, is_open_Rain,
            is_open_pressure, is_open_windrose, is_open_summary, is_open_windy]):
        interval1_disabled = True
        interval2_disabled = True
    else:
        interval1_disabled = False
        interval2_disabled = False
    return interval1_disabled, interval2_disabled


@app.callback(Output("card-content", "children"),
              [Input('interval-component', 'n_intervals'),
               Input("card-tabs", "active_tab")])
def windy_tab(n_intervals, active_tab):
    if active_tab == "satellite":
        return satellite_tab
    elif active_tab == "cloud":
        return cloud_tab
    elif active_tab == "thunderstorm":
        return thunder_tab
    elif active_tab == "rain":
        return rain_tab


# Run the app
if __name__ == '__main__':
    #app.run_server(debug=True)  # development server
    serve(app.server, host='0.0.0.0', port=5010, threads=100, _quiet=True)
