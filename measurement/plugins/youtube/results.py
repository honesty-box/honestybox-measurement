import collections
import sys

import six

if six.PY3 and not sys.version_info.minor == 5:  # All python 3 expect for 3.5
    from .results_py3 import *
else:
    YouTubeMeasurementResult = collections.namedtuple(
        "YouTubeMeasurementResult",
        "id errors download_rate download_rate_unit download_size download_size_unit"
        " url elapsed_time elapsed_time_unit ",
    )
