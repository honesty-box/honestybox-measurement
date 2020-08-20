import collections
import sys

import six

if six.PY3 and not sys.version_info.minor == 5:  # All python 3 expect for 3.5
    from .results_py3 import *
else:
    SpeedtestdotnetMeasurementResult = collections.namedtuple(
        "SpeedtestdotnetMeasurementResult",
        "id errors download_rate download_rate_unit upload_rate upload_rate_unit "
        "data_received data_received_unit latency server_name server_id server_sponsor server_host",
    )
