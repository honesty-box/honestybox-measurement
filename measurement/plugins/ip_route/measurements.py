"""
ip_route measurement, formerly the Traceroute measurement.
"""
import subprocess

from scapy.all import traceroute

from measurement.measurements import BaseMeasurement
from measurement.plugins.ip_route.results import IPRouteMeasurementResult
from measurement.plugins.latency.measurements import LatencyMeasurement


class IPRouteMeasurement(BaseMeasurement):
    def __init__(self, id, hosts, route_timeout=10, count=4):
        super(IPRouteMeasurement, self).__init__(id=id)
        self.id = id
        self.hosts = hosts
        self.route_timeout = route_timeout
        self.count = count

    def measure(self):
        initial_latency_results = self._find_least_latent_host(self.hosts)
        least_latent_host = initial_latency_results[0][0]

        results = [self._get_traceroute_result(least_latent_host, self.route_timeout)]
        if self.count > 0:
            latency_measurement = LatencyMeasurement(
                self.id, least_latent_host, count=self.count
            )
            results.append(latency_measurement.measure()[0])

        results.extend([res for _, res in initial_latency_results])
        return results

    def _find_least_latent_host(self, hosts):
        """
        Performs a latency test for each specified host
        Returns a sorted list of LatencyResults, sorted by average latency
        """
        initial_latency_results = []
        for host in hosts:
            latency_measurement = LatencyMeasurement(self.id, host, count=2)
            initial_latency_results.append((host, latency_measurement.measure()[0]))
        return sorted(
            initial_latency_results,
            key=lambda x: (x[1].average_latency is None, x[1].average_latency),
        )

    def _get_traceroute_result(self, host, timeout):
        try:
            traceroute_out = traceroute(host)
            traceroute_trace = traceroute_out[0].get_trace()
            ip = list(traceroute_trace.keys())[0]
            hop_count = len(traceroute_trace[ip])
        except subprocess.TimeoutExpired:
            return None

        return IPRouteMeasurementResult(
            id=self.id,
            host=host,
            ip=ip,
            hop_count=hop_count,
            trace=traceroute_trace,
            errors=[],
        )

    def _get_ip_route_error(self, key, traceback):
        pass
