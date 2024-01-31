"""(de-)serializing type objects"""
from datetime import date, datetime, time
import json
import re


class SerializableType:
    """base type"""

    def __call__(self, value):
        """accept any value"""
        return value

    def serialize(self, value):
        """return untouched value"""
        return value


class Integer(SerializableType):
    """int type (automatically assigned to int annotations)"""

    valid = re.compile(r"[-+]?\d+$")

    def __init__(self, minimum=None, maximum=None, force=False, name=None):
        self.min = int(minimum) if minimum is not None else None
        self.max = int(maximum) if maximum is not None else None
        self.force = force  # force to min or max instead of raising Error

        if minimum is None and maximum is None:
            self.__name__ = "int"

        if name:
            self.__name__ = name

    def __call__(self, value):
        if not self.valid.match(str(value)):
            raise ValueError("not an integer")
        value = int(value)
        if self.min is not None:
            if value < self.min:
                if self.force:
                    value = self.min
                else:
                    raise ValueError(f"not >= {self.min}")
        if self.max is not None:
            if value > self.max:
                if self.force:
                    value = self.max
                else:
                    raise ValueError(f"not <= {self.max}")
        return value


class Float(SerializableType):
    """float type (automatically assigned to float annotations)"""

    valid = re.compile(r"[-+]?(\d+|\.\d+|\d+.\d*)$")

    def __init__(  # pylint: disable=too-many-arguments
        self,
        minimum=None,
        maximum=None,
        exclusive_min=False,
        exclusive_max=False,
        name=None,
    ):
        self.min = float(minimum) if minimum is not None else None
        self.max = float(maximum) if maximum is not None else None
        self.exclusive_min = exclusive_min
        self.exclusive_max = exclusive_max

        if minimum is None and maximum is None:
            self.__name__ = "float"

        if name:
            self.__name__ = name

    def __call__(self, value):
        if not self.valid.match(str(value)):
            raise ValueError("not a float")
        value = float(value)
        if self.min is not None:
            if self.exclusive_min:
                if value <= self.min:
                    raise ValueError(f"not > {self.min}")
            else:
                if value < self.min:
                    raise ValueError(f"not >= {self.min}")
        if self.max is not None:
            if self.exclusive_max:
                if value >= self.max:
                    raise ValueError(f"not < {self.max}")
            else:
                if value > self.max:
                    raise ValueError(f"not <= {self.max}")
        return value


class String(SerializableType):
    """str type (automatically assigned to str annotations)"""

    def __init__(self, min_length=0, max_length=None):
        self.min_length = int(min_length)
        if self.min_length < 0:
            raise AttributeError("min_length must be greater than or equal to zero")
        if max_length is not None:
            max_length = int(max_length)
            if max_length < min_length:
                raise AttributeError(
                    f"max_length must be greater than {self.min_length}"
                )
        self.max_length = max_length

    def __call__(self, value):
        value = str(value)
        if self.min_length:
            if len(value) < self.min_length:
                raise ValueError(
                    f"is shorter than the minimum length ({self.min_length})"
                )
        if self.max_length is not None:
            if len(value) > self.max_length:
                raise ValueError(
                    f"is longer than the maximum length ({self.max_length})"
                )
        return value


class Boolean(SerializableType):
    """bool type (automatically assigned to bool annotations)"""

    __name__ = "bool"

    def __call__(self, value):
        if isinstance(value, str) and value.lower() == "true":
            return True
        if value in (1, "1", True):
            return True
        if isinstance(value, str) and value.lower() == "false":
            return False
        if value in (0, "0", False):
            return False
        raise ValueError("not a boolean")

    def serialize(self, value):
        return 1 if value else 0


class ISODateTime(SerializableType):
    """a datetime.datetime object that serializes to an ISO string"""

    def __init__(self, default_offset=None):
        self.default_offset = default_offset

    def __call__(self, value):
        if isinstance(value, datetime):
            result = value
        else:
            try:
                result = datetime.fromisoformat(value)
                if self.default_offset and result.tzinfo is None:
                    result = datetime.fromisoformat(value + self.default_offset)
            except TypeError as err:
                raise ValueError(err) from None
        return result

    def serialize(self, value):
        return value.isoformat()


class ISODate(SerializableType):
    """a datetime.date object that serializes to an ISO string"""

    def __call__(self, value):
        if not isinstance(value, date):
            try:
                value = date.fromisoformat(value)
            except TypeError as err:
                raise ValueError(err) from None
        return value

    def serialize(self, value):
        return value.isoformat()


class ISOTime(ISODateTime):
    """a datetime.time object that serializes to an ISO string"""

    def __call__(self, value):
        if not isinstance(value, time):
            try:
                value = time.fromisoformat(value)
            except TypeError as err:
                raise ValueError(err) from None
        return value


class OneOf(SerializableType):
    """allow one item from *args"""

    def __init__(self, *args, name=None):
        self.valid = set(args)

        if name:
            self.__name__ = name

    def __call__(self, value):
        if value not in self.valid:
            raise ValueError(f"not in {self.valid}")
        return value


class SomeOf(SerializableType):
    """allow an array of items that are a subset of *args"""

    def __init__(self, *args, name=None):
        self.choices = set(args)

        if name:
            self.__name__ = name

    def __call__(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as err:
                raise ValueError(err) from None
        distinct = set(value)
        if len(distinct) != len(value):
            raise ValueError("not a unique list of values")
        if not distinct.issubset(self.choices):
            raise ValueError(f"not a subset of {self.choices}")
        return value

    def serialize(self, value):
        return json.dumps(value)


class Map(SerializableType):
    """map (dict) -> json"""

    def __call__(self, value: dict):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as err:
                raise ValueError(err) from None
        if not isinstance(value, dict):
            raise ValueError("not a dict")
        return value

    def serialize(self, value):
        return json.dumps(value)
