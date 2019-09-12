# -*- coding: utf-8 -*-
from unittest import TestCase, mock
import six

from measurement.plugins.download_speed.measurements import WGET_OUTPUT_REGEX
from measurement.plugins.download_speed.measurements import (
    DownloadSpeedMeasurement,
)
from measurement.plugins.download_speed.results import (
    DownloadSpeedMeasurementResult,
    LatencyMeasurementResult,
)
from measurement.units import NetworkUnit, StorageUnit


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
    def setUp(self) -> None:
        super().setUp()

    def test_invalid_hosts(self, *args):
        self.assertRaises(
            ValueError,
            DownloadSpeedMeasurement,
            "test",
            ["invalid..host"],
        )

    def test_invalid_count(self, *args):
        self.assertRaises(
            TypeError,
            DownloadSpeedMeasurement,
            "test",
            ["http://validfakeurl.com"],
            count="invalid-count"
        )

    def test_invalid_negative_count(self, *args):
        self.assertRaises(
            ValueError,
            DownloadSpeedMeasurement,
            "test",
            ["http://validfakeurl.com"],
            count=-2
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
            )
        ]
        mock_latency_results.side_effect = results
        self.assertEqual(
            self.measurement._find_least_latent_url(self.example_urls),
            [(self.example_urls[1], results[1]), (self.example_urls[2], results[2]), (self.example_urls[0], results[0])]
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
            ),
        ]
        mock_latency_results.side_effect = results
        self.assertEqual(
            self.measurement._find_least_latent_url([self.example_urls[1]]),
            [(self.example_urls[1], results[0])]
        )
