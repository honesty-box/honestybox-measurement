import collections
import sys

import six

if six.PY3 and not sys.version_info.minor == 5:  # All python 3 expect for 3.5
    from .results_py3 import *
else:
    DownloadSpeedMeasurementResult = collections.namedtuple(
        "DownloadSpeedMeasurementResult",
        "id errors url download_size download_size_unit download_rate download_rate_unit",
    )
    LatencyMeasurementResult = collections.namedtuple(
        "LatencyMeasurementResult",
        "id errors host minimum_latency average_latency maximum_latency median_deviation",
    )
