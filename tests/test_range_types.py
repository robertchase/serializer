"""tests for types"""

import datetime

import pytest

from serializer import range_types


UTC = datetime.timezone.utc


@pytest.mark.parametrize(
    "value, lower, upper",
    (
        (
            "20240120T12--PT1H",
            datetime.datetime(2024, 1, 20, 12, tzinfo=UTC),
            datetime.datetime(2024, 1, 20, 13, tzinfo=UTC),
        ),
        (
            "PT1H/20240120T12",
            datetime.datetime(2024, 1, 20, 11, tzinfo=UTC),
            datetime.datetime(2024, 1, 20, 12, tzinfo=UTC),
        ),
        (
            "20231225T153233--20240120T12",
            datetime.datetime(2023, 12, 25, 15, 32, 33, tzinfo=UTC),
            datetime.datetime(2024, 1, 20, 12, tzinfo=UTC),
        ),
    ),
)
def test_parse_iso_datetime_range(value, lower, upper):
    test = range_types.ISODateTimeRange(value)
    assert test.lower_bound == lower
    assert test.upper_bound == upper


@pytest.mark.parametrize(
    "value, lower, upper",
    (
        ("20240120--P0YT1H", datetime.date(2024, 1, 20), datetime.date(2024, 1, 20)),
        ("P1YT1H/20240120", datetime.date(2023, 1, 20), datetime.date(2024, 1, 20)),
        ("20231225--20240120", datetime.date(2023, 12, 25), datetime.date(2024, 1, 20)),
    ),
)
def test_parse_iso_date_range(value, lower, upper):
    test = range_types.ISODateRange(value)
    assert test.lower_bound == lower
    assert test.upper_bound == upper


@pytest.mark.parametrize(
    "duration, result",
    (
        ("P0Y", (0, 0, 0, 0, 0, 0, 0)),
        ("P1Y", (1, 0, 0, 0, 0, 0, 0)),
        ("P10W", (0, 0, 10, 70, 0, 0, 0)),
        ("P14D", (0, 0, 2, 14, 0, 0, 0)),
        ("P1Y2M3DT4H5M6S", (1, 2, 0, 3, 4, 5, 6)),
        ("PT1.5M", (0, 0, 0, 0, 0, 1.5, 0)),
        ("P1.5D", (0, 0, 0, 1.5, 0, 0, 0)),
        ("P0Y", (0, 0, 0, 0, 0, 0, 0)),
        ("P", None),
        ("PY", None),
        ("P1.5Y", None),
        ("P1.5M", None),
        ("ABC", None),
    ),
)
def test_parse_iso_duration(duration, result):
    """Test ISO duration parsing."""
    dur = range_types.parse_iso_duration(duration)
    if dur is None:
        assert dur == result
    else:
        assert dur.years == result[0]
        assert dur.months == result[1]
        assert dur.weeks == result[2]
        assert dur.days == result[3]
        assert dur.hours == result[4]
        assert dur.minutes == result[5]
        assert dur.seconds == result[6]
