import collections
import sys

import six

if six.PY3 and not sys.version_info.minor == 5:  # All python 3 expect for 3.5
    from .results_py3 import *
else:
    LatencyMeasurementResult = collections.namedtuple(
        "LatencyMeasurementResult",
        "id errors host minimum_latency average_latency maximum_latency median_deviation "
        "packets_transmitted packets_received packets_lost packets_lost_unit elapsed_time elapsed_time_unit",
    )

    LatencyIndividualMeasurementResult = collections.namedtuple(
        "LatencyIndividualMeasurementResult",
        "id errors host packet_size packet_size_unit reverse_dns_address ip_address"
        " icmp_sequence time_to_live elapsed_time elapsed_time_unit",
    )
