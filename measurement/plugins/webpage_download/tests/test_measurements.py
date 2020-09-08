# -*- coding: utf-8 -*-
from unittest import TestCase, mock
import six
import subprocess

from measurement.plugins.latency.measurements import LatencyMeasurement
from measurement.results import Error
from measurement.plugins.webpage_download.measurements import WGET_OUTPUT_REGEX
from measurement.plugins.webpage_download.measurements import WebpageMeasurement
from measurement.plugins.webpage_download.measurements import WGET_ERRORS
from measurement.plugins.webpage_download.results import WebpageMeasurementResult
from measurement.plugins.latency.results import LatencyMeasurementResult

from measurement.units import NetworkUnit, StorageUnit, TimeUnit

# NOTE: To match what subprocess calls output, wget output strings
#       should end with "\n\n" and latency output strings should end with "\n"


def test_wget_output_regex_accepts_anticipated_format():
    anticipated_format = six.ensure_str(
        "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3s (75.8 Mb/s)\n"
    )
    results = WGET_OUTPUT_REGEX.search(anticipated_format).groupdict()
    assert results == {
        "download_rate": "75.8",
        "download_rate_unit": "Mb/s",
        "download_size": "2.4",
        "download_size_unit": "M",
        "file_count": "117",
        "elapsed_time": "0.3",
        "elapsed_time_unit": "s",
    }


class WebpageMeasurementWgetTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.wpm = WebpageMeasurement("test", "http://validfakehost.com/test")
        self.pretend_wget_out_kibit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3s (133.6 Kb/s)\n\n"
        self.pretend_wget_out_mibit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3s (75.8 Mb/s)\n\n"
        self.pretend_wget_out_invalid_rate_unit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3s (75.8 Tb/s)\n\n"
        self.invalid_rate_unit_matches = {
            "download_rate": "75.8",
            "download_rate_unit": "Tb/s",
            "download_size": "2.4",
            "download_size_unit": "M",
            "file_count": "117",
            "elapsed_time": "0.3",
            "elapsed_time_unit": "s",
        }
        self.pretend_wget_out_invalid_size_unit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4T in 0.3s (75.8 Mb/s)\n\n"
        self.invalid_size_unit_matches = {
            "download_rate": "75.8",
            "download_rate_unit": "Mb/s",
            "download_size": "2.4",
            "download_size_unit": "T",
            "file_count": "117",
            "elapsed_time": "0.3",
            "elapsed_time_unit": "s",
        }
        self.pretend_wget_out_invalid_time_unit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3Days (75.8 Mb/s)\n\n"
        self.invalid_time_unit_matches = {
            "download_rate": "75.8",
            "download_rate_unit": "Mb/s",
            "download_size": "2.4",
            "download_size_unit": "M",
            "file_count": "117",
            "elapsed_time": "0.3",
            "elapsed_time_unit": "Days",
        }
        self.pretend_wget_out_garbage = "FINISHED --2020-09-07 11:35:57--\nW0t4l t4ll clock time: 2.4s\nD0wnl04d3d: 117 tiles, 2.4M in 0.3s (75.8 Mb/s)\n\n"
        self.pretend_wget_out_invalid_rate_metric = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3s (&&&& Mb/s)\n\n"
        self.valid_wget_kibit_sec = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=NetworkUnit("Kibit/s"),
            download_rate=133.6,
            download_size=2.4,
            download_size_unit=StorageUnit("MiB"),
            downloaded_file_count=117,
            elapsed_time=0.3,
            elapsed_time_unit=TimeUnit("s"),
            errors=[],
        )
        self.valid_wget_mibit_sec = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=NetworkUnit("Mibit/s"),
            download_rate=75.8,
            download_size=2.4,
            download_size_unit=StorageUnit("MiB"),
            downloaded_file_count=117,
            elapsed_time=0.3,
            elapsed_time_unit=TimeUnit("s"),
            errors=[],
        )
        self.invalid_wget_mibit_sec = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            downloaded_file_count=None,
            elapsed_time=None,
            elapsed_time_unit=None,
            errors=[
                Error(
                    key="wget-err",
                    description=WGET_ERRORS.get("wget-err", ""),
                    traceback=self.pretend_wget_out_mibit,
                )
            ],
        )
        self.invalid_wget_rate_unit = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            downloaded_file_count=None,
            elapsed_time=None,
            elapsed_time_unit=None,
            errors=[
                Error(
                    key="wget-regex-unit",
                    description=WGET_ERRORS.get("wget-regex-unit", ""),
                    traceback=(self.invalid_rate_unit_matches),
                )
            ],
        )
        self.invalid_wget_size_unit = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            downloaded_file_count=None,
            elapsed_time=None,
            elapsed_time_unit=None,
            errors=[
                Error(
                    key="wget-regex-unit",
                    description=WGET_ERRORS.get("wget-regex-unit", ""),
                    traceback=(self.invalid_size_unit_matches),
                )
            ],
        )
        self.invalid_wget_time_unit = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            downloaded_file_count=None,
            elapsed_time=None,
            elapsed_time_unit=None,
            errors=[
                Error(
                    key="wget-regex-unit",
                    description=WGET_ERRORS.get("wget-regex-unit", ""),
                    traceback=(self.invalid_time_unit_matches),
                )
            ],
        )
        self.invalid_wget_regex = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            downloaded_file_count=None,
            elapsed_time=None,
            elapsed_time_unit=None,
            errors=[
                Error(
                    key="wget-regex",
                    description=WGET_ERRORS.get("wget-regex", ""),
                    traceback=self.pretend_wget_out_garbage,
                )
            ],
        )
        self.invalid_wget_rate_metric = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            downloaded_file_count=None,
            elapsed_time=None,
            elapsed_time_unit=None,
            errors=[
                Error(
                    key="wget-regex-metric",
                    description=WGET_ERRORS.get("wget-regex-metric", ""),
                    traceback=self.pretend_wget_out_invalid_rate_metric,
                )
            ],
        )

    @mock.patch("shutil.rmtree")
    @mock.patch("subprocess.run")
    def test_valid_wget_kibit_sec(self, mock_run, mock_rmtree):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="b''", stderr=self.pretend_wget_out_kibit,
        )
        mock_rmtree.side_effect = [0]
        self.assertEqual(
            self.valid_wget_kibit_sec,
            self.wpm._get_webpage_result(
                "http://validfakehost.com/test", self.wpm.download_timeout
            ),
        )

    @mock.patch("shutil.rmtree")
    @mock.patch("subprocess.run")
    def test_valid_wget_mibit_sec(self, mock_run, mock_rmtree):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="b''", stderr=self.pretend_wget_out_mibit,
        )
        mock_rmtree.side_effect = [0]
        self.assertEqual(
            self.valid_wget_mibit_sec,
            self.wpm._get_webpage_result(
                "http://validfakehost.com/test", self.wpm.download_timeout
            ),
        )

    @mock.patch("subprocess.run")
    def test_invalid_wget(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="b''", stderr=self.pretend_wget_out_mibit,
        )
        self.assertEqual(
            self.invalid_wget_mibit_sec,
            self.wpm._get_webpage_result(
                "http://validfakehost.com/test", self.wpm.download_timeout
            ),
        )

    @mock.patch("subprocess.run")
    def test_invalid_wget_rate_unit(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="b''",
            stderr=self.pretend_wget_out_invalid_rate_unit,
        )
        self.assertEqual(
            self.invalid_wget_rate_unit,
            self.wpm._get_webpage_result(
                "http://validfakehost.com/test", self.wpm.download_timeout
            ),
        )

    @mock.patch("subprocess.run")
    def test_invalid_wget_size_unit(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="b''",
            stderr=self.pretend_wget_out_invalid_size_unit,
        )
        self.assertEqual(
            self.invalid_wget_size_unit,
            self.wpm._get_webpage_result(
                "http://validfakehost.com/test", self.wpm.download_timeout
            ),
        )

    @mock.patch("subprocess.run")
    def test_invalid_wget_time_unit(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="b''",
            stderr=self.pretend_wget_out_invalid_time_unit,
        )
        self.assertEqual(
            self.invalid_wget_time_unit,
            self.wpm._get_webpage_result(
                "http://validfakehost.com/test", self.wpm.download_timeout
            ),
        )

    @mock.patch("subprocess.run")
    def test_wget_invalid_regex(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="b''", stderr=self.pretend_wget_out_garbage,
        )
        self.assertEqual(
            self.invalid_wget_regex,
            self.wpm._get_webpage_result(
                "http://validfakehost.com/test", self.wpm.download_timeout
            ),
        )


class WebpageMeasurementMeasureTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.wpm = WebpageMeasurement("test", "http://validfakehost.com/test")
        self.simple_wget_result = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=NetworkUnit("Kibit/s"),
            download_rate=133.6,
            download_size=2.4,
            download_size_unit=StorageUnit("MiB"),
            downloaded_file_count=117,
            elapsed_time=0.3,
            elapsed_time_unit=TimeUnit("s"),
            errors=[],
        )
        self.simple_latency_result = (
            LatencyMeasurementResult(
                id="test",
                host="validfakehost.com",
                minimum_latency=None,
                average_latency=25.0,
                maximum_latency=None,
                median_deviation=None,
                errors=[],
                packets_transmitted=None,
                packets_received=None,
                packets_lost=None,
                packets_lost_unit=None,
                time=None,
                time_unit=None,
            ),
        )

    @mock.patch(
        "measurement.plugins.webpage_download.measurements.WebpageMeasurement._get_webpage_result"
    )
    @mock.patch.object(LatencyMeasurement, "measure")
    def test_valid_measure(self, mock_latency_results, mock_wget_result):
        mock_latency_results.return_value = self.simple_latency_result
        mock_wget_result.return_value = self.simple_wget_result
        self.assertEqual(
            self.wpm.measure(), [self.simple_wget_result, self.simple_latency_result]
        )
