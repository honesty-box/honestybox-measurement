from unittest import TestCase, mock

from measurement.results import Error
from measurement.units import NetworkUnit

from measurement.plugins.wifi_availability.measurements import AccessPointMeasurement
from measurement.plugins.wifi_availability.results import (
    AccessPointMeasurementResult,
    ConnectedAccessPointMeasurementResult,
)
from measurement.plugins.wifi_availability.units import (
    SignalPowerUnit,
    SignalFrequencyUnit,
)


class FullMeasurementTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.apm = AccessPointMeasurement("example_id")
        self.example_iwconfig_result = ConnectedAccessPointMeasurementResult(
            id="example_id",
            essid="example_essid",
            bssid="example_bssid",
            frequency=1.234,
            frequency_unit=SignalFrequencyUnit("GHz"),
            bitrate=123.4,
            bitrate_unit=NetworkUnit("Mbit/s"),
            tx_power=12,
            tx_power_unit=SignalPowerUnit("dBm"),
            link_quality="12/34",
            signal_level=-12,
            signal_level_unit=SignalPowerUnit("dBm"),
            errors=[],
        )
        self.example_iwlist_result = AccessPointMeasurementResult(
            id="example_id",
            channel=321,
            frequency=4.321,
            frequency_unit=SignalFrequencyUnit("GHz"),
            quality="43/21",
            signal_level=-21,
            signal_level_unit=SignalPowerUnit("dBm"),
            essid="example_essid",
            bssid="example_bssid",
            standard="example_standard",
            bitrates=[
                "1Mb/s",
                "2Mb/s",
                "3Mb/s",
                "4Mb/s",
                "5Mb/s",
                "6Mb/s",
                "7Mb/s",
                "8Mb/s",
            ],
            last_beacon=7654321,
            errors=[],
        )

    @mock.patch(
        "measurement.plugins.wifi_availability.measurements.AccessPointMeasurement._get_iwconfig_result"
    )
    @mock.patch(
        "measurement.plugins.wifi_availability.measurements.AccessPointMeasurement._get_scan_results"
    )
    def test_measure(self, mock_get_scan_results, mock_get_iwconfig_result):
        mock_get_scan_results.return_value = [self.example_iwlist_result]
        mock_get_iwconfig_result.return_value = self.example_iwconfig_result
        self.assertCountEqual(
            self.apm.measure(),
            [self.example_iwconfig_result, self.example_iwlist_result],
        )

    @mock.patch(
        "measurement.plugins.wifi_availability.measurements.psutil.net_if_addrs"
    )
    def test__get_interface(self, mock_net_if_addrs):
        mock_net_if_addrs.return_value = {
            "interface_one": "interface_one_data",
            "interface_two": "interface_two_data",
        }
        self.assertCountEqual(
            list(self.apm._get_interfaces()), ["interface_one", "interface_two"]
        )


# noinspection PyArgumentList
class AccessPointTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.apm = AccessPointMeasurement("example_id")

    @mock.patch(
        "measurement.plugins.wifi_availability.measurements.AccessPointMeasurement._get_interfaces"
    )
    @mock.patch("subprocess.run")
    def test_scan_result_single_cell(self, mock_interface_out, mock_get_interfaces):
        example_iwlist_out_single_cell = 'wlp1s0    Scan completed :\n          Cell 01 - Address: 98:DA:C4:A8:D4:D4\n                    Channel:321\n                    Frequency:4.321 GHz\n                    Quality=43/21  Signal level=-21 dBm  \n                    Encryption key:on\n                    ESSID:"example_essid"\n                    Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n                              6 Mb/s; 7 Mb/s; 8 Mb/s\n                    Mode:Master\n                    Extra:tsf=00000000f5289342\n                    Extra: Last beacon: 7654321ms ago\n                    IE: Unknown: 000932356669667465656E\n                    IE: Unknown: 01088C129824B048606C\n                    IE: IEEE example_standard\n                        Group Cipher : CCMP\n                        Pairwise Ciphers (1) : CCMP\n                        Authentication Suites (1) : PSK\n                    IE: Unknown: 0B050A00130000\n                    IE: Unknown: 2D1AEF0117FFFFFF0000000000000080017800000000000000000000\n                    IE: Unknown: 3D16950D0400000000000000000000000000000000000000\n                    IE: Unknown: 7F080400000000000040\n                    IE: Unknown: BF0CB259820FEAFF0000EAFF0000\n                    IE: Unknown: C005019B000000\n                    IE: Unknown: C304020E0E0E\n                    IE: Unknown: DD09001018020A101C0000\n                    IE: Unknown: DD180050F20201018400033200002732000042225E0062212F00\n'
        example_iwlist_result = AccessPointMeasurementResult(
            id="example_id",
            channel=321,
            frequency=4.321,
            frequency_unit=SignalFrequencyUnit("GHz"),
            quality="43/21",
            signal_level=-21.0,
            signal_level_unit=SignalPowerUnit("dBm"),
            essid="example_essid",
            bssid="98:DA:C4:A8:D4:D4",
            standard="IEEE example_standard",
            bitrates=[
                "1Mbit/s",
                "2Mbit/s",
                "3Mbit/s",
                "4Mbit/s",
                "5Mbit/s",
                "6Mbit/s",
                "7Mbit/s",
                "8Mbit/s",
            ],
            last_beacon=7654321,
            errors=[],
        )
        mock_get_interfaces.return_value = ["Interface One"]
        run_mock = mock.MagicMock()

        run_mock.stdout = example_iwlist_out_single_cell
        run_mock.stderr = ""
        mock_interface_out.return_value = run_mock
        self.assertEqual(self.apm._get_scan_results(), [example_iwlist_result])

    @mock.patch(
        "measurement.plugins.wifi_availability.measurements.AccessPointMeasurement._get_interfaces"
    )
    @mock.patch("subprocess.run")
    def test_scan_result_three_cells(self, mock_interface_out, mock_get_interfaces):
        example_iwlist_out_three_cells = (
            "wlp1s0    Scan completed :\n          "
            'Cell 01 - Address: 98:DA:C4:A8:D4:D4\n                    Channel:1\n                    Frequency:4.321 GHz\n                    Quality=43/21  Signal level=-21 dBm  \n                    Encryption key:on\n                    ESSID:"example_essid"\n                    Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n                              6 Mb/s; 7 Mb/s; 8 Mb/s\n                    Mode:Master\n                    Extra:tsf=00000000f5289342\n                    Extra: Last beacon: 7654321ms ago\n                    IE: Unknown: 000932356669667465656E\n                    IE: Unknown: 01088C129824B048606C\n                    IE: IEEE example_standard\n                        Group Cipher : CCMP\n                        Pairwise Ciphers (1) : CCMP\n                        Authentication Suites (1) : PSK\n                    IE: Unknown: 0B050A00130000\n                    IE: Unknown: 2D1AEF0117FFFFFF0000000000000080017800000000000000000000\n                    IE: Unknown: 3D16950D0400000000000000000000000000000000000000\n                    IE: Unknown: 7F080400000000000040\n                    IE: Unknown: BF0CB259820FEAFF0000EAFF0000\n                    IE: Unknown: C005019B000000\n                    IE: Unknown: C304020E0E0E\n                    IE: Unknown: DD09001018020A101C0000\n                    IE: Unknown: DD180050F20201018400033200002732000042225E0062212F00\n'
            'Cell 02 - Address: 98:DA:C4:A8:D4:D4\n                    Channel:2\n                    Frequency:4.321 GHz\n                    Quality=43/21  Signal level=-21 dBm  \n                    Encryption key:on\n                    ESSID:"example_essid"\n                    Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n                              6 Mb/s; 7 Mb/s; 8 Mb/s\n                    Mode:Master\n                    Extra:tsf=00000000f5289342\n                    Extra: Last beacon: 7654321ms ago\n                    IE: Unknown: 000932356669667465656E\n                    IE: Unknown: 01088C129824B048606C\n                    IE: IEEE example_standard\n                        Group Cipher : CCMP\n                        Pairwise Ciphers (1) : CCMP\n                        Authentication Suites (1) : PSK\n                    IE: Unknown: 0B050A00130000\n                    IE: Unknown: 2D1AEF0117FFFFFF0000000000000080017800000000000000000000\n                    IE: Unknown: 3D16950D0400000000000000000000000000000000000000\n                    IE: Unknown: 7F080400000000000040\n                    IE: Unknown: BF0CB259820FEAFF0000EAFF0000\n                    IE: Unknown: C005019B000000\n                    IE: Unknown: C304020E0E0E\n                    IE: Unknown: DD09001018020A101C0000\n                    IE: Unknown: DD180050F20201018400033200002732000042225E0062212F00\n'
            'Cell 03 - Address: 98:DA:C4:A8:D4:D4\n                    Channel:3\n                    Frequency:4.321 GHz\n                    Quality=43/21  Signal level=-21 dBm  \n                    Encryption key:on\n                    ESSID:"example_essid"\n                    Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n                              6 Mb/s; 7 Mb/s; 8 Mb/s\n                    Mode:Master\n                    Extra:tsf=00000000f5289342\n                    Extra: Last beacon: 7654321ms ago\n                    IE: Unknown: 000932356669667465656E\n                    IE: Unknown: 01088C129824B048606C\n                    IE: IEEE example_standard\n                        Group Cipher : CCMP\n                        Pairwise Ciphers (1) : CCMP\n                        Authentication Suites (1) : PSK\n                    IE: Unknown: 0B050A00130000\n                    IE: Unknown: 2D1AEF0117FFFFFF0000000000000080017800000000000000000000\n                    IE: Unknown: 3D16950D0400000000000000000000000000000000000000\n                    IE: Unknown: 7F080400000000000040\n                    IE: Unknown: BF0CB259820FEAFF0000EAFF0000\n                    IE: Unknown: C005019B000000\n                    IE: Unknown: C304020E0E0E\n                    IE: Unknown: DD09001018020A101C0000\n                    IE: Unknown: DD180050F20201018400033200002732000042225E0062212F00\n'
        )
        example_iwlist_results = [
            AccessPointMeasurementResult(
                id="example_id",
                channel=1,
                frequency=4.321,
                frequency_unit=SignalFrequencyUnit("GHz"),
                quality="43/21",
                signal_level=-21.0,
                signal_level_unit=SignalPowerUnit("dBm"),
                essid="example_essid",
                bssid="98:DA:C4:A8:D4:D4",
                standard="IEEE example_standard",
                bitrates=[
                    "1Mbit/s",
                    "2Mbit/s",
                    "3Mbit/s",
                    "4Mbit/s",
                    "5Mbit/s",
                    "6Mbit/s",
                    "7Mbit/s",
                    "8Mbit/s",
                ],
                last_beacon=7654321,
                errors=[],
            ),
            AccessPointMeasurementResult(
                id="example_id",
                channel=2,
                frequency=4.321,
                frequency_unit=SignalFrequencyUnit("GHz"),
                quality="43/21",
                signal_level=-21.0,
                signal_level_unit=SignalPowerUnit("dBm"),
                essid="example_essid",
                bssid="98:DA:C4:A8:D4:D4",
                standard="IEEE example_standard",
                bitrates=[
                    "1Mbit/s",
                    "2Mbit/s",
                    "3Mbit/s",
                    "4Mbit/s",
                    "5Mbit/s",
                    "6Mbit/s",
                    "7Mbit/s",
                    "8Mbit/s",
                ],
                last_beacon=7654321,
                errors=[],
            ),
            AccessPointMeasurementResult(
                id="example_id",
                channel=3,
                frequency=4.321,
                frequency_unit=SignalFrequencyUnit("GHz"),
                quality="43/21",
                signal_level=-21.0,
                signal_level_unit=SignalPowerUnit("dBm"),
                essid="example_essid",
                bssid="98:DA:C4:A8:D4:D4",
                standard="IEEE example_standard",
                bitrates=[
                    "1Mbit/s",
                    "2Mbit/s",
                    "3Mbit/s",
                    "4Mbit/s",
                    "5Mbit/s",
                    "6Mbit/s",
                    "7Mbit/s",
                    "8Mbit/s",
                ],
                last_beacon=7654321,
                errors=[],
            ),
        ]
        mock_get_interfaces.return_value = ["Interface One"]
        run_mock = mock.MagicMock()
        run_mock.stdout = example_iwlist_out_three_cells
        run_mock.stderr = ""
        mock_interface_out.return_value = run_mock
        self.assertEqual(self.apm._get_scan_results(), example_iwlist_results)

    @mock.patch(
        "measurement.plugins.wifi_availability.measurements.AccessPointMeasurement._get_interfaces"
    )
    @mock.patch("subprocess.run")
    def test_scan_invalid_unit(self, mock_interface_out, mock_get_interfaces):
        example_iwlist_out_invalid_unit = 'wlp1s0    Scan completed :\n          Cell 01 - Address: 98:DA:C4:A8:D4:D4\n                    Channel:321\n                    Frequency:4.321 NotARealUnitz\n                    Quality=43/21  Signal level=-21 dBm  \n                    Encryption key:on\n                    ESSID:"example_essid"\n                    Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n                              6 Mb/s; 7 Mb/s; 8 Mb/s\n                    Mode:Master\n                    Extra:tsf=00000000f5289342\n                    Extra: Last beacon: 7654321ms ago\n                    IE: Unknown: 000932356669667465656E\n                    IE: Unknown: 01088C129824B048606C\n                    IE: IEEE example_standard\n                        Group Cipher : CCMP\n                        Pairwise Ciphers (1) : CCMP\n                        Authentication Suites (1) : PSK\n                    IE: Unknown: 0B050A00130000\n                    IE: Unknown: 2D1AEF0117FFFFFF0000000000000080017800000000000000000000\n                    IE: Unknown: 3D16950D0400000000000000000000000000000000000000\n                    IE: Unknown: 7F080400000000000040\n                    IE: Unknown: BF0CB259820FEAFF0000EAFF0000\n                    IE: Unknown: C005019B000000\n                    IE: Unknown: C304020E0E0E\n                    IE: Unknown: DD09001018020A101C0000\n                    IE: Unknown: DD180050F20201018400033200002732000042225E0062212F00\n'
        example_cell_invalid_unit = ' 01 - Address: 98:DA:C4:A8:D4:D4\n                    Channel:321\n                    Frequency:4.321 NotARealUnitz\n                    Quality=43/21  Signal level=-21 dBm  \n                    Encryption key:on\n                    ESSID:"example_essid"\n                    Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n                              6 Mb/s; 7 Mb/s; 8 Mb/s\n                    Mode:Master\n                    Extra:tsf=00000000f5289342\n                    Extra: Last beacon: 7654321ms ago\n                    IE: Unknown: 000932356669667465656E\n                    IE: Unknown: 01088C129824B048606C\n                    IE: IEEE example_standard\n                        Group Cipher : CCMP\n                        Pairwise Ciphers (1) : CCMP\n                        Authentication Suites (1) : PSK\n                    IE: Unknown: 0B050A00130000\n                    IE: Unknown: 2D1AEF0117FFFFFF0000000000000080017800000000000000000000\n                    IE: Unknown: 3D16950D0400000000000000000000000000000000000000\n                    IE: Unknown: 7F080400000000000040\n                    IE: Unknown: BF0CB259820FEAFF0000EAFF0000\n                    IE: Unknown: C005019B000000\n                    IE: Unknown: C304020E0E0E\n                    IE: Unknown: DD09001018020A101C0000\n                    IE: Unknown: DD180050F20201018400033200002732000042225E0062212F00\n'

        example_iwlist_result = AccessPointMeasurementResult(
            id="example_id",
            channel=None,
            frequency=None,
            frequency_unit=None,
            quality=None,
            signal_level=None,
            signal_level_unit=None,
            essid=None,
            bssid=None,
            standard=None,
            bitrates=None,
            last_beacon=None,
            errors=[
                Error(
                    key="scan-frequency_unit",
                    description="Could not process the frequency unit regex.",
                    traceback=example_cell_invalid_unit,
                )
            ],
        )
        mock_get_interfaces.return_value = ["Interface One"]
        run_mock = mock.MagicMock()
        run_mock.stdout = example_iwlist_out_invalid_unit
        run_mock.stderr = ""
        mock_interface_out.return_value = run_mock
        self.assertEqual(self.apm._get_scan_results(), [example_iwlist_result])

    @mock.patch(
        "measurement.plugins.wifi_availability.measurements.AccessPointMeasurement._get_interfaces"
    )
    @mock.patch("subprocess.run")
    def test_scan_missing_metric(self, mock_interface_out, mock_get_interfaces):
        example_iwlist_out_missing_metric = 'wlp1s0    Scan completed :\n          Cell 01 - Address: 98:DA:C4:A8:D4:D4\n                    Channel:321\n                    Quality=43/21  Signal level=-21 dBm  \n                    Encryption key:on\n                    ESSID:"example_essid"\n                    Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n                              6 Mb/s; 7 Mb/s; 8 Mb/s\n                    Mode:Master\n                    Extra:tsf=00000000f5289342\n                    Extra: Last beacon: 7654321ms ago\n                    IE: Unknown: 000932356669667465656E\n                    IE: Unknown: 01088C129824B048606C\n                    IE: IEEE example_standard\n                        Group Cipher : CCMP\n                        Pairwise Ciphers (1) : CCMP\n                        Authentication Suites (1) : PSK\n                    IE: Unknown: 0B050A00130000\n                    IE: Unknown: 2D1AEF0117FFFFFF0000000000000080017800000000000000000000\n                    IE: Unknown: 3D16950D0400000000000000000000000000000000000000\n                    IE: Unknown: 7F080400000000000040\n                    IE: Unknown: BF0CB259820FEAFF0000EAFF0000\n                    IE: Unknown: C005019B000000\n                    IE: Unknown: C304020E0E0E\n                    IE: Unknown: DD09001018020A101C0000\n                    IE: Unknown: DD180050F20201018400033200002732000042225E0062212F00\n'
        example_iwlist_result = AccessPointMeasurementResult(
            id="example_id",
            channel=321,
            frequency=None,
            frequency_unit=None,
            quality="43/21",
            signal_level=-21.0,
            signal_level_unit=SignalPowerUnit("dBm"),
            essid="example_essid",
            bssid="98:DA:C4:A8:D4:D4",
            standard="IEEE example_standard",
            bitrates=[
                "1Mbit/s",
                "2Mbit/s",
                "3Mbit/s",
                "4Mbit/s",
                "5Mbit/s",
                "6Mbit/s",
                "7Mbit/s",
                "8Mbit/s",
            ],
            last_beacon=7654321,
            errors=[],
        )
        mock_get_interfaces.return_value = ["Interface One"]
        run_mock = mock.MagicMock()
        run_mock.stdout = example_iwlist_out_missing_metric
        run_mock.stderr = ""
        mock_interface_out.return_value = run_mock
        self.assertEqual(self.apm._get_scan_results(), [example_iwlist_result])

    @mock.patch(
        "measurement.plugins.wifi_availability.measurements.AccessPointMeasurement._get_interfaces"
    )
    @mock.patch("subprocess.run")
    def test_scan_error(self, mock_interface_out, mock_get_interfaces):
        example_iwlist_result = AccessPointMeasurementResult(
            id="example_id",
            channel=None,
            frequency=None,
            frequency_unit=None,
            quality=None,
            signal_level=None,
            signal_level_unit=None,
            essid=None,
            bssid=None,
            standard=None,
            bitrates=None,
            last_beacon=None,
            errors=[
                Error(
                    key="scan-err",
                    description="scan had an unknown error.",
                    traceback="An error happened!",
                )
            ],
        )
        mock_get_interfaces.return_value = ["Interface One"]
        run_mock = mock.MagicMock()
        run_mock.stdout = ""
        run_mock.stderr = "An error happened!"
        mock_interface_out.return_value = run_mock
        self.assertEqual(self.apm._get_scan_results(), [example_iwlist_result])

    @mock.patch(
        "measurement.plugins.wifi_availability.measurements.AccessPointMeasurement._get_interfaces"
    )
    @mock.patch("subprocess.run")
    def test_scan_error_three_interfaces(self, mock_interface_out, mock_get_interfaces):
        self.maxDiff = None
        example_iwlist_results = [
            AccessPointMeasurementResult(
                id="example_id",
                channel=None,
                frequency=None,
                frequency_unit=None,
                quality=None,
                signal_level=None,
                signal_level_unit=None,
                essid=None,
                bssid=None,
                standard=None,
                bitrates=None,
                last_beacon=None,
                errors=[
                    Error(
                        key="scan-err",
                        description="scan had an unknown error.",
                        traceback="An error happened!",
                    )
                ],
            ),
            AccessPointMeasurementResult(
                id="example_id",
                channel=None,
                frequency=None,
                frequency_unit=None,
                quality=None,
                signal_level=None,
                signal_level_unit=None,
                essid=None,
                bssid=None,
                standard=None,
                bitrates=None,
                last_beacon=None,
                errors=[
                    Error(
                        key="scan-err",
                        description="scan had an unknown error.",
                        traceback="An error happened!",
                    )
                ],
            ),
            AccessPointMeasurementResult(
                id="example_id",
                channel=None,
                frequency=None,
                frequency_unit=None,
                quality=None,
                signal_level=None,
                signal_level_unit=None,
                essid=None,
                bssid=None,
                standard=None,
                bitrates=None,
                last_beacon=None,
                errors=[
                    Error(
                        key="scan-err",
                        description="scan had an unknown error.",
                        traceback="An error happened!",
                    )
                ],
            ),
        ]
        mock_get_interfaces.return_value = [
            "Interface One",
            "Interface Two",
            "Interface Three",
        ]
        run_mock = mock.MagicMock()
        run_mock.stdout = ""
        run_mock.stderr = "An error happened!"
        mock_interface_out.return_value = run_mock
        self.assertEqual(self.apm._get_scan_results(), example_iwlist_results)

    def test_parse_metric_bitrates_single_line(self):
        bitrates_match = "Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n"
        bitrates_expected = ["1Mbit/s", "2Mbit/s", "3Mbit/s", "4Mbit/s", "5Mbit/s"]
        self.assertEqual(
            self.apm._parse_access_point_metric("bitrates", bitrates_match),
            bitrates_expected,
        )

    def test_parse_metric_bitrates_two_lines(self):
        bitrates_match = "Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n                              6 Mb/s; 7 Mb/s; 8 Mb/s\n                    "
        bitrates_expected = [
            "1Mbit/s",
            "2Mbit/s",
            "3Mbit/s",
            "4Mbit/s",
            "5Mbit/s",
            "6Mbit/s",
            "7Mbit/s",
            "8Mbit/s",
        ]
        self.assertEqual(
            self.apm._parse_access_point_metric("bitrates", bitrates_match),
            bitrates_expected,
        )

    def test_parse_metric_bitrates_three_lines(self):
        bitrates_match = "Bit Rates:1 Mb/s; 2 Mb/s; 3 Mb/s; 4 Mb/s; 5 Mb/s\n                              6 Mb/s; 7 Mb/s; 8 Mb/s\n                    Bit Rates:9 Mb/s; 10 Mb/s; 11 Mb/s; 12 Mb/s\n"
        bitrates_expected = [
            "1Mbit/s",
            "2Mbit/s",
            "3Mbit/s",
            "4Mbit/s",
            "5Mbit/s",
            "6Mbit/s",
            "7Mbit/s",
            "8Mbit/s",
            "9Mbit/s",
            "10Mbit/s",
            "11Mbit/s",
            "12Mbit/s",
        ]
        self.assertEqual(
            self.apm._parse_access_point_metric("bitrates", bitrates_match),
            bitrates_expected,
        )

    def test_parse_metric_invalid_metric(self):
        with self.assertRaises(ValueError):
            self.apm._parse_access_point_metric("Ghz", "invalid_metric")

    def test_parse_metric_invalid_match(self):
        with self.assertRaises(ValueError):
            self.apm._parse_access_point_metric("InvalidMatch", "frequency_unit")


# noinspection PyArgumentList
class ConnectedAccessPointTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.apm = AccessPointMeasurement("example_id")

        self.example_iwconfig_out = 'tun0      no wireless extensions.\n\nwlp1s0    IEEE 802.11  ESSID:"example_essid"  \n          Mode:Managed  Frequency:1.234 GHz  Access Point: 98:DA:C4:A8:D4:D4   \n          Bit Rate=123.4 Mb/s   Tx-Power=12 dBm   \n          Retry short limit:7   RTS thr:off   Fragment thr:off\n          Power Management:on\n          Link Quality=12/34  Signal level=-12 dBm  \n          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0\n          Tx excessive retries:2  Invalid misc:93   Missed beacon:0\n\nlo        no wireless extensions.'
        self.example_iwconfig_out_invalid_frequency_unit = 'tun0      no wireless extensions.\n\nwlp1s0    IEEE 802.11  ESSID:"example_essid"  \n          Mode:Managed  Frequency:1.234 NotRealHz  Access Point: 98:DA:C4:A8:D4:D4   \n          Bit Rate=123.4 Mb/s   Tx-Power=12 dBm   \n          Retry short limit:7   RTS thr:off   Fragment thr:off\n          Power Management:on\n          Link Quality=12/34  Signal level=-12 dBm  \n          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0\n          Tx excessive retries:2  Invalid misc:93   Missed beacon:0\n\nlo        no wireless extensions.'
        self.example_iwconfig_out_missing_metric = 'tun0      no wireless extensions.\n\nwlp1s0    IEEE 802.11  ESSID:"example_essid"  \n          Mode:Managed (freq supposed to be here) Access Point: 98:DA:C4:A8:D4:D4   \n          Bit Rate=123.4 Mb/s   Tx-Power=12 dBm   \n          Retry short limit:7   RTS thr:off   Fragment thr:off\n          Power Management:on\n          Link Quality=12/34  Signal level=-12 dBm  \n          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0\n          Tx excessive retries:2  Invalid misc:93   Missed beacon:0\n\nlo        no wireless extensions.'

    @mock.patch("subprocess.run")
    def test_iwconfig_result_valid_units(self, mock_iwconfig_out):
        example_iwconfig_result = ConnectedAccessPointMeasurementResult(
            id="example_id",
            essid="example_essid",
            bssid="98:DA:C4:A8:D4:D4",
            frequency=1.234,
            frequency_unit=SignalFrequencyUnit("GHz"),
            bitrate=123.4,
            bitrate_unit=NetworkUnit("Mbit/s"),
            tx_power=12,
            tx_power_unit=SignalPowerUnit("dBm"),
            link_quality="12/34",
            signal_level=-12,
            signal_level_unit=SignalPowerUnit("dBm"),
            errors=[],
        )
        run_mock = mock.MagicMock()
        run_mock.stdout = self.example_iwconfig_out
        run_mock.stderr = ""
        mock_iwconfig_out.return_value = run_mock
        self.assertEqual(self.apm._get_iwconfig_result(), example_iwconfig_result)

    @mock.patch("subprocess.run")
    def test_iwconfig_result_invalid_units(self, mock_iwconfig_out):
        example_iwconfig_result = ConnectedAccessPointMeasurementResult(
            id="example_id",
            essid=None,
            bssid=None,
            frequency=None,
            frequency_unit=None,
            bitrate=None,
            bitrate_unit=None,
            tx_power=None,
            tx_power_unit=None,
            link_quality=None,
            signal_level=None,
            signal_level_unit=None,
            errors=[
                Error(
                    key="iwconfig-frequency_unit",
                    description="Could not process the frequency unit regex.",
                    traceback=self.example_iwconfig_out_invalid_frequency_unit,
                )
            ],
        )
        run_mock = mock.MagicMock()
        run_mock.stdout = self.example_iwconfig_out_invalid_frequency_unit
        run_mock.stderr = ""
        mock_iwconfig_out.return_value = run_mock
        self.assertEqual(self.apm._get_iwconfig_result(), example_iwconfig_result)

    @mock.patch("subprocess.run")
    def test_iwconfig_result_missing_metric(self, mock_iwconfig_out):
        example_iwconfig_result = ConnectedAccessPointMeasurementResult(
            id="example_id",
            essid="example_essid",
            bssid="98:DA:C4:A8:D4:D4",
            frequency=None,
            frequency_unit=None,
            bitrate=123.4,
            bitrate_unit=NetworkUnit("Mbit/s"),
            tx_power=12,
            tx_power_unit=SignalPowerUnit("dBm"),
            link_quality="12/34",
            signal_level=-12,
            signal_level_unit=SignalPowerUnit("dBm"),
            errors=[],
        )
        run_mock = mock.MagicMock()
        run_mock.stdout = self.example_iwconfig_out_missing_metric
        run_mock.stderr = ""
        mock_iwconfig_out.return_value = run_mock
        self.assertEqual(self.apm._get_iwconfig_result(), example_iwconfig_result)

    def test_parse_metric_bitrate_unit(self):
        bitrate_unit_match = "Mb/s"
        bitrate_unit_expected = NetworkUnit("Mbit/s")
        self.assertEqual(
            self.apm._parse_connected_access_point_metric(
                "bitrate_unit", bitrate_unit_match
            ),
            bitrate_unit_expected,
        )

    def test_parse_metric_invalid_metric(self):
        with self.assertRaises(ValueError):
            self.apm._parse_connected_access_point_metric("Ghz", "invalid_metric")

    def test_parse_metric_invalid_match(self):
        with self.assertRaises(ValueError):
            self.apm._parse_connected_access_point_metric(
                "InvalidMatch", "frequency_unit"
            )
