# Set location for Roque de los Muchachos
location_lst = [28.7666636, -17.8833298, 2200]  # lat, long, elevation

# plots configuration
config = {
    'displaylogo': False,  # remove plotly logo
    'modeBarButtonsToRemove': ['resetScale', 'lasso2d', 'select2d'],
    'toImageButtonOptions': {'format': 'png',
                             'filename': 'LST1_WS_plot',
                             'height': None,  # download image at the currently-rendered size
                             'width': None,
                             'scale': 1  # Multiply title/legend/axis/canvas sizes by this factor
                             }
}


# time options for the dropdown menu in the content plots
time_options = [{'label': '1 Hour', 'value': 1},
                {'label': '3 Hours', 'value': 3},
                {'label': '6 Hours', 'value': 6},
                {'label': '12 Hours', 'value': 12},
                {'label': '24 Hours', 'value': 24},
                {'label': '48 Hours', 'value': 48}]

# sidebar style
sidebar_style = {
    "text-align": "center",
    "padding": "2rem 1rem",
    "background-color": "#596568e3",
    "z-index": "5",
}

# Mapping color for wind speed in wind rose
spd_colors_speed = ["#d8d8d8",
                    "#b2f2ff",
                    "#33ddff",
                    "#00aaff",
                    "#0055ff",
                    "#0000ff",
                    "#aa00ff",
                    "#ff00ff",
                    "#cc0000",
                    "#ff6a00",
                    "#ffd500",
                    "#000000"
                    ]


# decode precipitation type
precipitationtype_dict = {0: 'None',
                          40: 'Precipitation present',
                          51: 'Light drizzle',
                          52: 'Moderate drizzle',
                          53: 'Heavy drizzle',
                          61: 'Light rain',
                          62: 'Moderate rain',
                          63: 'Heavy rain',
                          67: 'Light rain with snow',
                          68: 'Moderate rain with snow',
                          70: 'Snowfall',
                          71: 'Light snow',
                          72: 'Moderate snow',
                          73: 'Heavy snow',
                          74: 'Ice pallets',
                          89: 'Heavy hail',
                          }
