import typing
from dataclasses import dataclass

from measurement.results import MeasurementResult
from measurement.units import NetworkUnit, StorageUnit


@dataclass(frozen=True)
class DownloadSpeedMeasurementResult(MeasurementResult):
    """Encapsulates the results from a download speed measurement.

    :param url: The URL that was used to perform the download speed
    measurement.
    :param download_size: The size of the download (excluding units)
    that was used to perform the download speed measurement.
    :param download_size_unit: The unit of measurement used
    to describe the `download_size`.
    :param download_rate: The rate measured in the download speed
    measurement excluding units:
    :param download_rate_unit: The unit of measurement used to
    measure the `download_rate`.
    """

    url: str
    download_size: typing.Optional[float]
    download_size_unit: typing.Optional[StorageUnit]
    download_rate: typing.Optional[float]
    download_rate_unit: typing.Optional[NetworkUnit]


@dataclass(frozen=True)
class LatencyMeasurementResult(MeasurementResult):
    """Encapsulates the results from a latency measurement.

    :param host: The host that was used to perform the latency
    measurement.
    :param minimum_latency: The minimum amount of latency witnessed
    while performing the measurement.
    :param average_latency: The average amount of latency witnessed
    while performing the measurement.
    :param maximum_latency: The maximum amount of latency witnessed
    while performing the measurement.
    :param median_deviation: The median deviation witnessed across
    the measurement.
    """

    host: str
    minimum_latency: typing.Optional[float]
    average_latency: typing.Optional[float]
    maximum_latency: typing.Optional[float]
    median_deviation: typing.Optional[float]
