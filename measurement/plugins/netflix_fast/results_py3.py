import typing
from dataclasses import dataclass

from measurement.results import MeasurementResult
from measurement.units import TimeUnit, StorageUnit, RatioUnit, NetworkUnit


@dataclass(frozen=True)
class NetflixFastMeasurementResult(MeasurementResult):
    """Encapsulates the results from a NetflixFast measurement.
    """

    download_rate: typing.Optional[float]
    download_rate_unit: typing.Optional[NetworkUnit]
    download_size: typing.Optional[float]
    download_size_unit: typing.Optional[StorageUnit]
    asn: typing.Optional[str]
    ip: typing.Optional[str]
    isp: typing.Optional[str]
    city: typing.Optional[str]
    country: typing.Optional[str]
    urlcount: typing.Optional[int]
    reason_terminated: typing.Optional[str]


@dataclass(frozen=True)
class NetflixFastThreadResult(MeasurementResult):
    """Encapsulates the latency test results from an individual download url.
    """

    host: str
    download_size: typing.Optional[float]
    download_size_unit: typing.Optional[StorageUnit]
    download_rate: typing.Optional[float]
    download_rate_unit: typing.Optional[NetworkUnit]
    city: typing.Optional[str]
    country: typing.Optional[str]
    minimum_latency: typing.Optional[float]
    average_latency: typing.Optional[float]
    maximum_latency: typing.Optional[float]
    median_deviation: typing.Optional[float]
    packets_transmitted: typing.Optional[int]
    packets_received: typing.Optional[int]
    packets_lost: typing.Optional[float]
    packets_lost_unit: typing.Optional[RatioUnit]
    time: typing.Optional[float]
    time_unit: typing.Optional[TimeUnit]
