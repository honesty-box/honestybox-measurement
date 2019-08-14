import collections
import sys

import six

if six.PY3 and not sys.version_info.minor == 5:  # All python 3 expect for 3.5
    from .results_py3 import *
else:
    Error = collections.namedtuple("Error", "key description traceback")
    MeasurementResult = collections.namedtuple("MeasurementResult", "id errors")
