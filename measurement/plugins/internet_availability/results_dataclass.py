import typing
from dataclasses import dataclass

from measurement.results import MeasurementResult

from measurement.plugins.internet_availability.units import AvailabilityUnit


@dataclass(frozen=True)
class InternetAvailabilityResult(MeasurementResult):
    """The result of measuring the availability of the internet

    The different parts of the availability of reaching the network are
    also measure including the ability of the device to take a
    measurement.
    """

    # The availability of the internet from the device (including DNS)
    internet_with_dns: typing.Optional[AvailabilityUnit]
    # The availability of the internet from the device via IP address
    internet: typing.Optional[AvailabilityUnit]
    # The availability of the router from the device
    router: typing.Optional[AvailabilityUnit]
    # The availability of the device to take the measurement e.g. it will be unavailable when the
    # power is turned off
    device: typing.Optional[AvailabilityUnit]
