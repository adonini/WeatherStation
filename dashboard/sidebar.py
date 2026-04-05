from dash import html, dcc
from utils_modal import summary_body, body_mapping
import dash_bootstrap_components as dbc
from configurations import sidebar_style
from datetime import datetime, timedelta, timezone


BADGE_CLASSES = "fs-6 p-1 fw-light"

SIDEBAR_MODAL_TITLES = [
    "Humidity",
    "Wind 1' Avg",
    "Wind 10' Avg",
    "Wind Gusts",
    "Wind Direction",
    "Temperature",
    "Brightness",
    "Global Radiation",
    "Rain",
    "Rain Intensity",
    "Pressure",
]


def build_sidebar_modals():
    modals = []
    for title in SIDEBAR_MODAL_TITLES:
        body = body_mapping.get(title, "Default body content.")
        modals.append(
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(title), className="modal-header"),
                    dbc.ModalBody(body),
                ],
                id=f"modal_{title}",
                scrollable=True,
                is_open=False,
            )
        )
    return modals


# header of the sidebar
header_summary = dbc.Row([
    dbc.Col(
        html.I(className="bi bi-info-circle", id="summary-info-icon", n_clicks=0, style={"font-size": "24px", "cursor": "pointer"}),
        className="position-absolute top-50 start-0 translate-middle-y",
        width=1
    ),
    dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("Summary of meteorological safety limits"),
        ], className="modal-header"),
        dbc.ModalBody(summary_body)],
        id="modal_summary",
        scrollable=True,
        #size="xl",
        is_open=False,
    ),
    dbc.Col(
        html.H4("Current values", className="my-auto text-center ms-3"),
        #style={"margin-right": "10px"},
        width=11,
        align="center",
        className="w-100 align-items-center justify-content-center"
    )
], className='d-flex flex-lg-nowrap flex-column flex-lg-row align-items-center justify-content-around text-center')


###################
#  Sidebar cards
##################
# live values card
card_summary = dbc.Card([
    dbc.CardHeader(header_summary, className="card text-white bg-primary", style={'width': '100%'}),
    dbc.CardBody([
        dbc.ListGroup(id='live-values', flush=True),
    ], className="p-0 m-0"),  # removes the margin and the padding
    dbc.CardFooter(id="live-timestamp", children=[]),
])

# info card
card_info = dbc.Card([
    dbc.CardHeader("Info", className="card text-white bg-primary w-100 fs-5"),
    dbc.CardBody([
        html.Div([html.I(className="bi bi-clock me-2"), " Time ", html.Span(id="current-time", style={'marginLeft': '10px'})]),
        html.Div([html.I(className="bi bi-calendar3 me-2"), " Date ", html.Span(id="current-date", style={'marginLeft': '10px'})]),
        html.Hr(),
        html.Div([html.I(className="bi bi-sunrise me-2"), " Sunrise ", html.Span(id='sunrise-time', style={'marginLeft': '10px'})]),
        html.Div([html.I(className="bi bi-sunset me-2"), " Sunset ", html.Span(id='sunset-time', style={'marginLeft': '10px'})]),
        html.Hr(),
        html.Div([
            #html.P([html.I(className='fas fa-eye'), ' Visible ', html.Span(id='moon-visibility')]),
            #html.P([html.I(className='fas fa-moon mr-2'), ' Phase ', html.Span(id='moon-phase')]),
            html.P([html.I(className='bi bi-moon-stars me-2'), ' Illumination ', html.Span(id='moon-illumination', style={'marginLeft': '10px'})]),
            html.P([html.I(className='bi bi-arrow-up'), ' Rise ', html.Span(id='moon-rise', style={'marginLeft': '10px'})]),
            html.P([html.I(className='bi bi-arrow-down'), ' Set ', html.Span(id='moon-set', style={'marginLeft': '10px'})])
        ]),
    ]),
])


##############
# List group in sidebar
##############
def create_list_group_item(title, value, unit, timestamp, badge_color='green', row_color='default'):
    if value == 'n/a' or timestamp.replace(tzinfo=timezone.utc) < (datetime.now(timezone.utc) - timedelta(minutes=5)):
        badge_color = 'secondary'
        row_color = 'secondary'

    content = f"{value} {unit}" if value != 'n/a' else value

    if title in ["Humidity", "Wind 1' Avg", "Wind 10' Avg", "Wind Gusts", "Wind Direction", "Temperature", "Brightness", "Global Radiation", "Rain", "Pressure"]:
        line = dbc.ListGroupItem(
            dbc.Row([
                dbc.Col(
                    html.A(
                        title,
                        id=f"open_{title}",
                        href="#",
                        n_clicks=0,
                        className="align-items-center justify-content-center",
                        style={"color": "var(--primary)", "textDecoration": "none"}
                    )
                ),
                dbc.Col(
                    dbc.Badge(content, color=badge_color, class_name=BADGE_CLASSES),
                    className="d-flex align-items-center justify-content-center"
                )
            ]),
            color=row_color,
            className="border-bottom position-relative p-1"
        )
    else:
        line = dbc.ListGroupItem(
            dbc.Row([
                dbc.Col(title, className="align-items-center justify-content-center"),
                dbc.Col(
                    dbc.Badge(content, color=badge_color, class_name=BADGE_CLASSES),
                    className="d-flex align-items-center justify-content-center"
                )
            ]),
            color=row_color,
            className="border-bottom position-relative p-1"
        )
    return line


def create_list_group_item_alert(title, value, unit, badge_color='danger', row_color='danger'):
    if value == 'n/a':
        badge_color = 'secondary'
        row_color = 'secondary'

    if title in ["Humidity", "Wind 10' Avg", "Wind Gusts", "Rain", "Rain Intensity"]:
        line = dbc.ListGroupItem([
            dbc.Row([
                dbc.Col([
                    html.I(
                        className=("bi bi-exclamation-triangle-fill me-3" if badge_color == 'warning'
                                   else "bi bi-x-octagon-fill me-3"),
                        style={"display": "inline-block"}
                    ),
                    html.A(
                        title,
                        id=f"open_{title}",
                        href="#",
                        n_clicks=0,
                        style={"display": "inline-block", "cursor": "pointer",
                               "color": "var(--primary)", "textDecoration": "none"},
                    ),
                ], className="d-flex align-items-center justify-content-center"),
                dbc.Col(
                    dbc.Badge(f"{value} {unit}", color=badge_color, class_name=BADGE_CLASSES),
                    className="d-flex align-items-center justify-content-center"
                ),
            ]),
        ], color=row_color, className="border-bottom position-relative p-1")
    else:
        line = dbc.ListGroupItem([
            dbc.Row([
                dbc.Col(
                    dbc.Stack([
                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                        html.Div(title),
                    ], direction="horizontal", gap=1)
                ),
                dbc.Col(
                    dbc.Badge(f"{value} {unit}", color=badge_color, class_name=BADGE_CLASSES),
                    className="d-flex align-items-center justify-content-center"
                ),
            ]),
        ], color=row_color, className="border-bottom position-relative p-1")
    return line


######################
# Sidebar definition
#####################
sidebar = html.Div([
    dbc.Nav(
        [html.Div(card_summary),
         html.Div(build_sidebar_modals()),
         dcc.Interval(id='interval-livevalues', interval=20000, n_intervals=0, disabled=False),
         html.Hr(),
         html.Div(card_info)],
        vertical=True,
    )],
    className="sticky-top overflow-scroll vh-100",
    style=sidebar_style,
)
