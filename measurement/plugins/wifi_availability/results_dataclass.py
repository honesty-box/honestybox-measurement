import typing
from dataclasses import dataclass

from measurement.results import MeasurementResult
from measurement.units import NetworkUnit

from measurement.plugins.wifi_availability.units import (
    SignalFrequencyUnit,
    SignalPowerUnit,
)


@dataclass(frozen=True)
class AccessPointMeasurementResult(MeasurementResult):
    channel: typing.Optional[int]
    frequency: typing.Optional[float]
    frequency_unit: typing.Optional[SignalFrequencyUnit]
    quality: typing.Optional[str]
    signal_level: typing.Optional[float]
    signal_level_unit: typing.Optional[SignalPowerUnit]
    bssid: typing.Optional[str]
    essid: typing.Optional[str]
    standard: typing.Optional[str]
    bitrates: typing.Optional[list]
    last_beacon: typing.Optional[int]


@dataclass(frozen=True)
class ConnectedAccessPointMeasurementResult(MeasurementResult):
    bssid: typing.Optional[str]
    essid: typing.Optional[str]
    frequency: typing.Optional[float]
    frequency_unit: typing.Optional[SignalFrequencyUnit]
    bitrate: typing.Optional[float]
    bitrate_unit: typing.Optional[NetworkUnit]
    tx_power: typing.Optional[float]
    tx_power_unit: typing.Optional[SignalPowerUnit]
    link_quality: typing.Optional[str]
    signal_level: typing.Optional[float]
    signal_level_unit: typing.Optional[SignalPowerUnit]
