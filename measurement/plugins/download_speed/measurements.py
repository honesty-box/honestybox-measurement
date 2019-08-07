import re
import subprocess
import typing
from urllib.parse import urlparse

import validators
from validators import ValidationFailure

from measurement.measurements import BaseMeasurement
from measurement.plugins.download_speed.results import (
    DownloadSpeedMeasurementResult,
    LatencyMeasurementResult,
)
from measurement.results import Error
from measurement.units import NetworkUnit, StorageUnit

WGET_OUTPUT_REGEX = re.compile(
    r"\((?P<download_rate>[\d.]*)\s(?P<download_unit>.*)\).*\[(?P<download_size>\d*)\]"
)
LATENCY_OUTPUT_REGEX = re.compile(
    r"= (?P<minimum_latency>[\d.].*)/(?P<average_latency>[\d.].*)/(?P<maximum_latency>[\d.].*)/(?P<median_deviation>[\d.].*) "
)

WGET_ERRORS = {
    "wget-err": "wget had an unknown error.",
    "wget-split": "wget attempted to split the result but it was in an unanticipated format.",
    "wget-regex": "wget attempted get the known regex format and failed.",
    "wget-storage-unit": "wget could not process the storage unit.",
}


class DownloadSpeedMeasurement(BaseMeasurement):
    """A measurement designed to test download speed."""

    def __init__(self, id: str, url: str, count: int = 4) -> None:
        """Initialisation of a download speed measurement.

        :param id: A unique identifier for the measurement.
        :param url: A URL used to perform the download speed
        measurement.
        :param count: A positive integer describing the number of
        pings to perform. Defaults to 4.
        """
        super().__init__(id=id)

        validated_url = validators.url(url)

        if isinstance(validated_url, ValidationFailure):
            raise ValueError(f"`{url}` is not a valid url")

        if count < 0:
            raise ValueError(
                f"A value of {count} was provided for the number of pings. This must be a positive "
                f"integer or `0` to turn off the ping."
            )

        self.url = url
        self.count = count

    def measure(
        self
    ) -> typing.List[
        typing.Union[DownloadSpeedMeasurementResult, LatencyMeasurementResult]
    ]:
        """Perform the measurement."""
        results = [self._get_wget_results()]
        if self.count > 0:
            results.append(self._get_latency_results())
        return results

    def _get_latency_results(self) -> LatencyMeasurementResult:
        """Perform the latency measurement."""
        host = urlparse(self.url).netloc
        latency_out = subprocess.check_output(
            ["ping", "-c", f"{self.count}", host],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        latency_data = latency_out.split("\n")[-2]
        matches = LATENCY_OUTPUT_REGEX.search(latency_data)
        match_data = matches.groupdict()

        return LatencyMeasurementResult(
            id=self.id,
            host=host,
            maximum_latency=float(
                match_data.get("maximum_latency")
            ),  # TODO catch errors
            minimum_latency=float(
                match_data.get("minimum_latency")
            ),  # TODO catch errors
            average_latency=float(
                match_data.get("average_latency")
            ),  # TODO catch errors
            median_deviation=float(
                match_data.get("median_deviation")
            ),  # TODO catch errors
            errors=[],
        )

    def _get_wget_results(self) -> DownloadSpeedMeasurementResult:
        """Perform the download measurement."""
        wget_out = subprocess.run(
            f"wget --tries=2 -O /dev/null {self.url} 2>&1",
            shell=True,
            stdout=subprocess.PIPE,
        )

        if wget_out.stderr:
            return self._get_wget_error("wget-err", wget_out)

        try:
            wget_data = wget_out.stdout.decode("utf-8").split("\n")[-3]
        except KeyError:
            return self._get_wget_error("wget-split", wget_out)

        matches = WGET_OUTPUT_REGEX.search(wget_data)
        match_data = matches.groupdict()

        if len(match_data.keys()) != 3:
            return self._get_wget_error("wget-regex", wget_out)

        try:
            storage_unit = NetworkUnit(
                match_data.get("download_unit").replace("MB/s", "Mbit/s")
            )
        except ValueError:
            return self._get_wget_error("wget-storage-unit", wget_out)

        try:
            download_rate = float(match_data.get("download_rate"))
        except (TypeError, ValueError):
            return self._get_wget_error("wget-download-rate", wget_out)

        try:
            download_size = float(match_data.get("download_size"))
        except (TypeError, ValueError):
            return self._get_wget_error("wget-download-size", wget_out)

        return DownloadSpeedMeasurementResult(
            id=self.id,
            url=self.url,
            download_rate_unit=storage_unit,
            download_rate=download_rate,
            download_size=download_size,
            download_size_unit=StorageUnit.megabit,
            errors=[],
        )

    def _get_wget_error(self, key: str, traceback: str) -> DownloadSpeedMeasurementResult:
        return DownloadSpeedMeasurementResult(
            id=self.id,
            url=self.url,
            download_rate_unit=None,
            download_rate=None,
            download_size=None,
            download_size_unit=None,
            errors=[
                Error(
                    key=key,
                    description=WGET_ERRORS.get(key, ''),
                    traceback=traceback,
                )
            ],
        )