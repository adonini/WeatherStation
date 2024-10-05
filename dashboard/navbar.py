import dash_bootstrap_components as dbc
from dash import html

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
    dbc.DropdownMenuItem("AEMET ORM Predictions", href="https://www.aemet.es/documentos/es/eltiempo/prediccion/montana/boletin_montana/BM_Caldera_Taburiente.pdf", className="text-primary text-capitalize", target="_blank", external_link=True),
    dbc.DropdownMenuItem("Mountain Forecast", href="https://www.mountain-forecast.com/peaks/Roque-de-los-Muchachos/forecasts/2423", className="text-primary text-capitalize", target="_blank", external_link=True),
], direction='down', align_end=True, label="Menu", style={'zindex': '999'})

navbar = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col(
                html.Img(src='./assets/logo1.png', height="35px"),
                xs=12, lg=4,
                className="d-flex justify-content-lg-start justify-content-sm-center justify-content-center mb-1"
            ),
            dbc.Col(
                html.H1("LST-1 Weather Station", className="display-5 text-center mb-0"),
                xs=12, lg=5,
                className="d-flex justify-content-sm-center justify-content-center mb-1",
            ),
            dbc.Col(
                navbar_menu,
                xs=12, lg=3,
                className="d-flex justify-content-lg-end justify-content-sm-center justify-content-center"
            ),
        ], align="center", className="w-100 justify-content-center m-0 p-0")
    ], fluid=True),
    #color='primary',
    #dark=True,
    className='navbar navbar-expand-lg bg-white'
)
