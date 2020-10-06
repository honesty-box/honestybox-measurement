import collections
import sys

import six

if six.PY3 and not sys.version_info.minor == 5:  # All python 3 expect for 3.5
    from .results_dataclass import *  # NOQA: F403 F401
else:
    InternetAvailabilityResult = collections.namedtuple(
        "InternetAvailabilityResult",
        "id errors internet_with_dns internet router device",
    )
