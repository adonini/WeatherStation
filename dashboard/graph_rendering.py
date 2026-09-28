from datetime import timezone

import numpy as np
import plotly.graph_objects as go


def history_trace(*, x, y, **kwargs):
    # Epoch milliseconds retain sub-second precision and avoid expensive ISO date
    # encoding for every trace. explicitly set the axis type to date.
    times = np.asarray([
        np.nan if stamp is None else
        (stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)).timestamp() * 1000
        for stamp in x
    ], dtype=np.float64)
    values = np.asarray(y, dtype=np.float64)
    trace = go.Scattergl if len(times) >= 5000 else go.Scatter
    if trace is go.Scattergl:
        kwargs.pop('hoveron', None)  # SVG-only option; point hover remains enabled.
    return trace(x=times, y=values, **kwargs)
