from dash import html


# body of the wind rose info modal
info_body = html.Div([
    "A Wind Rose displays the distribution of wind speed and wind direction at a given location. ",
    html.Br(),
    "The rays point to the direction from which the wind is coming from, and their length shows the frequency of that direction.",
    html.Br(),
    "Each concentric circle represents a different frequency, starting from zero at the center to increasing frequencies at the outer circles.",
    html.Br(),
    "The colour depends on the wind speed.",
    html.Br(),
    """One of the scales to estimate wind speed is the Beaufort scale,
    an empirical scale that relates wind speed to observed conditions at sea or on land.""",
    html.Br(),
    """Note that the wind speeds in this scale are mean speeds, averaged over 10 minutes by convention, and do not capture the speed of wind gusts.""",
    html.Br(),
    html.Img(src=('./assets/Beaufortscale.jpeg'), style={"max-width": "100%", "height": "auto"}),
    html.Br(),
    html.Div(["Image from ", html.A("Howtoons", href="https://howtoons.com/The-Beaufort-Scale", className="text-primary", style={"text-decoration": "none"}, target="_blank")], style={"text-align": "center"}),
])

# body of the info modal in the sidebar
summary_body = html.Div([
    "Telescope cannot be operated under certain weather conditions.",
    html.Br(),
    "If a value exceeds the safety limit, it will be highlighted in ",
    html.Span("red", style={'color': 'red'}),
    " and tagged with the symbol ",
    html.I(className=("bi bi-x-octagon"), style={'color': 'red'}),
    ".",
    html.Br(),
    "If instead the value is close to reach the safety limit, it will be displayed in ",
    html.Span("orange", style={'color': 'orange'}),
    " and with the symbol ",
    html.I(className=("bi bi-exclamation-triangle"), style={'color': 'orange'}),
    ".",
    # html.Br(),
    # "Below the actions that have to be taken in case these limits are exceeded during observations.",
    # html.Br(),
    # html.Br(),
    # html.Table([
    #     html.Tr([
    #         html.Th("Condition", style={"font-weight": "bold", "text-align": "center"}),
    #         html.Th("Action", style={"font-weight": "bold", "text-align": "center"})],
    #         style={"border-bottom": "1px solid black"}),
    #     html.Tr([
    #         html.Td("Wind 10' Avg above 36 km/h", style={"padding-right": "40px"}),
    #         html.Td([html.Div("- Telescope to park-out"), html.Div("- Close camera shutter")])],
    #         style={"border-bottom": "1px solid black"}),
    #     html.Tr([
    #         html.Td("Wind gusts above 60 km/h", style={"padding-right": "40px"}),
    #         html.Td([html.Div("- Telescope to park-out"), html.Div("- Close camera shutter")])],
    #         style={"border-bottom": "1px solid black"}),
    #     html.Tr([
    #         html.Td("Humidity above 90%", style={"padding-right": "40px"}),
    #         html.Td([html.Div("- Telescope to park-out"), html.Div("- Close camera shutter")])],
    #         style={"border-bottom": "1px solid black"}),
    #     html.Tr([
    #         html.Td("Precipitation is detected", style={"padding-right": "40px"}),
    #         html.Td([html.Div("- Telescope to park-out"), html.Div("- Close camera shutter")])],
    #         style={"border-bottom": "1px solid black"})
    # ], style={"border-collapse": "collapse", "margin": "auto"}),
    #html.Br(),
    #"In case the weather safety limits are exceeded BEFORE the start of observation, the telescope has to be kept in parking position until weather improves."
])


# body of each modal in the live vaues sidebar section
body_mapping = {
    "Humidity": html.Div([
        "A built-in hygro-thermo sensor with an I2C interface is used to measure temperature and humidity levels.",
        html.Br(),
        html.Br(),
        "Measuring range: 0 ... 100% relative humidity",
        html.Br(),
        "Accuracy: ±1.8% of 10 ... 90%,",
        html.Br(),
        html.Span("±3.0% of 0 ... 100%", style={"display": "inline-block", "margin-left": "73px"}),
        html.Br(),
        "Resolution: 0.1%"
    ]),
    "Wind 1' Avg": html.Div([
        "The wind speed measuring module consists of 4 ultrasonic converters, arranged in pairs of two facing each other via a reflector.",
        html.Br(),
        "The wind measuring values are gliding-averaged over a time span of 1 minute on a base of 100 millisecond values.",
        html.Br(),
        html.Br(),
        "Measuring range: 0.01 ... 60 m/s",
        html.Br(),
        "Accuracy:",
        html.Br(),
        html.Span("- ≤5 m/s: ±0.3 m/s", style={"display": "inline-block", "margin-left": "10px"}),
        html.Br(),
        html.Span("- 5 ... 60 m/s: ±3% of measured value", style={"display": "inline-block", "margin-left": "10px"}),
        html.Br(),
        "Resolution: 0.01 m/s",
    ]),
    "Wind 10' Avg": "Value of the wind data of the previous 10 minutes.",
    "Wind Direction": html.Div([
        "Measuring range: 0 ... 360°",
        html.Br(),
        "Accuracy: ±2.0° with wind speed >2 m/s",
        html.Br(),
        "Resolution: 0.1°",
    ]),
    "Wind Gusts": "Maximum value of the wind velocity (gust) of the previous 1 minute. The gust value is calculated over 3 seconds.",
    "Global Radiation": html.Div([
        "The global radial indicator is calculated with the brightness measurement of the 4 brightness sensors and the elevation angle of the sun position.",
        html.Br(),
        html.Br(),
        "Measuring range: 0 ... 2000 W/m²",
        html.Br(),
        "Accuracy: typ. ± 30 W/m² compared to a Class B pyranometer",
        html.Br(),
        "Resolution: 1 W/m²"
    ]),
    "Rain": html.Div([
        "A Doppler radar module is used to detect precipitation and determine its intensity, quantity, and type. The radar module is mounted on top of the printed board in the device. The intensity of the last minute is extrapolated to one hour for the output.",
        html.Br(),
        "The precipitation intensity is always the moving average of the last minute.",
        html.Br(),
        html.Br(),
        "Measuring ranges:",
        html.Br(),
        html.Span("- Intensities: 0.001 ... 999 mm/h", style={"display": "inline-block", "margin-left": "10px"}),
        html.Br(),
        html.Span("- Resolution intensity: 0.001 mm/h", style={"display": "inline-block", "margin-left": "10px"}),
        html.Br(),
        html.Span("- Daily total: 0.01 ... 999 mm", style={"display": "inline-block", "margin-left": "10px"}),
        html.Br(),
        html.Span("- Resolution daily total: 0.01 mm", style={"display": "inline-block", "margin-left": "10px"})
    ]),
    "Temperature": html.Div([
        "A built-in hygro-thermo sensor with an I2C interface is used to measure temperature and humidity levels.",
        html.Br(),
        html.Br(),
        "Measuring range: -50 ... +80°C",
        html.Br(),
        "Accuracy: ±0.3°C @ 25°C",
        html.Br(),
        html.Span("±0.5°C -45 ... +60°C", style={"display": "inline-block", "margin-left": "75px"}),
        html.Br(),
        html.Span("±1.0°C -50 ... +80°C", style={"display": "inline-block", "margin-left": "75px"}),
        html.Br(),
        "Resolution: 0.1°C"
    ]),
    "Pressure": html.Div([
        "Air pressure is measured with a MEMs sensor.",
        html.Br(),
        html.Br(),
        "Measuring range: 260 ... 1260 hPa",
        html.Br(),
        "Accuracy: typ. ± 0.25 hPa @ -20 ... +80°C @ 800 ... 1100 hPa",
        html.Br(),
        html.Span("typ. ± 0.50 hPa @ -20 ... +80°C @ 600 ... 1100 hPa", style={"display": "inline-block", "margin-left": "73px"}),
        html.Br(),
        html.Span("typ. ± 1.00 hPa @ -50 ... -20°C @ 600 ... 800 hPa", style={"display": "inline-block", "margin-left": "73px"}),
        html.Br(),
        "Resolution: 0.1 hPa"
    ]),
    "Brightness": html.Div([
        "Brightness is measured using 4 individual photo sensors facing the 4 points of the compass at an elevation angle of 50°.",
        html.Br(),
        "The brightness is always averaged over 4 seconds.",
        html.Br(),
        html.Br(),
        "Measuring range: 1 lux ... 150 klux.",
        html.Br(),
        "Accuracy: 3% of relative measured value.",
        html.Br(),
        "Resolution: ~0.3% of measuring value."
    ])
}
