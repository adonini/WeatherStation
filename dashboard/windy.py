from urllib.parse import urlencode

from dash import html, Input, Output
import dash_bootstrap_components as dbc

LAYERS = {'cloud': ('Clouds', 'clouds'), 'wind': ('Wind', 'wind'),
          'gusts': ('Gusts', 'gust'), 'rain': ('Rain', 'rain')}


def forecast_urls(tab):
    _, overlay = LAYERS.get(tab, LAYERS['cloud'])
    params = dict(type='map', location='coordinates', metricRain='mm',
                  metricTemp='°C', metricWind='km/h', zoom=7, overlay=overlay,
                  product='ecmwf', level='surface', lat=28.5, lon=-16.5,
                  detailLat=28.7666636, detailLon=-17.8833298,
                  marker='true', message='true')
    return ('https://embed.windy.com/embed.html?' + urlencode(params),
            f'https://www.windy.com/?{overlay},28.767,-17.883,7')


def make_windy_card():
    src, link = forecast_urls('cloud')
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.H4('Forecast · Windy', className='my-auto'),
                dbc.Button(html.I(className='bi bi-info-circle'),
                           id='windy-info-icon', n_clicks=0, color='link',
                           className='text-white', title='About these forecasts'),
            ], className='d-flex align-items-center justify-content-between'),
        ], className='text-white bg-primary', style={'width': '100%'}),
        dbc.CardBody([
            dbc.Tabs([dbc.Tab(label=label, tab_id=key) for key, (label, _) in LAYERS.items()],
                     id='card-tabs', active_tab='cloud'),
            html.Iframe(id='windy-forecast-map', src=src,
                        title='Windy ECMWF forecast for the Canary Islands',
                        style={'width': '100%', 'height': '450px', 'border': 0,
                               'display': 'block'}),
        ], style={'padding': 0, 'width': '100%', 'minWidth': 0}),
        dbc.CardFooter([
            html.Div('ECMWF forecast · Use the map timeline to explore the coming hours.',
                     className='small'),
            html.A('Open in Windy ↗', id='windy-external-link', href=link,
                   target='_blank', rel='noopener noreferrer', className='small'),
        ], style={'width': '100%'}),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle('About the forecast')),
            dbc.ModalBody([
                html.P('These maps show ECMWF model forecasts. Use the timeline at the bottom of the map to select the forecast time.'),
                html.Ul([
                    html.Li('Clouds: predicted cloud cover.'),
                    html.Li('Wind: predicted surface wind speed and direction.'),
                    html.Li('Gusts: predicted surface wind gusts.'),
                    html.Li('Rain: predicted precipitation; read the accumulation period on the map.'),
                ]),
                html.P('Open Windy for more forecast controls.'),
            ]),
        ], id='modal_windy', is_open=False, scrollable=True, size='lg'),
    ], className='border rounded p-0 col-cards-2', style={'alignItems': 'stretch', 'minWidth': 0})


def register_windy_callbacks(app):
    @app.callback(Output('windy-forecast-map', 'src'),
                  Output('windy-external-link', 'href'),
                  Input('card-tabs', 'active_tab'), prevent_initial_call=True)
    def change_forecast_layer(active_tab):
        return forecast_urls(active_tab)
