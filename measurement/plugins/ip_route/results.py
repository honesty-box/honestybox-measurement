import collections
import sys

import six

if six.PY3 and not sys.version_info.minor == 5:  # All python 3 expect for 3.5
    from .results_py3 import *
else:
    IPRouteMeasurementResult = collections.namedtuple(
        "IPRouteMeasurementResult", "id errors host hop_count ip route",
    )
