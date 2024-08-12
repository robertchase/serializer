"""tests for types"""

import pytest

from serializer import range_types


@pytest.mark.parametrize(
    "duration, result",
    (
        ("P1Y", (1, 0, 0, 0, 0, 0, 0)),
        ("P10W", (0, 0, 10, 70, 0, 0, 0)),
        ("P14D", (0, 0, 2, 14, 0, 0, 0)),
        ("P1Y2M3DT4H5M6S", (1, 2, 0, 3, 4, 5, 6)),
        ("PT1.5M", (0, 0, 0, 0, 0, 1.5, 0)),
        ("P1.5D", (0, 0, 0, 1.5, 0, 0, 0)),
    ),
)
def test_parse_iso_duration(duration, result):
    """Test ISO duration parsing."""
    dur = range_types.parse_iso_duration(duration)
    assert dur.years == result[0]
    assert dur.months == result[1]
    assert dur.weeks == result[2]
    assert dur.days == result[3]
    assert dur.hours == result[4]
    assert dur.minutes == result[5]
    assert dur.seconds == result[6]
