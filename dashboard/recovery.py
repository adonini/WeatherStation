"""Shared recovery status reconstructed from station history, not browser state."""
from configurations import SAFETY
from datetime import timedelta, timezone
import math

REQUIRED_FIELDS = ('Relative_Humidity', 'Mean_10_Wind_Speed', 'Max_Wind')


def utc(stamp):
    return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp


def valid(value):
    return isinstance(value, (int, float)) and math.isfinite(value)



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
            active = []
            continue
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
        elif clear_since is None:
            clear_since = stamp
    if latest is None or now - latest > timedelta(seconds=SAFETY['max_data_gap_seconds']):
        return {'state': 'unknown', 'message': 'Recovery cannot be verified — waiting for fresh station data.'}
    if active:
        return {'state': 'alert', 'active': active}
    if clear_since is None:
        return {'state': 'unknown', 'message': 'Recovery cannot be verified, safety values are missing'}
    deadline = clear_since + timedelta(seconds=SAFETY['recovery_seconds'])
    if latest < deadline:
        return {'state': 'recovery', 'deadline': deadline.timestamp() * 1000,
                'duration_seconds': SAFETY['recovery_seconds'],
                'server_now': now.timestamp() * 1000}
    return {'state': 'clear'}
