"""
As of 2020/05/18 the fast.com uses 5s minimum, 30s maximum
"""

import requests
import re
import time
import urllib
import json
from threading import Thread
from collections import deque
from statistics import mean

from measurement.measurements import BaseMeasurement
from measurement.results import Error
from measurement.units import RatioUnit, TimeUnit, StorageUnit, NetworkUnit
from measurement.plugins.latency.measurements import LatencyMeasurement
from measurement.plugins.download_speed.measurements import DownloadSpeedMeasurement
from measurement.plugins.netflix_fast_test.results import (
    NetflixFastMeasurementResult,
    NetflixFastThreadResult,
)


NETFLIX_ERRORS = {
    "netflix-err": "Netflix test encountered an unknown error",
    "netflix-ping": "Netflix test encountered an error when pinging hosts",
    "netflix-response": "Netflix test received an invalid response from fast.com",
    "netflix-script-regex": "Netflix test failed to find script in the response",
    "netflix-script-response": "Netflix test received an invalid response from script",
    "netflix-token-regex": "Netflix test failed to find token in the response",
    "netflix-api-response": "Netflix test received an invalid response when querying for URLs",
    "netflix-api-json": "Netflix test failed to decode URLs",
    "netflix-api-parse": "Netflix test failed interpret elements of the decoded JSON",
    "netflix-connection": "Netflix test failed to connect to download URLs",
    "netflix-download": "Netflix test encountered an error downloading data",
}
# CHUNK_SIZE = 100 * 1024
CHUNK_SIZE = 64 * 2 ** 10
MIN_TIME = 3
MAX_TIME = 30
SLEEP_SECONDS = 0.2
PING_COUNT = 4
STABLE_MEASUREMENTS_LENGTH = 6
STABLE_MEASUREMENTS_DELTA = 2
# URLCOUNT = 3

total = 0
done = 0


class NetflixFastTestMeasurement(BaseMeasurement):
    def __init__(self, id, urlcount=3, terminate_on_thread_complete=True):
        super(NetflixFastTestMeasurement, self).__init__(id=id)
        self.id = id
        self.urlcount = urlcount
        self.terminate_on_thread_complete = terminate_on_thread_complete
        self.finished_threads = 0
        self.exit_threads = False
        self.total = 0
        self.sessions = []
        self.client_data = {"asn": None, "ip": None, "isp": None, "location": None}
        self.targets = []
        self.thread_results = [
            {
                "index": i,
                "elapsed_time": None,
                "download_size": 0,
                "download_rate": 0,
                "url": None,
                "location": None,
            }
            for i in range(self.urlcount)
        ]
        self.completed_total = 0
        self.completed_elapsed_time = None

    def measure(self):
        results = []
        results.append(self._get_fast_result())
        for thread_result in self.thread_results:
            results.append(self._get_url_result(thread_result))
        return results

    def _get_fast_result(self):
        s = requests.Session()
        try:
            resp = self._get_response(s)
        except ConnectionError as e:
            return self._get_netflix_error("netflix-response", traceback=str(e))

        try:
            script = re.search(r'<script src="(.*?)">', resp.text).group(1)
        except AttributeError:
            return self._get_netflix_error("netflix-script-regex", traceback=resp.text)

        try:
            script_resp = s.get("https://fast.com{script}".format(script=script))
        except ConnectionError as e:
            return self._get_netflix_error("netflix-script-response", traceback=str(e))

        try:
            token = re.search(r'token:"(.*?)"', script_resp.text).group(1)
        except AttributeError as e:
            return self._get_netflix_error(
                "netflix-token-regex", traceback=script_resp.text
            )

        try:
            self._query_api(s, token)
        except ConnectionError as e:
            return self._get_netflix_error("netflix-api-response", traceback=str(e))
        except json.decoder.JSONDecodeError as e:
            return self._get_netflix_error("netflix-api-json", traceback=str(e))
        except TypeError as e:
            return self._get_netflix_error("netflix-api-parse", traceback=str(e))
        except KeyError as e:
            return self._get_netflix_error("netflix-api-parse", traceback=str(e))

        try:
            conns = [
                self._get_connection(target["url"]) for target in self.thread_results
            ]
        except ConnectionError as e:
            return self._get_netflix_error("netflix-connection", traceback=str(e))

        fast_data = self._manage_threads(conns)

        return NetflixFastMeasurementResult(
            id=self.id,
            download_rate=float(fast_data["speed_mbps"]),
            download_rate_unit=NetworkUnit("Mbit/s"),
            download_size=float(fast_data["total"]),
            download_size_unit=StorageUnit("B"),
            asn=self.client_data["asn"],
            ip=self.client_data["ip"],
            isp=self.client_data["isp"],
            city=self.client_data["location"]["city"],
            country=self.client_data["location"]["country"],
            urlcount=self.urlcount,
            reason_terminated=fast_data["reason_terminated"],
            errors=[],
        )

    def _manage_threads(self, conns):
        # Create worker threads
        threads = [None] * len(self.thread_results)
        for i in range(len(self.thread_results)):
            threads[i] = Thread(
                target=self._threaded_download,
                args=(conns[i], self.thread_results[i], time.time()),
            )
            threads[i].daemon = True
            threads[i].start()

        start_time = time.time()
        recent_measurements = deque(maxlen=STABLE_MEASUREMENTS_LENGTH)
        percent_deltas = deque(maxlen=STABLE_MEASUREMENTS_LENGTH)
        while True:
            elapsed_time = time.time() - start_time
            total = 0
            for thread_result in self.thread_results:
                total += thread_result["download_size"]
            speed_kBps = total / elapsed_time / 1024
            recent_measurements.append(speed_kBps)

            if len(recent_measurements) == 10:
                # Calculate percentage difference to the average of the last ten measurements
                percent_deltas.append(
                    (speed_kBps - mean(recent_measurements)) / speed_kBps * 100
                )

            if self._is_test_complete(elapsed_time, percent_deltas):
                reason_terminated = self._is_test_complete(elapsed_time, percent_deltas)
                self.exit_threads = True
                for thread in threads:
                    thread.join()

                if (self.completed_elapsed_time is not None) & (
                    reason_terminated == "thread_complete"
                ):
                    # Record the speed at the time the thread finished downloading
                    speed_mbps = (
                        self.completed_total
                        / self.completed_elapsed_time
                        / 1024
                        / 1024
                        * 8
                    )
                else:
                    elapsed_time = time.time() - start_time
                    speed_mbps = total / elapsed_time / 1024 / 1024 * 8

                return {
                    "speed_mbps": speed_mbps,
                    "total": total,
                    "reason_terminated": reason_terminated,
                }
            time.sleep(SLEEP_SECONDS)

    def _threaded_download(self, conn, thread_result, start_time):
        # Iterate through the URL content
        g = conn.iter_content(chunk_size=CHUNK_SIZE)
        for chunk in g:
            if self.exit_threads:
                break
            thread_result["download_size"] += len(chunk)

        completed_time = time.time()
        elapsed_time = completed_time - start_time

        # If this is the first thread to complete, record the time and total at this point
        if self.completed_elapsed_time == None:
            self.completed_elapsed_time = elapsed_time
            for global_thread_result in self.thread_results:
                self.completed_total += global_thread_result["download_size"]

        thread_result["download_rate"] = (
            thread_result["download_size"] / elapsed_time / 1024 / 1024 * 8
        )
        thread_result["elapsed_time"] = elapsed_time
        self.finished_threads += 1

    def _query_api(self, s, token):
        params = {"https": "true", "token": token, "urlCount": self.urlcount}
        # '/v2/' path returns all location data about the servers
        api_resp = s.get("https://api.fast.com/netflix/speedtest/v2", params=params)
        api_json = api_resp.json()
        for i in range(len(api_json["targets"])):
            self.thread_results[i]["url"] = api_json["targets"][i]["url"]
            self.thread_results[i]["location"] = api_json["targets"][i]["location"]
        self.client_data = api_json["client"]
        return

    def _is_stabilised(self, percent_deltas, elapsed_time):
        return (
            elapsed_time > MIN_TIME
            and len(percent_deltas) >= STABLE_MEASUREMENTS_LENGTH
            and max(percent_deltas) < STABLE_MEASUREMENTS_DELTA
        )

    def _get_response(self, s):
        return s.get("http://fast.com/")

    def _get_connection(self, url):
        s = requests.Session()
        self.sessions.append(s)
        conn = s.get(url, stream=True)
        return conn

    def _is_test_complete(self, elapsed_time, percent_deltas):
        if elapsed_time > MAX_TIME:
            return "time_expired"
        if self._is_stabilised(percent_deltas, elapsed_time):
            return "result_stabilised"
        if self.finished_threads == len(self.thread_results):
            return "all_complete"
        if (self.finished_threads >= 1) & (self.terminate_on_thread_complete):
            return "thread_complete"
        return False

    def _get_url_result(self, thread_result):
        host = urllib.parse.urlparse(thread_result["url"]).netloc
        city = thread_result["location"]["city"]
        country = thread_result["location"]["country"]
        LatencyResult = LatencyMeasurement(self.id, host, count=PING_COUNT).measure()[0]

        return NetflixFastThreadResult(
            id=self.id,
            host=host,
            city=city,
            country=country,
            download_size=thread_result["download_size"],
            download_size_unit=StorageUnit("B"),
            download_rate=thread_result["download_rate"],
            download_rate_unit=NetworkUnit("Mbit/s"),
            minimum_latency=LatencyResult.minimum_latency,
            average_latency=LatencyResult.average_latency,
            maximum_latency=LatencyResult.maximum_latency,
            median_deviation=LatencyResult.median_deviation,
            packets_transmitted=LatencyResult.packets_transmitted,
            packets_received=LatencyResult.packets_received,
            packets_lost=LatencyResult.packets_lost,
            packets_lost_unit=LatencyResult.packets_lost_unit,
            time=LatencyResult.time,
            time_unit=LatencyResult.time_unit,
            errors=LatencyResult.errors,
        )

    def _get_netflix_error(self, key, traceback):
        return NetflixFastMeasurementResult(
            id=self.id,
            download_rate=None,
            download_rate_unit=None,
            download_size=None,
            download_size_unit=None,
            asn=None,
            ip=None,
            isp=None,
            city=None,
            country=None,
            urlcount=self.urlcount,
            reason_terminated=None,
            errors=[
                Error(
                    key=key,
                    description=NETFLIX_ERRORS.get(key, ""),
                    traceback=traceback,
                )
            ],
        )
