# -*- coding: utf-8 -*-
from unittest import TestCase, mock
import six
import subprocess

from measurement.results import Error
from measurement.plugins.download_speed.measurements import WGET_OUTPUT_REGEX
from measurement.plugins.download_speed.measurements import DownloadSpeedMeasurement
from measurement.plugins.download_speed.measurements import WGET_ERRORS, LATENCY_ERRORS
from measurement.plugins.download_speed.results import (
    DownloadSpeedMeasurementResult,
    LatencyMeasurementResult,
)

from measurement.units import NetworkUnit, StorageUnit

# NOTE: To match what subprocess calls output, wget output strings
#       should end with "\n\n" and latency output strings should end with "\n"


def test_wget_output_regex_accepts_anticipated_format():
    anticipated_format = six.ensure_str(
        "2019-08-07 09:12:08 (16.7 MB/s) - '/dev/null’ saved [11376]"
    )
    results = WGET_OUTPUT_REGEX.search(anticipated_format).groupdict()
    assert results == {
        "download_rate": "16.7",
        "download_size": "11376",
        "download_unit": "MB/s",
    }


class DownloadSpeedMeasurementCreationTestCase(TestCase):

    def test_invalid_hosts(self, *args):
        self.assertRaises(
            ValueError, DownloadSpeedMeasurement, "test", ["invalid..host"]
        )

    def test_invalid_count(self, *args):
        self.assertRaises(
            TypeError,
            DownloadSpeedMeasurement,
            "test",
            ["http://validfakeurl.com"],
            count="invalid-count",
        )

    def test_invalid_negative_count(self, *args):
        self.assertRaises(
            ValueError,
            DownloadSpeedMeasurement,
            "test",
            ["http://validfakeurl.com"],
            count=-2,
        )


class DownloadSpeedMeasurementWgetTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.measurement = DownloadSpeedMeasurement(
            "test", ["https://validfakehost.com/test"]
        )
        self.valid_wget = DownloadSpeedMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=NetworkUnit("Mibit/s"),
            download_rate=133.6,
            download_size=11376,
            download_size_unit=StorageUnit.megabit,
            errors=[],
        )
        self.invalid_wget = DownloadSpeedMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            errors=[
                Error(
                    key="wget-err",
                    description=WGET_ERRORS.get("wget-err", ""),
                    traceback="\n2019-08-07 09:12:08 (16.7 MB/s) - '/dev/null’ saved [11376]\n\n",
                )
            ],
        )
        self.invalid_regex = DownloadSpeedMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            errors=[
                Error(
                    key="wget-regex",
                    description=WGET_ERRORS.get("wget-regex", ""),
                    traceback="\n2019-08-07 09:12:08 [BAD REGEX]\n\n",
                )
            ],
        )

    @mock.patch("subprocess.run")
    def test_valid_wget(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="b''",
            stderr="\n2019-08-07 09:12:08 (16.7 MB/s) - '/dev/null’ saved [11376]\n\n",
        )
        self.assertEqual(
            self.valid_wget,
            self.measurement._get_wget_results(
                "http://validfakehost.com/test", self.measurement.download_timeout
            ),
        )

    @mock.patch("subprocess.run")
    def test_invalid_wget(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="b''",
            stderr="\n2019-08-07 09:12:08 (16.7 MB/s) - '/dev/null’ saved [11376]\n\n",
        )
        self.assertEqual(
            self.invalid_wget,
            self.measurement._get_wget_results(
                "http://validfakehost.com/test", self.measurement.download_timeout
            ),
        )

    @mock.patch("subprocess.run")
    def test_wget_invalid_regex(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="b''",
            stderr="\n2019-08-07 09:12:08 [BAD REGEX]\n\n",
        )
        self.assertEqual(
            self.invalid_regex,
            self.measurement._get_wget_results(
                "http://validfakehost.com/test", self.measurement.download_timeout
            ),
        )


class DownloadSpeedMeasurementLatencyTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.measurement = DownloadSpeedMeasurement(
            "test", ["https://validfakehost.com/test"]
        )
        self.valid_latency = LatencyMeasurementResult(
            id="test",
            host="validfakehost.com",
            minimum_latency=5.484,
            average_latency=6.133,
            maximum_latency=7.133,
            median_deviation=0.611,
            errors=[],
        )
        self.invalid_latency = LatencyMeasurementResult(
            id="test",
            host="validfakehost.com",
            minimum_latency=None,
            average_latency=None,
            maximum_latency=None,
            median_deviation=None,
            errors=[
                Error(
                    key="ping-err",
                    description=LATENCY_ERRORS.get("ping-err", ""),
                    traceback="the ping messed up!",
                )
            ],
        )
        self.invalid_regex = LatencyMeasurementResult(
            id="test",
            host="validfakehost.com",
            minimum_latency=None,
            average_latency=None,
            maximum_latency=None,
            median_deviation=None,
            errors=[
                Error(
                    key="ping-regex",
                    description=LATENCY_ERRORS.get("ping-regex", ""),
                    traceback="\nrtt min/avg/max/mdev = [BAD REGEX] ms\n",
                )
            ],
        )

    @mock.patch("subprocess.run")
    def test_valid_latency(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="\nrtt min/avg/max/mdev = 5.484/6.133/7.133/0.611 ms\n",
            stderr="",
        )
        self.assertEqual(
            self.valid_latency,
            self.measurement._get_latency_results("validfakehost.com"),
        )

    @mock.patch("subprocess.run")
    def test_invalid_latency(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="\nrtt min/avg/max/mdev = 5.484/6.133/7.133/0.611 ms\n",
            stderr="the ping messed up!",
        )
        self.assertEqual(
            self.invalid_latency,
            self.measurement._get_latency_results("validfakehost.com"),
        )

    @mock.patch("subprocess.run")
    def test_latency_invalid_regex(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="\nrtt min/avg/max/mdev = [BAD REGEX] ms\n",
            stderr="",
        )
        self.assertEqual(
            self.invalid_regex,
            self.measurement._get_latency_results("validfakehost.com"),
        )


class DownloadSpeedMeasurementClosestServerTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.example_urls = [
            "http://n1-validfakehost.com",
            "http://n2-validfakehost.com",
            "http://n3-validfakehost.com",
        ]
        self.measurement = DownloadSpeedMeasurement("test", self.example_urls)
        print("asdf")

    @mock.patch.object(DownloadSpeedMeasurement, "_get_latency_results")
    def test_sort_least_latent_url(self, mock_latency_results):
        results = [
            LatencyMeasurementResult(
                id="test",
                host="n1-validfakehost.com",
                minimum_latency=None,
                average_latency=None,
                maximum_latency=None,
                median_deviation=None,
                errors=[],
            ),
            LatencyMeasurementResult(
                id="test",
                host="n2-validfakehost.com",
                minimum_latency=None,
                average_latency=25.0,
                maximum_latency=None,
                median_deviation=None,
                errors=[],
            ),
            LatencyMeasurementResult(
                id="test",
                host="n3-validfakehost.com",
                minimum_latency=None,
                average_latency=999.0,
                maximum_latency=None,
                median_deviation=None,
                errors=[],
            ),
        ]
        mock_latency_results.side_effect = results
        self.assertEqual(
            self.measurement._find_least_latent_url(self.example_urls),
            [
                (self.example_urls[1], results[1]),
                (self.example_urls[2], results[2]),
                (self.example_urls[0], results[0]),
            ],
        )

    @mock.patch.object(DownloadSpeedMeasurement, "_get_latency_results")
    def test_sort_one_url(self, mock_latency_results):
        results = [
            LatencyMeasurementResult(
                id="test",
                host="n2-validfakehost.com",
                minimum_latency=None,
                average_latency=25.0,
                maximum_latency=None,
                median_deviation=None,
                errors=[],
            )
        ]
        mock_latency_results.side_effect = results
        self.assertEqual(
            self.measurement._find_least_latent_url([self.example_urls[1]]),
            [(self.example_urls[1], results[0])],
        )
