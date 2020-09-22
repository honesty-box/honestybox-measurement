import time
import subprocess
import re
import os
import tempfile
import shutil
import requests
from six.moves.urllib.parse import urlparse
from bs4 import BeautifulSoup

from measurement.measurements import BaseMeasurement
from measurement.results import Error
from measurement.units import RatioUnit, TimeUnit, StorageUnit, NetworkUnit
import pywebcopy

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
WEB_ERRORS = {
    "web-get": "Failed to complete the initial connection",
    "web-parse": "Failed to parse assets from HTML",
    "web-parse-rel": "Failed to determine 'rel' attribute of link",
    "web-assets": "Failed to download secondary assets",
    "web-timeout": "Initial page download timed out",
}
WGET_DOWNLOAD_RATE_UNIT_MAP = {
    "Kb/s": NetworkUnit("Kibit/s"),
    "Mb/s": NetworkUnit("Mibit/s"),
}
WGET_DOWNLOAD_SIZE_UNIT_MAP = {"K": StorageUnit("KiB"), "M": StorageUnit("MiB")}
WGET_TIME_UNIT_MAP = {"s": TimeUnit("s")}
VALID_LINK_EXTENSTIONS = [".css", ".ico", ".png", ".woff2", ""]
VALID_LINK_REL_ATTRIBUTES = [
    "manifest",
    "modulepreload",
    "preload",
    "prerender",
    "stylesheet",
    "apple-touch-icon",
    "icon",
    "shortcut icon",
]


class WebpageMeasurement(BaseMeasurement):
    def __init__(self, id, url, count=4, download_timeout=180):
        self.id = id
        self.url = url
        self.count = count
        self.download_timeout = download_timeout

    def measure(self):
        host = urlparse(self.url).netloc
        return [
            self._get_webpage_result(self.url, host),
            LatencyMeasurement(self.id, host, count=self.count).measure(),
        ]

    # def _get_webpage_result_wget(self, url, host, download_timeout):
    #     tmp_dir = "{}/webpage_download_{}".format(tempfile.gettempdir(), os.getpid())
    #     try:
    #         wget_out = subprocess.run(
    #             [
    #                 "wget",
    #                 "--tries=2",
    #                 "--no-check-certificate",
    #                 "-P",
    #                 tmp_dir,
    #                 "-U",
    #                 "Mozilla",
    #                 "-e",
    #                 "robots=off",
    #                 "-H",
    #                 "-p",
    #                 "-k",
    #                 "--report-speed=bits",
    #                 url,
    #             ],
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.PIPE,
    #             timeout=download_timeout,
    #             universal_newlines=True,
    #         )
    #     except subprocess.TimeoutExpired:
    #         return self._get_webpage_error("wget-timeout", traceback=None)
    #
    #     if wget_out.returncode != 0:
    #         return self._get_webpage_error("wget-err", traceback=str(wget_out.stderr))
    #     try:
    #         wget_data = wget_out.stderr
    #         import pprint
    #
    #         pprint.pprint(wget_data)
    #     except IndexError:
    #         return self._get_webpage_error("wget-split", traceback=str(wget_out.stderr))
    #     matches = WGET_OUTPUT_REGEX.search(wget_data)
    #
    #     try:
    #         match_data = matches.groupdict()
    #     except AttributeError:
    #         return self._get_webpage_error("wget-regex", traceback=str(wget_out.stderr))
    #
    #     if len(match_data.keys()) != 7:
    #         return self._get_webpage_error("wget-regex", traceback=str(wget_out.stderr))
    #
    #     try:
    #         metric_dict = self._parse_wget_regex(match_data)
    #     except (TypeError, ValueError):
    #         return self._get_webpage_error("wget-regex-metric", traceback=(match_data))
    #     except KeyError:
    #         return self._get_webpage_error("wget-regex-unit", traceback=(match_data))
    #
    #     try:
    #         # Remove the created temp directory and all contents
    #         shutil.rmtree(tmp_dir)
    #     except FileNotFoundError as e:
    #         return self._get_webpage_error("wget-no_directory", traceback=str(e))
    #
    #     return WebpageMeasurementResult(
    #         id=self.id,
    #         url=url,
    #         download_rate=metric_dict["download_rate"],
    #         download_rate_unit=metric_dict["download_rate_unit"],
    #         download_size=metric_dict["download_size"],
    #         download_size_unit=metric_dict["download_size_unit"],
    #         downloaded_file_count=metric_dict["downloaded_file_count"],
    #         elapsed_time=metric_dict["elapsed_time"],
    #         elapsed_time_unit=metric_dict["elapsed_time_unit"],
    #         errors=[],
    #     )
    #
    # def _parse_wget_regex(self, match_data):
    #     download_rate = float(match_data.get("download_rate"))
    #     download_rate_unit = WGET_DOWNLOAD_RATE_UNIT_MAP[
    #         match_data.get("download_rate_unit")
    #     ]
    #     download_size = float(match_data.get("download_size"))
    #     download_size_unit = WGET_DOWNLOAD_SIZE_UNIT_MAP[
    #         match_data.get("download_size_unit")
    #     ]
    #     downloaded_file_count = int(match_data.get("file_count"))
    #     elapsed_time = float(match_data.get("elapsed_time"))
    #     elapsed_time_unit = WGET_TIME_UNIT_MAP[match_data.get("elapsed_time_unit")]
    #     return {
    #         "download_rate": download_rate,
    #         "download_rate_unit": download_rate_unit,
    #         "download_size": download_size,
    #         "download_size_unit": download_size_unit,
    #         "downloaded_file_count": downloaded_file_count,
    #         "elapsed_time": elapsed_time,
    #         "elapsed_time_unit": elapsed_time_unit,
    #     }

    def _get_webpage_result(self, url, host):
        s = requests.Session()
        headers = {
            "dnt": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        }

        start_time = time.time()
        try:
            r = s.get(url, headers=headers, timeout=self.download_timeout)
        except ConnectionError as e:
            return self._get_webpage_error("web-get", traceback=str(e))
        except requests.exceptions.ReadTimeout as e:
            return self._get_webpage_error("web-timeout", traceback=str(e))
        try:
            to_download = self._parse_html(r.text)
        except TypeError as e:
            return self._get_webpage_error("web-parse-rel", traceback=str(e))
        try:
            asset_download_metrics = self._download_assets(s, to_download, host)
        except TypeError as e:
            return self._get_webpage_error("web-assets", traceback=str(e))

        primary_download_size = len(r.text)
        asset_download_size = asset_download_metrics["asset_download_size"]
        elapsed_time = asset_download_metrics["completion_time"] - start_time
        download_rate = (primary_download_size + asset_download_size) * 8 / elapsed_time
        failed_asset_downloads = asset_download_metrics["failed_asset_downloads"]

        return WebpageMeasurementResult(
            id=self.id,
            url=url,
            download_rate=download_rate,
            download_rate_unit=NetworkUnit("bit/s"),
            download_size=primary_download_size + asset_download_size,
            download_size_unit=StorageUnit("B"),
            asset_count=len(to_download),
            failed_asset_downloads=failed_asset_downloads,
            elapsed_time=elapsed_time,
            elapsed_time_unit=TimeUnit("s"),
            errors=[],
        )

    def _parse_html(self, content):
        soup = BeautifulSoup(content, "html.parser")
        # hlinks = soup.find_all("a")
        imgs = soup.find_all("img")
        links = soup.find_all("link")
        scripts = soup.find_all("script")
        to_download = []
        for img in imgs:
            if img.has_attr("src"):
                to_download.append(img["src"])
        for script in scripts:
            if script.has_attr("src"):
                to_download.append(script["src"])
        for link in links:
            if link.has_attr("rel") & link.has_attr("href"):
                # Join in the case where `rel` is more than one word
                rel = " ".join(link["rel"])
                if rel in VALID_LINK_REL_ATTRIBUTES:
                    to_download.append(link["href"])

        return to_download

    def _download_assets(self, session, to_download, host):
        # Store the amount of bytes downloaded
        asset_download_sizes = []
        failed_asset_downloads = 0
        for asset in to_download:
            try:
                # Identify data URLs (already downloaded inline, counted in main download size)
                if "data:" in asset:
                    continue

                # Check if path w/o preceeding slashes is a valid URL
                if asset.startswith("//"):
                    download_url = "https:" + asset
                # Check if path is a relative path
                elif asset.startswith("/"):
                    download_url = "https://" + host + asset
                # ...or simply a normal file link
                else:
                    download_url = asset

                a = session.get(download_url, timeout=self.download_timeout)
                if a.status_code >= 400:
                    raise ConnectionError
                asset_download_sizes.append(len(a.text))
            except ConnectionError:
                failed_asset_downloads = failed_asset_downloads + 1
            except requests.exceptions.MissingSchema:
                failed_asset_downloads = failed_asset_downloads + 1
            except requests.exceptions.ReadTimeout:
                failed_asset_downloads = failed_asset_downloads + 1

        return {
            "asset_download_size": sum(asset_download_sizes),
            "failed_asset_downloads": failed_asset_downloads,
            "completion_time": time.time(),
        }

    def _get_webpage_error(self, key, traceback):
        return WebpageMeasurementResult(
            id=self.id,
            url=self.url,
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            asset_count=None,
            failed_asset_downloads=None,
            elapsed_time=None,
            elapsed_time_unit=None,
            errors=[
                Error(key=key, description=WEB_ERRORS.get(key, ""), traceback=traceback)
            ],
        )
