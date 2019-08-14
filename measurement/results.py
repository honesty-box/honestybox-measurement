import collections

import six

if six.PY3:
    from .results_py3 import *
else:
    Error = collections.namedtuple("Error", "key description traceback")
    MeasurementResult = collections.namedtuple("MeasurementResult", "id errors")
