"""Shared recovery status reconstructed from station history, not browser state."""
from configurations import SAFETY
from datetime import timedelta, timezone
import math

REQUIRED_FIELDS = ('Relative_Humidity', 'Mean_10_Wind_Speed', 'Max_Wind')


def utc(stamp):
    return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp


def valid(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def alert_message(active, readings, stale=False):
    """Use one action for combined alerts, with severe wind taking priority."""
    windy = 'wind' in active or 'gust' in active
    conditions = (['HIGH WIND'] if windy else [])
    conditions += ['HIGH HUMIDITY'] if 'humidity' in active else []
    conditions += ['RAIN'] if 'rain' in active else []
    severe = 'strong_wind' in active
    heading = 'VERY STRONG WIND' if severe else ' + '.join(conditions)
    if heading == 'RAIN':
        heading = 'RAIN DETECTED'
    action = ('Park the telescopes and go to the residencia' if severe else
              'Close the camera shutter and bring the telescopes to standby' if windy else
              'Close the camera shutter')
    lines = ['⚠ ' + heading + ' ⚠', action]
    if severe:
        others = [name for flag, name in (('humidity', 'high humidity'), ('rain', 'rain')) if flag in active]
        if others:
            lines.append('Also active: ' + ', '.join(others) + '.')
    if stale:
        lines.append('Station data unavailable — alert clearance cannot be verified.')
    return '\n'.join(lines)


def recovery_status(rows, now, compute_flags):
    """Require ten minutes of fresh clear samples; retain 20s rain debounce.
    A gap over two minutes interrupts evidence of continuous clear weather.
    The caller supplies the app's existing raw-rain classification.
    """
    now = utc(now)
    rows = sorted(rows, key=lambda row: utc(row['timestamp']))
    previous = None
    clear_since = None
    wet_since = dry_since = None
    rain_active = False
    active = []
    latest = None
    alert_readings = {}
    missing = False
    for row in rows:
        stamp = utc(row['timestamp'])
        if stamp > now or (previous is not None and stamp <= previous):
            continue
        if previous is None or stamp - previous > timedelta(seconds=SAFETY['max_data_gap_seconds']):
            clear_since = wet_since = dry_since = None
            rain_active = False
        previous = stamp
        latest = stamp
        if not all(valid(row.get(key)) for key in REQUIRED_FIELDS):
            clear_since = None
            missing = True
            continue
        missing = False
        flags = compute_flags(row)
        if flags['rain_raw']:
            dry_since = None
            wet_since = wet_since or stamp
            if stamp - wet_since >= timedelta(seconds=SAFETY['rain_confirm_seconds']):
                rain_active = True
        else:
            wet_since = None
            dry_since = dry_since or stamp
            if stamp - dry_since >= timedelta(seconds=SAFETY['rain_clear_seconds']):
                rain_active = False
        active = [name for name in ('humidity', 'wind', 'gust', 'strong_wind') if flags[name]]
        if rain_active:
            active.append('rain')
        if active:
            clear_since = None
            alert_readings = row
        elif clear_since is None:
            clear_since = stamp
    stale = latest is None or now - latest > timedelta(seconds=SAFETY['max_data_gap_seconds'])
    if active:
        return {'state': 'alert', 'active': active,
                'message': alert_message(active, alert_readings, stale or missing)}
    if stale:
        return {'state': 'unknown', 'message': 'Recovery cannot be verified, waiting for fresh station data'}
    if clear_since is None:
        return {'state': 'unknown', 'message': 'Recovery cannot be verified, safety values are missing'}
    deadline = clear_since + timedelta(seconds=SAFETY['recovery_seconds'])
    if latest < deadline:
        return {'state': 'recovery', 'deadline': deadline.timestamp() * 1000,
                'duration_seconds': SAFETY['recovery_seconds'],
                'server_now': now.timestamp() * 1000}
    return {'state': 'clear'}
