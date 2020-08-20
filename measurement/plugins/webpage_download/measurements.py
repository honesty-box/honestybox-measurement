import time
import requests

from measurement.measurements import BaseMeasurement
from measurement.results import Error
from measurement.units import RatioUnit, TimeUnit, StorageUnit, NetworkUnit

from measurement.plugins.webpage_download.results import WebpageMeasurementResult

BITS_PER_BYTE = 8
CHUNK_SIZE = 64 * 2 ** 10


class WebpageMeasurement(BaseMeasurement):
    def __init__(self, id, url):
        self.id = id
        self.url = url

    def measure(self):
        return self._get_webpage_result(self.url)

    def _get_webpage_result(self, url):
        s = requests.Session()
        start_time = time.time()
        connection = s.get(url)
        download_size = len(connection.content)
        elapsed_time = time.time() - start_time
        download_rate = download_size / elapsed_time * BITS_PER_BYTE

        return WebpageMeasurementResult(
            id=self.id,
            url=url,
            download_rate=download_rate,
            download_rate_unit=NetworkUnit("bit/s"),
            download_size=download_size,
            download_size_unit=StorageUnit("B"),
            elapsed_time=elapsed_time,
            elapsed_time_unit=TimeUnit("s"),
            errors=[],
        )
