"""Interactive EUMETSAT viewer and cached observation-time metadata."""
import logging
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc
from flask import jsonify

WMS_URL = 'https://view.eumetsat.int/geoserver/wms'
LAYER = 'mtg_fd:ir105_hrfi'
LAYERS = {
    'msg_fes:cth': 'Cloud Top Height',
    LAYER: 'Infrared · colour',
    'mtg_fd:rgb_dust': 'Dust',
    'msg_fes:ir108': 'MSG 10.8 µm · grayscale',
    'mtg_fd:li_afa': 'Lightning storms',
}


_cache = {'checked': None, 'layers': {}, 'failed': False}
_lock = threading.Lock()


def _download(params):
    with urlopen(WMS_URL + '?' + urlencode(params), timeout=15) as response:
        return response.read()


def wms_timestamp(stamp):
    """GeoServer requires UTC Z rather than an explicit +00:00 offset."""
    return stamp.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def layer_times(document):
    ns = {'w': 'http://www.opengis.net/wms'}
    result = {}
    for layer in ET.fromstring(document).findall('.//w:Layer', ns):
        name = layer.findtext('w:Name', namespaces=ns)
        if name not in LAYERS:
            continue
        for dimension in layer.findall('w:Dimension', ns):
            if dimension.get('name') == 'time':
                stamp = datetime.fromisoformat(dimension.get('default', '').replace('Z', '+00:00'))
                result[name] = {'label': LAYERS[name], 'latest': wms_timestamp(stamp)}
    if LAYER not in result:
        raise ValueError('EUMETSAT infrared observation time unavailable')
    return result


def latest_timestamp(document):
    return datetime.fromisoformat(layer_times(document)[LAYER]['latest'].replace('Z', '+00:00'))


def satellite_metadata():
    with _lock:
        now = time.monotonic()
        ttl = 60 if _cache['failed'] else 300
        if _cache['checked'] is None or now - _cache['checked'] >= ttl:
            try:
                _cache['layers'] = layer_times(_download({
                    'service': 'WMS', 'request': 'GetCapabilities', 'version': '1.3.0'}))
                _cache['failed'] = False
            except Exception:
                logging.getLogger(__name__).warning('Satellite metadata refresh failed', exc_info=True)
                _cache['failed'] = True
            _cache['checked'] = time.monotonic()
        return {'layers': {name: info for name, info in _cache['layers'].items() if name in LAYERS},
                'order': [name for name in LAYERS if name in _cache['layers']],
                'failed': _cache['failed']}


def make_satellite_card():
    header = dbc.Row([
        dbc.Col(html.H4('EUMETSAT', className='my-auto'), width=11, align='center'),
        dbc.Col([
            dbc.Button(html.I(className='fa fa-refresh', style={'font-size': '24px'}),
                       id='eumetsat-refresh', n_clicks=0, title='Refresh satellite imagery',
                       style={'float': 'right'}, className='position-absolute top-50 end-0 translate-middle-y'),
            dbc.Tooltip('Refresh satellite imagery', target='eumetsat-refresh', placement='bottom'),
        ], width=1, align='center'),
    ], align='center')
    return dbc.Card([
        dbc.CardHeader(header, className='card text-white bg-primary', style={'width': '100%'}),
        dbc.CardBody(html.Iframe(
            id='eumetsat-viewer', src='assets/satellite_viewer.html', title='Meteosat satellite map of the Canary Islands',
            allow='fullscreen', style={'width': '100%', 'height': '490px', 'border': 0, 'display': 'block'}),
            style={'width': '100%', 'padding': 0, 'overflow': 'hidden'}),
        dbc.CardFooter([
            html.Span('Meteosat observations · © EUMETSAT · '),
            html.A('EUMETView ↗', href='https://view.eumetsat.int/', target='_blank', rel='noopener noreferrer'),
        ], className='small', style={'width': '100%'}),
        dcc.Store(id='eumetsat-controls'),
    ], className='border rounded p-0 col-cards-2')


def register_satellite_callbacks(app):
    @app.server.route('/eumetsat/metadata')
    def eumetsat_metadata():
        response = jsonify(satellite_metadata())
        response.headers['Cache-Control'] = 'no-store'
        return response

    app.clientside_callback('''function(refresh) {
        const frame = document.getElementById('eumetsat-viewer');
        const message = {type: 'eumetsat-controls', refresh: refresh};
        if (frame) {
            const send = () => frame.contentWindow.postMessage(message, window.location.origin);
            frame.onload = send;
            send();
        }
        return message;
    }''', Output('eumetsat-controls', 'data'),
        Input('eumetsat-refresh', 'n_clicks'))
