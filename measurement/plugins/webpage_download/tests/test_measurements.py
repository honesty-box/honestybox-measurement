# -*- coding: utf-8 -*-
from unittest import TestCase, mock
from unittest.mock import call

import six
import subprocess

from measurement.plugins.latency.measurements import LatencyMeasurement
from measurement.results import Error
from measurement.plugins.webpage_download.measurements import WebpageMeasurement
from measurement.plugins.webpage_download.measurements import WEB_ERRORS

from measurement.plugins.webpage_download.results import WebpageMeasurementResult
from measurement.plugins.latency.results import LatencyMeasurementResult

from measurement.units import NetworkUnit, StorageUnit, TimeUnit, RatioUnit

# class WebpageMeasurementWgetTestCase(TestCase):
#     def setUp(self) -> None:
#         super().setUp()
#         self.wpm = WebpageMeasurement("test", "http://validfakehost.com/test")
#         self.pretend_wget_out_kibit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3s (133.6 Kb/s)\n\n"
#         self.pretend_wget_out_mibit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3s (75.8 Mb/s)\n\n"
#         self.pretend_wget_out_invalid_rate_unit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3s (75.8 Tb/s)\n\n"
#         self.invalid_rate_unit_matches = {
#             "download_rate": "75.8",
#             "download_rate_unit": "Tb/s",
#             "download_size": "2.4",
#             "download_size_unit": "M",
#             "file_count": "117",
#             "elapsed_time": "0.3",
#             "elapsed_time_unit": "s",
#         }
#         self.pretend_wget_out_invalid_size_unit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4T in 0.3s (75.8 Mb/s)\n\n"
#         self.invalid_size_unit_matches = {
#             "download_rate": "75.8",
#             "download_rate_unit": "Mb/s",
#             "download_size": "2.4",
#             "download_size_unit": "T",
#             "file_count": "117",
#             "elapsed_time": "0.3",
#             "elapsed_time_unit": "s",
#         }
#         self.pretend_wget_out_invalid_time_unit = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3Days (75.8 Mb/s)\n\n"
#         self.invalid_time_unit_matches = {
#             "download_rate": "75.8",
#             "download_rate_unit": "Mb/s",
#             "download_size": "2.4",
#             "download_size_unit": "M",
#             "file_count": "117",
#             "elapsed_time": "0.3",
#             "elapsed_time_unit": "Days",
#         }
#         self.pretend_wget_out_garbage = "FINISHED --2020-09-07 11:35:57--\nW0t4l t4ll clock time: 2.4s\nD0wnl04d3d: 117 tiles, 2.4M in 0.3s (75.8 Mb/s)\n\n"
#         self.pretend_wget_out_invalid_rate_metric = "FINISHED --2020-09-07 11:35:57--\nTotal wall clock time: 2.4s\nDownloaded: 117 files, 2.4M in 0.3s (&&&& Mb/s)\n\n"
#         self.valid_wget_kibit_sec = WebpageMeasurementResult(
#             id="test",
#             url="http://validfakehost.com/test",
#             download_rate_unit=NetworkUnit("Kibit/s"),
#             download_rate=133.6,
#             download_size=2.4,
#             download_size_unit=StorageUnit("MiB"),
#             downloaded_file_count=117,
#             elapsed_time=0.3,
#             elapsed_time_unit=TimeUnit("s"),
#             errors=[],
#         )
#         self.valid_wget_mibit_sec = WebpageMeasurementResult(
#             id="test",
#             url="http://validfakehost.com/test",
#             download_rate_unit=NetworkUnit("Mibit/s"),
#             download_rate=75.8,
#             download_size=2.4,
#             download_size_unit=StorageUnit("MiB"),
#             downloaded_file_count=117,
#             elapsed_time=0.3,
#             elapsed_time_unit=TimeUnit("s"),
#             errors=[],
#         )
#         self.invalid_wget_mibit_sec = WebpageMeasurementResult(
#             id="test",
#             url="http://validfakehost.com/test",
#             download_rate_unit=None,
#             download_rate=None,
#             download_size=None,
#             download_size_unit=None,
#             downloaded_file_count=None,
#             elapsed_time=None,
#             elapsed_time_unit=None,
#             errors=[
#                 Error(
#                     key="wget-err",
#                     description=WGET_ERRORS.get("wget-err", ""),
#                     traceback=self.pretend_wget_out_mibit,
#                 )
#             ],
#         )
#         self.invalid_wget_rate_unit = WebpageMeasurementResult(
#             id="test",
#             url="http://validfakehost.com/test",
#             download_rate_unit=None,
#             download_rate=None,
#             download_size=None,
#             download_size_unit=None,
#             downloaded_file_count=None,
#             elapsed_time=None,
#             elapsed_time_unit=None,
#             errors=[
#                 Error(
#                     key="wget-regex-unit",
#                     description=WGET_ERRORS.get("wget-regex-unit", ""),
#                     traceback=(self.invalid_rate_unit_matches),
#                 )
#             ],
#         )
#         self.invalid_wget_size_unit = WebpageMeasurementResult(
#             id="test",
#             url="http://validfakehost.com/test",
#             download_rate_unit=None,
#             download_rate=None,
#             download_size=None,
#             download_size_unit=None,
#             downloaded_file_count=None,
#             elapsed_time=None,
#             elapsed_time_unit=None,
#             errors=[
#                 Error(
#                     key="wget-regex-unit",
#                     description=WGET_ERRORS.get("wget-regex-unit", ""),
#                     traceback=(self.invalid_size_unit_matches),
#                 )
#             ],
#         )
#         self.invalid_wget_time_unit = WebpageMeasurementResult(
#             id="test",
#             url="http://validfakehost.com/test",
#             download_rate_unit=None,
#             download_rate=None,
#             download_size=None,
#             download_size_unit=None,
#             downloaded_file_count=None,
#             elapsed_time=None,
#             elapsed_time_unit=None,
#             errors=[
#                 Error(
#                     key="wget-regex-unit",
#                     description=WGET_ERRORS.get("wget-regex-unit", ""),
#                     traceback=(self.invalid_time_unit_matches),
#                 )
#             ],
#         )
#         self.invalid_wget_regex = WebpageMeasurementResult(
#             id="test",
#             url="http://validfakehost.com/test",
#             download_rate_unit=None,
#             download_rate=None,
#             download_size=None,
#             download_size_unit=None,
#             downloaded_file_count=None,
#             elapsed_time=None,
#             elapsed_time_unit=None,
#             errors=[
#                 Error(
#                     key="wget-regex",
#                     description=WGET_ERRORS.get("wget-regex", ""),
#                     traceback=self.pretend_wget_out_garbage,
#                 )
#             ],
#         )
#         self.invalid_wget_rate_metric = WebpageMeasurementResult(
#             id="test",
#             url="http://validfakehost.com/test",
#             download_rate_unit=None,
#             download_rate=None,
#             download_size=None,
#             download_size_unit=None,
#             downloaded_file_count=None,
#             elapsed_time=None,
#             elapsed_time_unit=None,
#             errors=[
#                 Error(
#                     key="wget-regex-metric",
#                     description=WGET_ERRORS.get("wget-regex-metric", ""),
#                     traceback=self.pretend_wget_out_invalid_rate_metric,
#                 )
#             ],
#         )
#
#     @mock.patch("shutil.rmtree")
#     @mock.patch("subprocess.run")
#     def test_valid_wget_kibit_sec(self, mock_run, mock_rmtree):
#         mock_run.return_value = subprocess.CompletedProcess(
#             args=[], returncode=0, stdout="b''", stderr=self.pretend_wget_out_kibit,
#         )
#         mock_rmtree.side_effect = [0]
#         self.assertEqual(
#             self.valid_wget_kibit_sec,
#             self.wpm._get_webpage_result_wget(
#                 "http://validfakehost.com/test", self.wpm.download_timeout
#             ),
#         )
#
#     @mock.patch("shutil.rmtree")
#     @mock.patch("subprocess.run")
#     def test_valid_wget_mibit_sec(self, mock_run, mock_rmtree):
#         mock_run.return_value = subprocess.CompletedProcess(
#             args=[], returncode=0, stdout="b''", stderr=self.pretend_wget_out_mibit,
#         )
#         mock_rmtree.side_effect = [0]
#         self.assertEqual(
#             self.valid_wget_mibit_sec,
#             self.wpm._get_webpage_result_wget(
#                 "http://validfakehost.com/test", self.wpm.download_timeout
#             ),
#         )
#
#     @mock.patch("subprocess.run")
#     def test_invalid_wget(self, mock_run):
#         mock_run.return_value = subprocess.CompletedProcess(
#             args=[], returncode=1, stdout="b''", stderr=self.pretend_wget_out_mibit,
#         )
#         self.assertEqual(
#             self.invalid_wget_mibit_sec,
#             self.wpm._get_webpage_result_wget(
#                 "http://validfakehost.com/test", self.wpm.download_timeout
#             ),
#         )
#
#     @mock.patch("subprocess.run")
#     def test_invalid_wget_rate_unit(self, mock_run):
#         mock_run.return_value = subprocess.CompletedProcess(
#             args=[],
#             returncode=0,
#             stdout="b''",
#             stderr=self.pretend_wget_out_invalid_rate_unit,
#         )
#         self.assertEqual(
#             self.invalid_wget_rate_unit,
#             self.wpm._get_webpage_result_wget(
#                 "http://validfakehost.com/test", self.wpm.download_timeout
#             ),
#         )
#
#     @mock.patch("subprocess.run")
#     def test_invalid_wget_size_unit(self, mock_run):
#         mock_run.return_value = subprocess.CompletedProcess(
#             args=[],
#             returncode=0,
#             stdout="b''",
#             stderr=self.pretend_wget_out_invalid_size_unit,
#         )
#         self.assertEqual(
#             self.invalid_wget_size_unit,
#             self.wpm._get_webpage_result_wget(
#                 "http://validfakehost.com/test", self.wpm.download_timeout
#             ),
#         )
#
#     @mock.patch("subprocess.run")
#     def test_invalid_wget_time_unit(self, mock_run):
#         mock_run.return_value = subprocess.CompletedProcess(
#             args=[],
#             returncode=0,
#             stdout="b''",
#             stderr=self.pretend_wget_out_invalid_time_unit,
#         )
#         self.assertEqual(
#             self.invalid_wget_time_unit,
#             self.wpm._get_webpage_result_wget(
#                 "http://validfakehost.com/test", self.wpm.download_timeout
#             ),
#         )
#
#     @mock.patch("subprocess.run")
#     def test_wget_invalid_regex(self, mock_run):
#         mock_run.return_value = subprocess.CompletedProcess(
#             args=[], returncode=0, stdout="b''", stderr=self.pretend_wget_out_garbage,
#         )
#         self.assertEqual(
#             self.invalid_wget_regex,
#             self.wpm._get_webpage_result_wget(
#                 "http://validfakehost.com/test", self.wpm.download_timeout
#             ),
#         )


# class WebpageMeasurementMeasureTestCase(TestCase):
#     def setUp(self) -> None:
#         super().setUp()
#         self.wpm = WebpageMeasurement("test", "http://validfakehost.com/test")
#         self.simple_wget_result = WebpageMeasurementResult(
#             id="test",
#             url="http://validfakehost.com/test",
#             download_rate_unit=NetworkUnit("Kibit/s"),
#             download_rate=133.6,
#             download_size=2.4,
#             download_size_unit=StorageUnit("MiB"),
#             downloaded_file_count=117,
#             elapsed_time=0.3,
#             elapsed_time_unit=TimeUnit("s"),
#             errors=[],
#         )
#         self.simple_latency_result = (
#             LatencyMeasurementResult(
#                 id="test",
#                 host="validfakehost.com",
#                 minimum_latency=None,
#                 average_latency=25.0,
#                 maximum_latency=None,
#                 median_deviation=None,
#                 errors=[],
#                 packets_transmitted=None,
#                 packets_received=None,
#                 packets_lost=None,
#                 packets_lost_unit=None,
#                 time=None,
#                 time_unit=None,
#             ),
#         )
#
#     @mock.patch(
#         "measurement.plugins.webpage_download.measurements.WebpageMeasurement._get_webpage_result"
#     )
#     @mock.patch.object(LatencyMeasurement, "measure")
#     def test_valid_measure(self, mock_latency_results, mock_wget_result):
#         mock_latency_results.return_value = self.simple_latency_result
#         mock_wget_result.return_value = self.simple_wget_result
#         self.assertEqual(
#             self.wpm.measure(), [self.simple_wget_result, self.simple_latency_result]
#         )


class WebpageMeasurementResultsTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.wpm = WebpageMeasurement("test", "http://validfakehost.com/test")
        self.simple_webpage_output = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate=100 / 1.00 * 8,
            download_rate_unit=NetworkUnit("bit/s"),
            download_size=100,
            download_size_unit=StorageUnit("B"),
            asset_count=123,
            failed_asset_downloads=0,
            elapsed_time=1.00,
            elapsed_time_unit=TimeUnit("s"),
            errors=[],
        )
        self.simple_latency_output = LatencyMeasurementResult(
            id=("test"),
            host="validfakehost.com",
            minimum_latency=0,
            average_latency=0,
            maximum_latency=0,
            median_deviation=0,
            packets_transmitted=0,
            packets_received=0,
            packets_lost=0,
            packets_lost_unit=RatioUnit("%"),
            time=0,
            time_unit=TimeUnit("d"),
            errors=[],
        )
        self.simple_asset_download_metrics = {
            "asset_download_size": 90,
            "failed_asset_downloads": 0,
            "completion_time": 2.00,
        }
        self.get_error_result = WebpageMeasurementResult(
            id="test",
            url="http://validfakehost.com/test",
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            asset_count=None,
            failed_asset_downloads=None,
            elapsed_time=None,
            elapsed_time_unit=None,
            errors=[
                Error(
                    key="web-get",
                    description=WEB_ERRORS.get("web-get", ""),
                    traceback="[Errno -2] Name or service not known",
                )
            ],
        )

    @mock.patch("measurement.plugins.latency.measurements.LatencyMeasurement.measure")
    @mock.patch(
        "measurement.plugins.webpage_download.measurements.WebpageMeasurement._get_webpage_result"
    )
    def test_measure(self, mock_get_webpage, mock_get_latency):
        mock_get_webpage.return_value = self.simple_webpage_output
        mock_get_latency.return_value = self.simple_latency_output
        self.assertEqual(
            self.wpm.measure(), [self.simple_webpage_output, self.simple_latency_output]
        )

    @mock.patch(
        "measurement.plugins.webpage_download.measurements.WebpageMeasurement._download_assets"
    )
    @mock.patch(
        "measurement.plugins.webpage_download.measurements.WebpageMeasurement._parse_html"
    )
    @mock.patch("requests.Session")
    @mock.patch("time.time")
    def test_get_requests_measurement(
        self, mock_time, mock_get_session, mock_parse_html, mock_download_assets
    ):
        mock_time.return_value = 1.00
        mock_session = mock.MagicMock()
        mock_resp = mock.MagicMock()
        # Total 'downloaded' size is 100 bytes
        mock_resp.text = "Ten chars_"
        mock_session.get.side_effect = [mock_resp]
        mock_parse_html.return_value = [
            "URL number {x}".format(x=i + 1) for i in range(123)
        ]
        mock_download_assets.return_value = self.simple_asset_download_metrics
        mock_get_session.return_value = mock_session
        self.assertEqual(
            self.wpm._get_webpage_result(
                "http://validfakehost.com/test", "validfakehost.com", "https"
            ),
            self.simple_webpage_output,
        )

    @mock.patch(
        "measurement.plugins.webpage_download.measurements.WebpageMeasurement._download_assets"
    )
    @mock.patch(
        "measurement.plugins.webpage_download.measurements.WebpageMeasurement._parse_html"
    )
    @mock.patch("requests.Session")
    @mock.patch("time.time")
    def test_get_requests_error(
        self, mock_time, mock_get_session, mock_parse_html, mock_download_assets
    ):
        mock_time.return_value = 1.00
        mock_session = mock.MagicMock()
        mock_session.get.side_effect = [
            ConnectionError("[Errno -2] Name or service not known")
        ]
        mock_get_session.return_value = mock_session
        self.assertEqual(
            self.wpm._get_webpage_result(
                "http://validfakehost.com/test", "validfakehost.com", "https"
            ),
            self.get_error_result,
        )


class WebpageHTMLParseTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.wpm = WebpageMeasurement("test", "http://validfakehost.com/test")
        self.img_html = (
            '<img alt="HBOX" id="logo" src="/logo/src/name.png"/>\n'
            '<img alt="HBOX" id="another" src="/another/src/name.png"/>\n'
            '<img alt="HBOX" id="ayylmao" src="/ayylmao/src/name.png"/>\n'
            '<img alt="HBOX" id="no source"/>\n'
        )
        self.img_urls = [
            "/logo/src/name.png",
            "/another/src/name.png",
            "/ayylmao/src/name.png",
        ]
        self.script_html = (
            '<script src="/script_one/src/name.js"/>\n'
            '<script src="/script_two/src/name.js"/>\n'
            '<script src="/script_three/src/name.js"/>\n'
            "<script/>\n"
        )
        self.script_urls = [
            "/script_one/src/name.js",
            "/script_two/src/name.js",
            "/script_three/src/name.js",
        ]
        self.link_html = (
            '<link href="http://validfakehost.com/test" rel="manifest"/>\n'
            '<link href="http://externalfakehost.com/one" rel="modulepreload"/>\n'
            '<link href="http://externalfakehost.com/two" rel="preload"/>\n'
            '<link href="http://externalfakehost.com/three" rel="prerender"/>\n'
            '<link href="http://externalfakehost.com/four.css" rel="stylesheet"/>\n'
            '<link href="http://externalfakehost.com/five.png" rel="apple-touch-icon"/>\n'
            '<link href="http://externalfakehost.com/six.ico" rel="icon"/>\n'
            '<link href="http://externalfakehost.com/seven.ico" rel="shortcut icon"/>\n'
            '<link href="http://externalfakehost.com/eight.txt" rel="dont care"/>\n'
            '<link href="http://externalfakehost.com/no_rel.txt"/>\n'
            '<link rel="icon"/>\n'
        )
        self.link_urls = [
            "http://validfakehost.com/test",
            "http://externalfakehost.com/one",
            "http://externalfakehost.com/two",
            "http://externalfakehost.com/three",
            "http://externalfakehost.com/four.css",
            "http://externalfakehost.com/five.png",
            "http://externalfakehost.com/six.ico",
            "http://externalfakehost.com/seven.ico",
        ]

    def test_parse_img(self):
        self.assertEqual(self.wpm._parse_html(self.img_html), self.img_urls)

    def test_parse_script(self):
        self.assertEqual(self.wpm._parse_html(self.script_html), self.script_urls)

    def test_parse_links(self):
        self.assertEqual(self.wpm._parse_html(self.link_html), self.link_urls)


class WebpageAssetDownloadTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.wpm = WebpageMeasurement("test", "http://validfakehost.com/test")
        self.all_url_types = [
            "https://validfakehost.com/an_image.jpg",
            "/resources/client/a_stylesheet.css",
            "//res.validfakehost.com/fonts/a_font.woff2",
        ]
        self.all_success_urls_transformed = [
            call(
                "https://validfakehost.com/an_image.jpg",
                timeout=self.wpm.download_timeout,
            ),
            call(
                "https://validfakehost.com/resources/client/a_stylesheet.css",
                timeout=self.wpm.download_timeout,
            ),
            call(
                "https://res.validfakehost.com/fonts/a_font.woff2",
                timeout=self.wpm.download_timeout,
            ),
        ]
        self.all_success_dict = {
            "asset_download_size": 3,
            "failed_asset_downloads": 0,
            "completion_time": 1.23,
        }
        self.one_failure_dict = {
            "asset_download_size": 2,
            "failed_asset_downloads": 1,
            "completion_time": 1.23,
        }
        self.all_failure_dict = {
            "asset_download_size": 0,
            "failed_asset_downloads": 3,
            "completion_time": 1.23,
        }

    @mock.patch("time.time")
    def test_all_success_dict(self, mock_time):
        mock_time.return_value = 1.23
        mock_session = mock.MagicMock()
        responses = []
        for i in range(3):
            response = mock.MagicMock()
            response.text = str("i")
            response.status_code = 200
            responses.append(response)
        mock_session.get.side_effect = responses
        self.assertEqual(
            self.wpm._download_assets(
                mock_session, self.all_url_types, "validfakehost.com", "https"
            ),
            self.all_success_dict,
        )

    def test_all_success_urls(self):
        mock_session = mock.MagicMock()
        responses = []
        for i in range(3):
            response = mock.MagicMock()
            response.text = str("i")
            response.status_code = 200
            responses.append(response)
        mock_session.get.side_effect = responses
        self.wpm._download_assets(
            mock_session, self.all_url_types, "validfakehost.com", "https"
        )
        mock_session.get.assert_has_calls(self.all_success_urls_transformed)

    @mock.patch("time.time")
    def test_single_failure_code(self, mock_time):
        mock_time.return_value = 1.23
        mock_session = mock.MagicMock()
        responses = []
        for i in range(2):
            response = mock.MagicMock()
            response.text = str("i")
            response.status_code = 200
            responses.append(response)
        fail_response = mock.MagicMock()
        fail_response.text = "0"
        fail_response.status_code = 404
        responses.append(fail_response)
        mock_session.get.side_effect = responses
        self.assertEqual(
            self.wpm._download_assets(
                mock_session, self.all_url_types, "validfakehost.com", "https"
            ),
            self.one_failure_dict,
        )

    @mock.patch("time.time")
    def test_single_failure_error(self, mock_time):
        mock_time.return_value = 1.23
        mock_session = mock.MagicMock()
        responses = []
        for i in range(2):
            response = mock.MagicMock()
            response.text = str("i")
            response.status_code = 200
            responses.append(response)
        responses.append(ConnectionError)
        mock_session.get.side_effect = responses
        self.assertEqual(
            self.wpm._download_assets(
                mock_session, self.all_url_types, "validfakehost.com", "https"
            ),
            self.one_failure_dict,
        )

    @mock.patch("time.time")
    def test_all_failure(self, mock_time):
        mock_time.return_value = 1.23
        mock_session = mock.MagicMock()
        responses = []
        for i in range(2):
            response = mock.MagicMock()
            response.text = str("i")
            response.status_code = 404
            responses.append(response)
        responses.append(ConnectionError)
        mock_session.get.side_effect = responses
        self.assertEqual(
            self.wpm._download_assets(
                mock_session, self.all_url_types, "validfakehost.com", "https"
            ),
            self.all_failure_dict,
        )
