# -*- coding: utf-8 -*-
import six

from measurement.plugins.download_speed.measurements import WGET_OUTPUT_REGEX


def test_wget_output_regex_accepts_anticipated_format():
    anticipated_format = six.ensure_str(
        "2019-08-07 09:12:08 (16.7 MB/s) - '/dev/null’ saved [11376]"
    )
    results = WGET_OUTPUT_REGEX.search(anticipated_format).groupdict()
    assert results == {
        "download_rate": "16.7",
        "download_size": "11376",
        "download_unit": "MB/s",
    }
