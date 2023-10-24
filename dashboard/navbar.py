import dash_bootstrap_components as dbc


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
