import typing
from dataclasses import dataclass

from measurement.results import MeasurementResult
from measurement.units import TimeUnit, StorageUnit, RatioUnit, NetworkUnit


@dataclass(frozen=True)
class SpeedtestdotnetMeasurementResult(MeasurementResult):
    """Encapsulates the results from a speedtestdotnet measurement.

    :param host: The host that was used to perform the latency
    measurement.

    """

    download_rate: typing.Optional[float]
    download_rate_unit: typing.Optional[NetworkUnit]
    upload_rate: typing.Optional[float]
    upload_rate_unit: typing.Optional[NetworkUnit]
    latency: typing.Optional[float]
    server_name: typing.Optional[str]
    server_id: typing.Optional[str]
    server_sponsor: typing.Optional[str]
    server_host: typing.Optional[str]
