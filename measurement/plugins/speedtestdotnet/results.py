import collections
import sys

import six

if six.PY3 and not sys.version_info.minor == 5:  # All python 3 expect for 3.5
    from .results_py3 import *
else:
    SpeedtestdotnetMeasurementResult = collections.namedtuple(
        "SpeedtestdotnetMeasurementResult",
        "id errors host minimum_latency average_latency maximum_latency median_deviation "
        "packets_transmitted packets_received packets_lost packets_lost_unit time time_unit",
    )

