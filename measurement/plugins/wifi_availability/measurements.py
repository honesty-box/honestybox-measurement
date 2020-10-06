import re
import subprocess
import sys

import psutil
from measurement.measurements import BaseMeasurement
from measurement.results import Error
from measurement.units import NetworkUnit
import six

from measurement.plugins.wifi_availability.results import (
    AccessPointMeasurementResult,
    ConnectedAccessPointMeasurementResult,
)
from measurement.plugins.wifi_availability.units import (
    SignalFrequencyUnit,
    SignalPowerUnit,
)


IWCONFIG_REGEXES = {
    "essid": re.compile(r"ESSID:\"(?P<essid>.*)\""),
    "bssid": re.compile(r"Access Point: (?P<bssid>\S*)"),
    "frequency": re.compile(r"Frequency:(?P<frequency>\d*.\d*)"),
    "frequency_unit": re.compile(r"Frequency:\d*.\d* (?P<frequency_unit>\w*)"),
    "bitrate": re.compile(r"Bit Rate=(?P<bitrate>\d*.\d*)"),
    "bitrate_unit": re.compile(r"Bit Rate=\d*.\d* (?P<bitrate_unit>\w*\/\w*)"),
    "tx_power": re.compile(r"Tx-Power=(?P<tx_power>\d*\.*\d*)"),
    "tx_power_unit": re.compile(r"Tx-Power=\d*\.*\d* (?P<tx_power_unit>\w*)"),
    "link_quality": re.compile(r"Link Quality=(?P<link_quality>\d*\/\d*)"),
    "signal_level": re.compile(r"Signal level=(?P<signal_level>-?\d*)"),
    "signal_level_unit": re.compile(r"Signal level=-?\d* (?P<signal_level_unit>\w*)"),
}
SCAN_REGEXES = {
    "channel": re.compile(r"Channel:(?P<channel>\d*)"),
    "frequency": re.compile(
        r"Frequency:(?P<frequency>\d*\.\d*) (?P<frequency_unit>\w*)"
    ),
    "frequency_unit": re.compile(r"Frequency:\d*\.\d* (?P<frequency_unit>\w*)"),
    "quality": re.compile(r"Quality=(?P<quality>\d*\/\d*)"),
    "signal_level": re.compile(
        r"Signal level=(?P<signal_level>-?\d*) (?P<signal_level_unit>\w*)"
    ),
    "signal_level_unit": re.compile(r"Signal level=-?\d* (?P<signal_level_unit>\w*)"),
    "essid": re.compile(r'ESSID:"(?P<essid>.*)"'),
    "bssid": re.compile(r"Address: (?P<bssid>\S*)"),
    "standard": re.compile(r"(?P<standard>IEEE .*)"),
    "bitrates": re.compile(r"(?P<bitrates>Bit Rates:.*(?:\n.*)*)Mode"),
    "last_beacon": re.compile(r"Last beacon: (?P<last_beacon>\d*)"),
}
IWCONFIG_ERRORS = {
    "iwconfig-err": "iwconfig had an unknown error.",
    "iwconfig-none": "No valid metrics could be parsed from the iwconfig output",
    "iwconfig-regex": "Attempted to get the known regex format and failed.",
    "iwconfig-timeout": "Measurement request timed out.",
    "iwconfig-essid": "Could not process the essid regex.",
    "iwconfig-bssid": "Could not process the bssid regex.",
    "iwconfig-frequency": "Could not process the frequency regex.",
    "iwconfig-frequency_unit": "Could not process the frequency unit regex.",
    "iwconfig-tx_power": "Could not process the tx_power regex.",
    "iwconfig-tx_power_unit": "Could not process the tx_power unit regex.",
    "iwconfig-link_quality": "Could not process the link_quality regex.",
    "iwconfig-signal_level": "Could not process the signal_level regex.",
    "iwconfig-signal_level_unit": "Could not process the signal_level unit regex.",
    "iwconfig-err-err": "Encountered an error when fetching the error.",
}
SCAN_ERRORS = {
    "scan-err": "scan had an unknown error.",
    "scan-none": "No interfaces were able to find access points",
    "scan-split": "Attempted to split the result but it was in an unknown format.",
    "scan-regex": "Attempted to get the known regex format and failed.",
    "scan-timeout": "Measurement request timed out.",
    "scan-channel": "Could not process the channel regex.",
    "scan-frequency": "Could not process the frequency regex.",
    "scan-frequency_unit": "Could not process the frequency unit regex.",
    "scan-quality": "Could not process the quality regex.",
    "scan-signal_level": "Could not process the signal level regex.",
    "scan-signal_level_unit": "Could not process the signal level unit regex.",
    "scan-essid": "Could not process the essid regex",
    "scan-bssid": "Could not process the bssid regex",
    "scan-standard": "Could not process the standard regex.",
    "scan-bitrates": "Could not process the bitrates regex.",
    "scan-err-err": "Encountered an error when fetching the error.",
}


class AccessPointMeasurement(BaseMeasurement):
    def __init__(self, id: str, check_connected: bool = True):
        self.id = id
        self.check_connected = check_connected

    def _get_interfaces(self):
        addrs = psutil.net_if_addrs()
        return addrs.keys()

    def measure(self):
        results = self._get_scan_results()
        if self.check_connected is True:
            results += [self._get_iwconfig_result()]
        return results

    def _get_iwconfig_result(self):
        try:
            # Note that iwconfig will always write to stderr if there is an interface that cannot scan.
            iwconfig_out = subprocess.run(
                ["iwconfig"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                universal_newlines=True,
            )
        except subprocess.TimeoutExpired:
            return self._get_iwconfig_error("iwconfig-timeout", traceback=None)
        try:
            metrics = {}
            for metric, regex in IWCONFIG_REGEXES.items():
                match = regex.search(iwconfig_out.stdout)
                if match is not None:
                    metrics[metric] = self._parse_connected_access_point_metric(
                        metric, match.groupdict()[metric]
                    )
                else:
                    metrics[metric] = None
        except (KeyError, ValueError) as err_type:
            return self._get_iwconfig_error(
                "iwconfig-{err_type}".format(err_type=err_type),
                traceback=iwconfig_out.stdout,
            )
        if not any(metrics.values()):
            return self._get_iwconfig_error(
                "iwconfig-none", traceback=iwconfig_out.stdout
            )
        try:
            return ConnectedAccessPointMeasurementResult(
                id=self.id,
                essid=metrics["essid"],
                bssid=metrics["bssid"],
                frequency=metrics["frequency"],
                frequency_unit=metrics["frequency_unit"],
                bitrate=metrics["bitrate"],
                bitrate_unit=metrics["bitrate_unit"],
                tx_power=metrics["tx_power"],
                tx_power_unit=metrics["tx_power_unit"],
                link_quality=metrics["link_quality"],
                signal_level=metrics["signal_level"],
                signal_level_unit=metrics["signal_level_unit"],
                errors=[],
            )
        except KeyError:
            return self._get_iwconfig_error("iwconfig-regex", traceback=iwconfig_out)

    def _get_scan_results(self):
        results = []
        # List of errors (if any) for each interface that occurr during the iwlist command
        iwlist_errors = []
        for interface in self._get_interfaces():
            try:
                interface_out = subprocess.run(
                    ["iwlist", interface, "scan"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    universal_newlines=True,
                )
            except subprocess.TimeoutExpired:
                return [self._get_scan_error("scan-timeout", traceback=None)]
            if interface_out.stderr != "":
                iwlist_errors.append(
                    self._get_scan_error("scan-err", traceback=interface_out.stderr)
                )
                continue

            try:
                interface_data = interface_out.stdout.split("Cell")
            except KeyError:
                results.append(
                    self._get_scan_error("scan-split", traceback=interface_out)
                )

            # Check if the split produced a valid output.
            if len(interface_data) < 2:
                iwlist_errors.append(
                    self._get_scan_error("scan-err", traceback=interface_out.stderr)
                )
                continue
            for cell in interface_data[1:]:
                results.append(self._get_cell_result(cell))

        # If all interfaces failed to produce a valid result, return all the errors
        if len(results) == 0:
            return iwlist_errors
        return results

    def _get_cell_result(self, cell):
        try:
            metrics = {}
            for metric, regex in SCAN_REGEXES.items():
                match = SCAN_REGEXES[metric].search(cell)
                if match is not None:
                    metrics[metric] = self._parse_access_point_metric(
                        metric, match.groupdict()[metric]
                    )
                else:
                    metrics[metric] = None
        except (KeyError, ValueError) as err_type:
            return self._get_scan_error(
                "scan-{err_type}".format(err_type=err_type), traceback=cell
            )
        # If no metrics could be resolved, consider the cell an error.
        if not any(metrics.values()):
            return self._get_scan_error("scan-regex", traceback=cell)
        try:
            return AccessPointMeasurementResult(
                id=self.id,
                channel=metrics["channel"],
                frequency=metrics["frequency"],
                frequency_unit=metrics["frequency_unit"],
                quality=metrics["quality"],
                signal_level=metrics["signal_level"],
                signal_level_unit=metrics["signal_level_unit"],
                essid=metrics["essid"],
                bssid=metrics["bssid"],
                standard=metrics["standard"],
                bitrates=metrics["bitrates"],
                last_beacon=metrics["last_beacon"],
                errors=[],
            )
        except KeyError:
            return self._get_scan_error("scan-regex", traceback=cell)

    def _parse_connected_access_point_metric(self, metric, match):
        if match == "":
            return None
        if metric == "bitrate_unit":
            match = match.replace("Mb/s", "Mbit/s")
        try:
            if (
                six.PY3 and not sys.version_info.minor == 5
            ):  # All python 3 expect for 3.5
                # Introspect dataclass to determine correct type for this metric.
                unit = ConnectedAccessPointMeasurementResult.__dataclass_fields__[
                    metric
                ].type.__args__[0]
                return unit(match)
            else:
                print("got here:" + match)
                # Without access to dataclasses we must cast metric values to types explicitly.
                if metric in ["essid", "bssid", "link_quality"]:
                    return str(match)
                if metric in ["frequency_unit"]:
                    return SignalFrequencyUnit(match)
                if metric in ["bitrate_unit"]:
                    return NetworkUnit(match)
                if metric in ["tx_power_unit", "signal_level_unit"]:
                    return SignalPowerUnit(match)
                if metric in ["frequency", "bitrate", "tx_power", "signal_level"]:
                    return float(match)
                # Metric is not a ConnectedAccessPointMeasurementResult metric.
                raise ValueError(metric)
        except (KeyError, TypeError, ValueError):
            raise ValueError(metric)

    def _parse_access_point_metric(self, metric, match):
        if match == "":
            return None
        if metric == "bitrates":
            match = (
                match.replace("\n", ";")
                .replace("Bit Rates:", "")
                .replace(" ", "")
                .replace("Mb/s", "Mbit/s")
                .split(";")[:-1]
            )
        try:
            if (
                six.PY3 and not sys.version_info.minor == 5
            ):  # All python 3 expect for 3.5
                # Introspect dataclass to determine correct type for this metric.
                unit = AccessPointMeasurementResult.__dataclass_fields__[
                    metric
                ].type.__args__[0]
                return unit(match)
            else:
                # Without access to dataclasses we must cast metric values to types explicitly.
                if metric in ["essid", "bssid", "quality", "standard"]:
                    return str(match)
                if metric in ["frequency_unit"]:
                    return SignalFrequencyUnit(match)
                if metric in ["signal_level_unit"]:
                    return SignalPowerUnit(match)
                if metric in ["frequency", "signal_level"]:
                    return float(match)
                if metric in ["channel", "last_beacon"]:
                    return int(match)
                if metric in ["bitrates"]:
                    return list(match)
                # Metric is not an AccessPointMeasurementResult metric.
                raise ValueError(metric)
        except (KeyError, TypeError, ValueError):
            raise ValueError(metric)

    def _get_iwconfig_error(self, key, traceback):
        try:
            return ConnectedAccessPointMeasurementResult(
                id=self.id,
                essid=None,
                bssid=None,
                frequency=None,
                frequency_unit=None,
                bitrate=None,
                bitrate_unit=None,
                tx_power=None,
                tx_power_unit=None,
                link_quality=None,
                signal_level=None,
                signal_level_unit=None,
                errors=[
                    Error(
                        key=key,
                        description=IWCONFIG_ERRORS.get(key, ""),
                        traceback=traceback,
                    )
                ],
            )
        except KeyError:
            return self._get_iwconfig_error("iwconfig-err-err", traceback=traceback)

    def _get_scan_error(self, key, traceback):
        try:
            return AccessPointMeasurementResult(
                id=self.id,
                channel=None,
                frequency=None,
                frequency_unit=None,
                quality=None,
                signal_level=None,
                signal_level_unit=None,
                essid=None,
                bssid=None,
                standard=None,
                bitrates=None,
                last_beacon=None,
                errors=[
                    Error(
                        key=key,
                        description=SCAN_ERRORS.get(key, ""),
                        traceback=traceback,
                    )
                ],
            )
        except KeyError:
            return self._get_scan_error("scan-err-err", traceback=traceback)
