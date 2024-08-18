"""Serializable date and datetime ranges."""

import datetime
import re

from dateutil.relativedelta import relativedelta

import serializer
from serializer.types import ISODateTime, ISODate


class Range(serializer.Serializable):
    """A range bounded by two values (default: int).

    A range has a lower_bound and an upper_bound which can be compared with
    >, <, >=, <=.

    If is_upper_exclusive is True or is_lower_exclusive is True, comparisons
    on the respective bounds will exclude the bound itself; otherwise, the
    bound is part of the range.
    """

    lower_bound: int
    upper_bound: int
    is_lower_exclusive: bool = False
    is_upper_exclusive: bool = False

    def _parse_string_arg(self, arg):  # override
        """Parse range elements as a comma separated string."""
        return arg.split(",")

    def _after_init(self):  # override
        if self.lower_bound > self.upper_bound:
            raise ValueError("lower_bound cannot be greater than upper_bound")

    def contains(self, value: datetime.datetime) -> bool:
        """Checks if value is within the range bounds."""
        if self.is_lower_exclusive and value <= self.lower_bound:
            return False
        if value < self.lower_bound:
            return False
        if self.is_upper_exclusive and value >= self.upper_bound:
            return False
        if value > self.upper_bound:
            return False
        return True


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

    If timezone information is not provided, then "Z" will be used.
    """

    lower_bound: ISODateTime
    upper_bound: ISODateTime

    def _parse_string_arg(self, arg):
        """Parse range elements as an ISO range."""
        return parse_iso_range(arg, self.date_parser, self.duration_parser)

    def date_parser(self, value):
        """Parse datetime."""
        try:
            parsed = datetime.datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                parsed = datetime.datetime.fromisoformat(value + "Z")
            return parsed
        except ValueError:
            raise ValueError("invalid datetime value") from None

    def duration_parser(self, value):
        """Parse duration value."""
        return parse_iso_duration(value)


class ISODateRange(ISODateTimeRange):
    """A range bounded by two dates."""

    lower_bound: ISODate
    upper_bound: ISODate

    def date_parser(self, value):
        """Parse datetime.date."""
        try:
            return datetime.datetime.fromisoformat(value).date()
        except ValueError:
            pass
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            raise ValueError("invalid date value") from None

    def duration_parser(self, value):
        """Remove time portion from duration value before parsing."""
        return parse_iso_duration(value.split("T")[0])


def parse_iso_range(value: str, date_parser, duration_parser):
    """parse a daterange into a pair (list) of datetime or date values"""

    if len(parts := re.split(r"/|--", value)) == 1:
        raise ValueError("range separator not found")

    part1, part2 = parts

    if part1[0] == part2[0] == "P":
        raise ValueError("both parts of a range cannot be durations")

    if part1[0] == "P":
        end_date = date_parser(part2)
        if (duration := duration_parser(part1)) is None:
            raise ValueError("invalid duration value")
        start_date = end_date - duration
    elif part2[0] == "P":
        start_date = date_parser(part1)
        if (duration := duration_parser(part2)) is None:
            raise ValueError("invalid duration value")
        end_date = start_date + duration
    else:
        start_date = date_parser(part1)
        end_date = date_parser(part2)

    return [start_date, end_date]


_valid_iso_duration = re.compile(
    r"P(?:(\d+)Y)?"
    r"(?:(\d+)M)?"
    r"(?:(\d+(?:[\.,]\d+)?)W)?"  # note: decimal is either "." or ","
    r"(?:(\d+(?:[\.,]\d+)?)D)?"
    r"(?:T"
    r"(?:(\d+(?:[\.,]\d+)?)H)?"
    r"(?:(\d+(?:[\.,]\d+)?)M)?"
    r"(?:(\d+(?:[\.,]\d+)?)S)?"
    r")?$"
)


def parse_iso_duration(value: str) -> relativedelta | None:
    """Parse ISO 8601 duration.

    A valid duration is of the form:

        PnYnMnDTnHnMnS

    Where "n" is a number and any of the elements are optional. "P" indicates
    that the value is a duration, and "T" separates day values from time values.

    A valid duration must:
        * begin with "P" (for period)
        * include at least one element (even if it is zero)
        * allow decimal numbers for every element except (Y)ear and (M)onth
          (this differs from the standard which implies that only the last
           defined element can include a decimal)
    """
    result = None
    if m := _valid_iso_duration.match(value):
        if any(m.groups()):
            years, months, weeks, days, hours, minutes, seconds = [
                float(val.replace(",", ".")) if val else 0 for val in m.groups()
            ]
            result = relativedelta(
                years=years,
                months=months,
                weeks=weeks,
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds,
            )
    return result
