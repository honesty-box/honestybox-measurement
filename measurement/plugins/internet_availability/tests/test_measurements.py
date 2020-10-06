from unittest import TestCase, mock

from measurement.results import Error

from measurement.plugins.internet_availability.measurements import (
    CouldNotParsePingResultError,
    InternetAvailabilityMeasurement,
)
from measurement.plugins.internet_availability.results import InternetAvailabilityResult
from measurement.plugins.internet_availability.units import AvailabilityUnit


class InternetAvailabilityMeasurementTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super(InternetAvailabilityMeasurementTestCase, cls).setUpClass()
        cls.iam = InternetAvailabilityMeasurement("1")

    @mock.patch.object(
        InternetAvailabilityMeasurement,
        "_run_ping_test",
        mock.MagicMock(return_value=AvailabilityUnit.available),
    )
    def test_measure_returns_anticipated_format(self):
        self.assertEqual(
            self.iam.measure(),
            [
                InternetAvailabilityResult(
                    id=self.iam.id,
                    errors=[],
                    internet_with_dns=AvailabilityUnit.available,
                    internet=AvailabilityUnit.available,
                    router=AvailabilityUnit.available,
                    device=AvailabilityUnit.available,
                )
            ],
        )

    @mock.patch.object(
        InternetAvailabilityMeasurement,
        "_run_ping_test",
        mock.MagicMock(side_effect=CouldNotParsePingResultError("error text")),
    )
    def test_measure_returns_an_error_result_on_parsing_ping_error(self):
        self.assertEqual(
            self.iam.measure(),
            [
                InternetAvailabilityResult(
                    id=self.iam.id,
                    errors=[
                        Error(
                            key="internet-available-ping",
                            description="Internet available ping result could not be parsed by regex.",
                            traceback="error text",
                        )
                    ],
                    internet_with_dns=None,
                    internet=None,
                    router=None,
                    device=None,
                )
            ],
        )

    def test_get_device_availability_is_true(self):
        self.assertEqual(
            self.iam._get_device_availability(), AvailabilityUnit.available
        )

    @mock.patch(
        "measurement.plugins.internet_availability.measurements.netifaces.gateways",
        return_value={},
    )
    def test_get_router_availability_returns_unavailable_when_no_gateways_found(
        self, *args
    ):
        self.assertEqual(
            self.iam._get_router_availability(), AvailabilityUnit.unavailable
        )

    @mock.patch(
        "measurement.plugins.internet_availability.measurements.netifaces.gateways",
        return_value={
            2: [("192.168.1.1", "enp3s0", True)],
            "default": {2: ("192.168.1.1", "enp3s0")},
            10: [("fe80::6238:e0ff:fed8:581b", "enp3s0", True)],
        },
    )
    @mock.patch.object(
        InternetAvailabilityMeasurement,
        "_run_ping_test",
        mock.MagicMock(return_value=AvailabilityUnit.available),
    )
    def test_get_router_availability_returns_anticipated_value(self, *args):
        self.assertEqual(
            self.iam._get_router_availability(), AvailabilityUnit.available
        )

    @mock.patch.object(
        InternetAvailabilityMeasurement,
        "_run_ping_test",
        mock.MagicMock(return_value=AvailabilityUnit.available),
    )
    def test_get_internet_availability_returns_true_when_any_service_available(self):
        self.assertEqual(
            self.iam._get_internet_availability(), AvailabilityUnit.available
        )

    @mock.patch.object(
        InternetAvailabilityMeasurement,
        "_run_ping_test",
        mock.MagicMock(return_value=AvailabilityUnit.unavailable),
    )
    def test_get_internet_availability_returns_false_when_no_services_are_available(
        self,
    ):
        self.assertEqual(
            self.iam._get_internet_availability(), AvailabilityUnit.unavailable
        )

    @mock.patch("measurement.plugins.internet_availability.measurements.subprocess.run")
    def test_run_ping_test_raises_error_on_ping_result_parsing_issue(
        self, subprocess_run_mock
    ):
        return_mock = mock.Mock()
        return_mock.returncode = 0
        return_mock.stdout = ""

        subprocess_run_mock.return_value = return_mock
        with self.assertRaises(CouldNotParsePingResultError):
            self.iam._run_ping_test("test")

    @mock.patch("measurement.plugins.internet_availability.measurements.subprocess.run")
    def test_run_ping_test_returns_available_if_any_pings_returns(
        self, subprocess_run_mock
    ):
        return_mock = mock.Mock()
        return_mock.returncode = 0
        return_mock.stdout = "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=55 time=6.78 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=55 time=6.30 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=55 time=5.53 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=55 time=6.39 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 5.536/6.253/6.780/0.454 ms\n"
        subprocess_run_mock.return_value = return_mock

        self.assertEqual(self.iam._run_ping_test("1.1.1.1"), AvailabilityUnit.available)

    @mock.patch("measurement.plugins.internet_availability.measurements.subprocess.run")
    def test_run_ping_test_returns_unavailable_if_no_pings_return(
        self, subprocess_run_mock
    ):
        return_mock = mock.Mock()
        return_mock.returncode = 0
        return_mock.stdout = "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n\n--- 1.1.1.1 ping statistics ---\n1 packets transmitted, 0 received, 100% packet loss, time 0ms\n\n"
        subprocess_run_mock.return_value = return_mock

        self.assertEqual(
            self.iam._run_ping_test("1.1.1.1"), AvailabilityUnit.unavailable
        )

    @mock.patch.object(
        InternetAvailabilityMeasurement,
        "_run_ping_test",
        mock.MagicMock(return_value=AvailabilityUnit.available),
    )
    def test_get_internet_with_dns_availability_returns_true_when_any_service_available(
        self,
    ):
        self.assertEqual(
            self.iam._get_internet_with_dns_availability(), AvailabilityUnit.available
        )

    @mock.patch.object(
        InternetAvailabilityMeasurement,
        "_run_ping_test",
        mock.MagicMock(return_value=AvailabilityUnit.unavailable),
    )
    def test_get_internet_with_dns_availability_returns_false_when_no_services_are_available(
        self,
    ):
        self.assertEqual(
            self.iam._get_internet_with_dns_availability(), AvailabilityUnit.unavailable
        )

    @mock.patch.object(
        InternetAvailabilityMeasurement,
        "_run_ping_test",
        mock.MagicMock(
            side_effect=[
                CouldNotParsePingResultError(
                    "ping: test: Temporary failure in name resolution"
                ),
                AvailabilityUnit.available,
            ]
        ),
    )
    def test_get_internet_with_dns_availability_catches_dns_unavailable_error(
        self, *args
    ):
        self.assertEqual(
            self.iam._get_internet_with_dns_availability(), AvailabilityUnit.available
        )
