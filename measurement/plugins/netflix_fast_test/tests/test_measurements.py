import subprocess
from unittest import TestCase, mock

from measurement.plugins.netflix_fast_test.measurements import (
    NetflixFastTestMeasurement, NETFLIX_ERRORS, CHUNK_SIZE, MIN_TIME, MAX_TIME,
    SLEEP_SECONDS, PING_COUNT, STABLE_MEASUREMENTS_LENGTH, STABLE_MEASUREMENTS_DELTA
)
from measurement.plugins.netflix_fast_test.results import (
    NetflixFastMeasurementResult, NetflixFastThreadResult
)
from measurement.results import Error
from measurement.units import RatioUnit, TimeUnit, StorageUnit, NetworkUnit

class NetflixFastResultTestCase(TestCase):

    def setUp(self) -> None:
        self.nft = NetflixFastTestMeasurement("1")
        super().setUp()

    @mock.patch(
        "measurement.plugins.netflix_fast_test.measurements.NetflixFastTestMeasurement._get_fast_result"
    )
    @mock.patch(
        "measurement.plugins.netflix_fast_test.measurements.NetflixFastTestMeasurement._get_url_result"
    )
    def test_measure(self, mock_get_url_result, mock_get_fast_result):
        mock_get_url_result.side_effect = ["A", "B", "C"]
        mock_get_fast_result.return_value = "fast"
        assert self.nft.measure() == ["fast", "A", "B", "C"]


