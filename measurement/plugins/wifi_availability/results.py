import collections
import sys

import six

if six.PY3 and not sys.version_info.minor == 5:  # All python 3 expect for 3.5
    from .results_dataclass import *  # NOQA: F403 F401
else:
    AccessPointMeasurementResult = collections.namedtuple(
        "AccessPointMeasurementResult",
        "id errors channel frequency frequency_unit quality signal_level, signal_level_unit essid bssid standard bitrates last_beacon",
    )
    ConnectedAccessPointMeasurementResult = collections.namedtuple(
        "ConnectedAccessPointMeasurement",
        "id errors essid bssid frequency frequency_unit bitrate bitrate_unit tx_power tx_power_unit link_quality signal_level signal_level_unit",
    )
