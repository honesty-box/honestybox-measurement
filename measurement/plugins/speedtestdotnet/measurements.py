import re
import subprocess

import validators
from validators import ValidationFailure
import speedtest

from measurement.measurements import BaseMeasurement
from measurement.plugins.speedtestdotnet.results import (
    SpeedtestdotnetMeasurementResult
)
from measurement.results import Error
from measurement.units import RatioUnit, TimeUnit, StorageUnit, NetworkUnit

SPEEDTEST_ERRORS = {
    "speedtest-err": "wget had an unknown error.",
    "speedtest-config": "speedtest failed to retrieve a config",
    "speedtest-best-server": "speedtest could not find the best server",
    "speedtest-share": "speedtest could not share results"
}

class SpeedtestdotnetMeasurement(BaseMeasurement):
    def __init__(self, id, servers=None):
        super(SpeedtestdotnetMeasurement, self).__init__(id=id)
        self.id = id
        self.servers = servers
        
    def measure(self, share=False):
        """
        @params share: Boolean determining whether to generate a PNG on speedtest.net displaying the result of the test.
        """
        try:
            s = speedtest.Speedtest()
            # print(s)
            # print(s.results)
            # print(s.results.share())
            s.get_servers(self.servers)
            s.get_best_server()
            s.download()
            s.upload()
            if share:
                s.results.share()
            # print(s.results)
            results_dict = s.results.dict()
            import pprint
            print(pprint.pformat(results_dict))
            return SpeedtestdotnetMeasurementResult(
                id=self.id,
                download_rate=float(results_dict["download"]),
                download_rate_unit=NetworkUnit("bit/s"),
                upload_rate=float(results_dict["upload"]),
                upload_rate_unit=NetworkUnit("bit/s"),
                latency=float(results_dict["ping"]),
                server_name=results_dict["server"]["name"],
                server_id=results_dict["server"]["id"],
                server_sponsor=results_dict["server"]["sponsor"],
                server_host=results_dict["server"]["host"],
                errors=[]
            )
        except speedtest.ConfigRetrievalError as e:
            return self._get_speedtest_error("speedtest-config", traceback=str(e))
        except speedtest.SpeedtestBestServerFailure as e:
            return self._get_speedtest_error("speedtest-best-server", traceback=str(e))
        except speedtest.ShareResultsConnectFailure as e:
            return self._get_speedtest_error("speedtest-share", traceback=str(e))

    def _get_speedtest_error(self, key, traceback):
        return SpeedtestdotnetMeasurementResult(
            id=self.id,
            download_rate=None,
            download_rate_unit=None,
            upload_rate=None,
            upload_rate_unit=None,
            latency=None,
            server_name=None,
            server_id=None,
            server_sponsor=None,
            server_host=None,
            errors=[
                Error(
                    key=key, description=SPEEDTEST_ERRORS.get(key, ""), traceback=traceback
                )
            ],
        )
