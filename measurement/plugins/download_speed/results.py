import collections

import six

if six.PY3:
    from .results_py3 import *
else:
    DownloadSpeedMeasurementResult = collections.namedtuple(
        "DownloadSpeedMeasurementResult",
        "id errors url download_size download_size_unit download_rate download_rate_units",
    )
    LatencyMeasurementResult = collections.namedtuple(
        "LatencyMeasurementResult",
        "id errors host minimum_latency maximum_latency median_deviation",
    )
