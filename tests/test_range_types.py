"""tests for types"""

import datetime

import pytest

from serializer import range_types


UTC = datetime.timezone.utc


@pytest.mark.parametrize(
    "lower, upper, l_exclusive, u_exclusive, value, is_contained",
    (
        (1, 10, False, False, 1, True),
        (1, 10, True, False, 1, False),
        (1, 10, False, False, 10, True),
        (1, 10, False, True, 10, False),
    ),
)
def test_contains(lower, upper, l_exclusive, u_exclusive, value, is_contained):
    test = range_types.Range(lower, upper, l_exclusive, u_exclusive)
    if is_contained:
        assert test.contains(value)
    else:
        assert not test.contains(value)


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
        ("P10W", (0, 0, 10, 0, 0, 0, 0)),
        ("P14D", (0, 0, 0, 14, 0, 0, 0)),
        ("P1Y2M3DT4H5M6S", (1, 2, 0, 3, 4, 5, 6)),
        ("P1M", (0, 1, 0, 0, 0, 0, 0)),
        ("PT1M", (0, 0, 0, 0, 0, 1, 0)),
        ("PT1.5S", (0, 0, 0, 0, 0, 0, 1.5)),
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


def test_empty_date_range():
    """Test empty date range."""
    test = range_types.ISODateRange("/")
    assert test.lower_bound == test.upper_bound


def test_empty_datetime_range():
    """Test empty datetime range."""
    test = range_types.ISODateTimeRange("/")
    assert test.lower_bound == test.upper_bound


def test_double_duration_date():
    """Test range composed of two date durations."""
    test = range_types.ISODateRange("P1D/P1D")
    assert (test.upper_bound - test.lower_bound) == datetime.timedelta(days=2)


def test_double_duration_datetime():
    """Test range composed of two datetime durations."""
    test = range_types.ISODateTimeRange("PT1H/PT1H")
    assert (test.upper_bound - test.lower_bound) == datetime.timedelta(hours=2)
