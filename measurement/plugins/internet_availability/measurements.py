import re
import subprocess
import typing

from measurement.measurements import BaseMeasurement
from measurement.results import Error

import netifaces
from measurement.plugins.internet_availability.results import InternetAvailabilityResult
from measurement.plugins.internet_availability.units import AvailabilityUnit

PING_AVAILABILITY_REGEX = re.compile(
    r"packets transmitted, (?P<number_of_available>\d) received"
)


class CouldNotParsePingResultError(BaseException):
    """The ping result is not in the anticipated format."""

    pass


class InternetAvailabilityMeasurement(BaseMeasurement):
    """Measures if the internet and associated services are available.

    Any response (including only intermittent responses) are considered
    that the service is available.
    """

    def measure(self) -> typing.List[InternetAvailabilityResult]:
        try:
            return [
                InternetAvailabilityResult(
                    id=self.id,
                    errors=[],
                    internet_with_dns=self._get_internet_with_dns_availability(),
                    internet=self._get_internet_availability(),
                    router=self._get_router_availability(),
                    device=self._get_device_availability(),
                )
            ]
        except CouldNotParsePingResultError as e:
            return [
                InternetAvailabilityResult(
                    id=self.id,
                    errors=[
                        Error(
                            key="internet-available-ping",
                            description="Internet available ping result could not be parsed by regex.",
                            traceback=str(e),
                        )
                    ],
                    internet_with_dns=None,
                    internet=None,
                    router=None,
                    device=None,
                )
            ]

    def _get_device_availability(self):
        """If the test is being run the device is available."""
        return AvailabilityUnit.available

    def _get_router_availability(self):
        """Determine if the router / gateway is up and available.

        This assumes that the route to the internet is defined on the
        default gateway.
        """
        gateways = netifaces.gateways()
        try:
            default_gateway_ip = gateways["default"][netifaces.AF_INET][0]
        except KeyError:  # If the gateway cannot be found it is considered down
            return AvailabilityUnit.unavailable
        try:
            return self._run_ping_test(default_gateway_ip)
        except CouldNotParsePingResultError as error:
            if "Network is unreachable" not in str(error):
                raise error
        return AvailabilityUnit.unavailable

    def _get_internet_with_dns_availability(self):
        """Test internet availability by pinging via DNS.

        If any service responds with a ping the internet is considered
        available.
        """
        for address in ["www.google.com", "www.bing.com"]:
            try:
                if self._run_ping_test(address) == AvailabilityUnit.available:
                    return AvailabilityUnit.available
            except CouldNotParsePingResultError as error:
                if self._should_raise_error(
                    str(error),
                    [
                        "Temporary failure in name resolution",
                        "Destination Net Unreachable",
                    ],
                ):
                    raise error
        return AvailabilityUnit.unavailable

    def _get_internet_availability(self):
        """Test internet availability by pinging via IP address.

        If any service responds with a ping the internet is considered
        available.
        """
        for address in ["8.8.8.8", "1.1.1.1", "1.0.0.1"]:
            try:
                if self._run_ping_test(address) == AvailabilityUnit.available:
                    return AvailabilityUnit.available
            except CouldNotParsePingResultError as error:
                if self._should_raise_error(
                    str(error),
                    ["Network is unreachable", "Destination Net Unreachable"],
                ):
                    raise error
        return AvailabilityUnit.unavailable

    def _should_raise_error(self, error_message, accepted_error_strings):
        """Determines if the error is unknown and should be propogated

        The `accepted_error_strings` only need to have on present in
        a substring for it to be a known error and return that no error
        should be raised.
        """
        return not any(
            known_error_string in error_message
            for known_error_string in accepted_error_strings
        )

    @staticmethod
    def _run_ping_test(address):
        """Performs a ping test to determine if a service is available.

        Any response from a service is considered available.
        """
        latency_out = subprocess.run(
            ["ping", "-c", "4", "{h}".format(h=address)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        # If there is an error we first return `stderr` but sometimes the errors get send through
        # `stdout` so we will fallback to that.
        if latency_out.returncode != 0:
            if latency_out.stderr != "":
                raise CouldNotParsePingResultError(latency_out.stderr)
            raise CouldNotParsePingResultError(latency_out.stdout)

        matches = PING_AVAILABILITY_REGEX.search(str(latency_out.stdout))

        try:
            number_available = int(matches.groupdict()["number_of_available"])
        except AttributeError:
            raise CouldNotParsePingResultError(latency_out)

        if number_available > 0:
            return AvailabilityUnit.available
        return AvailabilityUnit.unavailable
