import typing
from dataclasses import dataclass

from measurement.results import MeasurementResult
from measurement.units import TimeUnit, StorageUnit, RatioUnit, NetworkUnit


@dataclass(frozen=True)
class IPRouteMeasurementResult(MeasurementResult):
    """Encapsulates the result from a IPRoute measurement.
    """

    host: typing.Optional[str]
    hop_count: typing.Optional[int]
    ip: typing.Optional[str]
    trace: typing.Optional[list]
