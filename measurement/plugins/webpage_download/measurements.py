import time
import subprocess
import re
import os
import tempfile
import shutil
from six.moves.urllib.parse import urlparse

from measurement.measurements import BaseMeasurement
from measurement.results import Error
from measurement.units import RatioUnit, TimeUnit, StorageUnit, NetworkUnit

from measurement.plugins.webpage_download.results import WebpageMeasurementResult
from measurement.plugins.latency.measurements import LatencyMeasurement

WGET_OUTPUT_REGEX = re.compile(
    r"\((?P<download_rate>[\d.]*)\s(?P<download_unit>.*)\).*\[(?P<download_size>\d*)[\]/]"
)
WGET_OUTPUT_REGEX = re.compile(
    r"Downloaded: (?P<file_count>[\d.]*) files, (?P<download_size>[\d.]*)(?P<download_size_unit>\S*) in (?P<elapsed_time>[\d.]*)(?P<elapsed_time_unit>\S*) \((?P<download_rate>[\d.]*)\s(?P<download_rate_unit>[\S]*)\)"
)
WGET_ERRORS = {
    "wget-err": "wget had an unknown error.",
    "wget-split": "wget attempted to split the result but it was in an unanticipated format.",
    "wget-regex": "wget attempted to get the known regex format and failed.",
    "wget-regex-metric": "wget could not parse a metric from the regex matches.",
    "wget-regex-unit": "wget could not parse a unit from the regex matches.",
    "wget-no-server": "No server could be resolved.",
    "wget-timeout": "Measurement request timed out.",
    "wget-no-directory": "Could not remove created temp directory.",
}
WGET_DOWNLOAD_RATE_UNIT_MAP = {
    "Kb/s": NetworkUnit("Kibit/s"),
    "Mb/s": NetworkUnit("Mibit/s"),
}
WGET_DOWNLOAD_SIZE_UNIT_MAP = {
    "K": StorageUnit("KiB"),
    "M": StorageUnit("MiB"),
}
WGET_TIME_UNIT_MAP = {
    "s": TimeUnit("s"),
}


class WebpageMeasurement(BaseMeasurement):
    def __init__(self, id, url, count=4, download_timeout=180):
        self.id = id
        self.url = url
        self.count = count
        self.download_timeout = download_timeout

    def measure(self):
        host = urlparse(self.url).netloc
        return [
            self._get_webpage_result(self.url, self.download_timeout),
            LatencyMeasurement(self.id, host, count=self.count).measure(),
        ]

    def _get_webpage_result(self, url, download_timeout):
        tmp_dir = "{}/webpage_download_{}".format(tempfile.gettempdir(), os.getpid())
        try:
            wget_out = subprocess.run(
                [
                    "wget",
                    "--tries=2",
                    "--no-check-certificate",
                    "-P",
                    tmp_dir,
                    "-U",
                    "Mozilla",
                    "-e",
                    "robots=off",
                    "-H",
                    "-p",
                    "-k",
                    "--report-speed=bits",
                    url,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=download_timeout,
                universal_newlines=True,
            )
        except subprocess.TimeoutExpired:
            return self._get_webpage_error("wget-timeout", traceback=None)

        if wget_out.returncode != 0:
            return self._get_webpage_error("wget-err", traceback=str(wget_out.stderr))
        try:
            wget_data = wget_out.stderr
        except IndexError:
            return self._get_webpage_error("wget-split", traceback=str(wget_out.stderr))
        matches = WGET_OUTPUT_REGEX.search(wget_data)

        try:
            match_data = matches.groupdict()
        except AttributeError:
            return self._get_webpage_error("wget-regex", traceback=str(wget_out.stderr))

        if len(match_data.keys()) != 7:
            return self._get_webpage_error("wget-regex", traceback=str(wget_out.stderr))

        try:
            metric_dict = self._parse_wget_regex(match_data)
        except (TypeError, ValueError):
            return self._get_webpage_error("wget-regex-metric", traceback=(match_data))
        except KeyError:
            return self._get_webpage_error("wget-regex-unit", traceback=(match_data))

        try:
            # Remove the created temp directory and all contents
            shutil.rmtree(tmp_dir)
        except FileNotFoundError as e:
            return self._get_webpage_error("wget-no_directory", traceback=str(e))

        return WebpageMeasurementResult(
            id=self.id,
            url=url,
            download_rate=metric_dict["download_rate"],
            download_rate_unit=metric_dict["download_rate_unit"],
            download_size=metric_dict["download_size"],
            download_size_unit=metric_dict["download_size_unit"],
            downloaded_file_count=metric_dict["downloaded_file_count"],
            elapsed_time=metric_dict["elapsed_time"],
            elapsed_time_unit=metric_dict["elapsed_time_unit"],
            errors=[],
        )

    def _parse_wget_regex(self, match_data):
        download_rate = float(match_data.get("download_rate"))
        download_rate_unit = WGET_DOWNLOAD_RATE_UNIT_MAP[
            match_data.get("download_rate_unit")
        ]
        download_size = float(match_data.get("download_size"))
        download_size_unit = WGET_DOWNLOAD_SIZE_UNIT_MAP[
            match_data.get("download_size_unit")
        ]
        downloaded_file_count = int(match_data.get("file_count"))
        elapsed_time = float(match_data.get("elapsed_time"))
        elapsed_time_unit = WGET_TIME_UNIT_MAP[match_data.get("elapsed_time_unit")]
        return {
            "download_rate": download_rate,
            "download_rate_unit": download_rate_unit,
            "download_size": download_size,
            "download_size_unit": download_size_unit,
            "downloaded_file_count": downloaded_file_count,
            "elapsed_time": elapsed_time,
            "elapsed_time_unit": elapsed_time_unit,
        }

    def _get_webpage_error(self, key, traceback):
        return WebpageMeasurementResult(
            id=self.id,
            url=self.url,
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            downloaded_file_count=None,
            elapsed_time=None,
            elapsed_time_unit=None,
            errors=[
                Error(
                    key=key, description=WGET_ERRORS.get(key, ""), traceback=traceback,
                )
            ],
        )
