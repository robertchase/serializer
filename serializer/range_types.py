"""Serializable date and datetime ranges."""

from collections import namedtuple
import datetime
import re

import serializer
from serializer.types import ISODateTime, ISODate


class Range(serializer.Serializable):
    """A range bounded by two values (default: int).

    A range has a lower_bound and an upper_bound which can be compared with
    >, <, >=, <=.

    If is_upper_exclusive is True or is_lower_exclusive is True, comparisons
    on the respective bounds will exclude the bound itself; otherwise, the
    bound is part of the range.

    If upper_bound or lower_bound (not both) is missing, then it will not
    checked (the range is unbounded in that direction).
    """

    lower_bound: int = serializer.Optional
    upper_bound: int = serializer.Optional
    is_lower_exclusive: bool = False
    is_upper_exclusive: bool = False

    def _parse_string_arg(self, arg: str):  # override
        """Parse range elements as a comma separated string."""
        return arg.split(",")

    def _after_init(self):  # override
        lower = getattr(self, "lower_bound", None)
        upper = getattr(self, "upper_bound", None)
        if lower is None and upper is None:
            raise ValueError("lower_bound or upper_bound must be assigned")
        if lower is not None and upper is not None:
            if self.lower_bound > self.upper_bound:
                raise ValueError("lower_bound cannot be greater than upper_bound")

    def contains(self, value) -> bool:
        """Checks if value is within the range bounds."""
        if hasattr(self, "lower_bound"):
            if self.is_lower_exclusive:
                if value <= self.lower_bound:
                    return False
            elif value < self.lower_bound:
                return False
        if hasattr(self, "upper_bound"):
            if self.is_upper_exclusive:
                if value >= self.upper_bound:
                    return False
            elif value > self.upper_bound:
                return False
        return True


Duration = namedtuple("Duration", "years months weeks days hours minutes seconds")


class ISODateTimeRange(Range):
    """A range bounded by two datetime.datetime values.

    When constructed with a single string arg, the value can be: two
    ISO-formated datetimes, an ISO range (see ISO 8601) followed by an ISO
    datetime, or an ISO datetime followed by an ISO range. The two values are
    separated by a "/" or a "--".

    Example string values for 12-1pm on Jan 1st 2024 UTC:

        2024-01-01T12:00:00Z/24-01-01T13:00:00Z
        PT1H/24-01-01T13:00:00Z
        24-01-01T12:00:00Z--PT60M

    A single string arg with two separated ISO range values can also be
    supplied, which will indicate durations before and after the current time.

    The following indicates a range of one hour before the current time and
    fifteen minutes after the current time:

        PT1H/PT15M

    If a single string arg is missing one or both separated values, then the
    current time is assumed for the missing value(s).

    The following indicates the ten previous hours (a range from 10 hours ago
    until now):

        PT10H/

    If timezone information is not provided, then "Z" will be used.
    """

    lower_bound: ISODateTime = serializer.Optional
    upper_bound: ISODateTime = serializer.Optional

    def _parse_string_arg(self, arg):
        """Parse range elements as an ISO range."""
        return parse_iso_range(arg, self.date_parser, self.duration_parser)

    def date_parser(self, value: str) -> datetime.datetime:
        """Parse datetime."""
        try:
            parsed = datetime.datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                parsed = datetime.datetime.fromisoformat(value + "Z")
            return parsed
        except ValueError:
            raise ValueError("invalid datetime value") from None

    def duration_parser(self, value: str) -> Duration:
        """Parse duration value."""
        return parse_iso_duration(value)


class ISODateRange(ISODateTimeRange):
    """A range bounded by two dates."""

    lower_bound: ISODate = serializer.Optional
    upper_bound: ISODate = serializer.Optional

    def date_parser(self, value: str) -> datetime.date:
        """Parse datetime.date."""
        try:
            return datetime.datetime.fromisoformat(value).date()
        except ValueError:
            pass
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            raise ValueError("invalid date value") from None

    def duration_parser(self, value: str) -> Duration:
        """Remove time portion from duration value before parsing."""
        return parse_iso_duration(value.split("T")[0])


def parse_iso_range(value: str, date_parser, duration_parser):
    """Parse a daterange into a pair (list) of datetime or date values."""

    if len(parts := re.split(r"/|--", value)) == 1:
        raise ValueError("range separator not found")

    part1, part2 = parts
    now = datetime.datetime.now().isoformat()
    if not part1:
        part1 = now
    if not part2:
        part2 = now

    if part1[0] == part2[0] == "P":
        middle = date_parser(now)
        if (duration := duration_parser(part1)) is None:
            raise ValueError("invalid duration value")
        start_date = sub_duration(middle, duration)
        if (duration := duration_parser(part2)) is None:
            raise ValueError("invalid duration value")
        end_date = add_duration(middle, duration)
    elif part1[0] == "P":
        end_date = date_parser(part2)
        if (duration := duration_parser(part1)) is None:
            raise ValueError("invalid duration value")
        start_date = sub_duration(end_date, duration)
    elif part2[0] == "P":
        start_date = date_parser(part1)
        if (duration := duration_parser(part2)) is None:
            raise ValueError("invalid duration value")
        end_date = add_duration(start_date, duration)
    else:
        start_date = date_parser(part1)
        end_date = date_parser(part2)

    return [start_date, end_date]


_valid_iso_duration = re.compile(
    r"P(?:(\d+)Y)?"
    r"(?:(\d+)M)?"
    r"(?:(\d+)W)?"
    r"(?:(\d+)D)?"
    r"(?:T"
    r"(?:(\d+)H)?"
    r"(?:(\d+)M)?"
    r"(?:(\d+(?:[\.,]\d+)?)S)?"  # note: decimal is either "." or ","
    r")?$"
)


def parse_iso_duration(value: str) -> Duration | None:
    """Parse ISO 8601 duration.

    A valid duration is of the form:

        PnYnMnDTnHnMnS

    Where "n" is a number and any of the elements are optional. "P" indicates
    that the value is a duration, and "T" separates day values from time values.

    A valid duration must:
        * begin with "P" (for period)
        * include at least one element (even if it is zero)
        * allow only int values, except for seconds, which can be float
          (this differs from the standard)
    """
    result = None
    if m := _valid_iso_duration.match(value):
        if any(m.groups()):
            years, months, weeks, days, hours, minutes = [
                int(val) if val is not None else 0 for val in m.groups()[:-1]
            ]
            result = Duration(
                years,
                months,
                weeks,
                days,
                hours,
                minutes,
                float(m.group(7).replace(",", ".")) if m.group(7) else 0,
            )
    return result


def sub_duration(
    ts: datetime.datetime | datetime.date, duration: Duration
) -> datetime.datetime | datetime.date:
    """Subtract time from a datetime or date."""
    negative_duration = Duration(
        -duration.years,
        -duration.months,
        -duration.weeks,
        -duration.days,
        -duration.hours,
        -duration.minutes,
        -duration.seconds,
    )
    return add_duration(ts, negative_duration)


def add_duration(
    ts: datetime.datetime | datetime.date, duration: Duration
) -> datetime.datetime | datetime.date:
    """Add time to a datetime or date."""
    if isinstance(ts, datetime.datetime):
        return add_duration_datetime(ts, duration)
    return add_duration_date(ts, duration)


def add_duration_date(ts: datetime.date, duration: Duration) -> datetime.date:
    """Add time to a datetime.date."""
    year = ts.year + duration.years + (ts.month + duration.months - 1) // 12
    month = (ts.month + duration.months - 1) % 12 + 1
    return datetime.date(year, month, 1) + datetime.timedelta(
        days=duration.days + ts.day - 1, weeks=duration.weeks
    )


def add_duration_datetime(
    ts: datetime.datetime, duration: Duration
) -> datetime.datetime:
    """Add time to a datetime.datetime."""
    tzinfo = datetime.timezone.utc if ts.tzinfo is None else ts.tzinfo
    dt = add_duration_date(ts.date(), duration)
    return datetime.datetime(
        dt.year, dt.month, dt.day, tzinfo=tzinfo
    ) + datetime.timedelta(
        hours=ts.hour + duration.hours,
        minutes=ts.minute + duration.minutes,
        seconds=ts.second + duration.seconds,
    )
