"""(de-)serializing type objects"""
from datetime import date, datetime, time
import re


def get_type(type_):
    """map a type to a subclass of SerializerType"""
    if isinstance(type_, List):
        return type_
    if isinstance(type_, type) and issubclass(type_, SerializerType):
        return type_()
    if isinstance(type_, SerializerType):
        return type_
    if isinstance(type_, type) and issubclass(type_, Serializable):
        return type_

    return {
        int: Integer,
        float: Float,
        str: String,
        bool: Boolean,
    }.get(type_, SerializerType)()


class Serializable:  # pylint: disable=too-few-public-methods
    """used to prevent a circular reference to serializer.Serializable

    Notice that serializer.Serializer is a subclass of this "interface", so
    that "get_type" can reference this class without knowing about the
    "serializer.py" module.
    """


class List:  # pylint: disable=too-few-public-methods
    """same as above"""


class SerializerType:
    """base type"""

    def __call__(self, value):
        return value

    def serialize(self, value):
        """return untouched value"""
        return value


class Integer(SerializerType):
    """int type (automatically assigned to int annotations)"""

    __name__ = "int"

    def __call__(self, value):
        if not re.match(r"\d+$", str(value)):
            raise ValueError("not an integer")
        return int(value)


class Float(SerializerType):
    """float type (automatically assigned to float annotations)"""

    __name__ = "float"

    def __call__(self, value):
        if isinstance(value, (int, float)):
            return float(value)
        if not re.match(r"(\d+|\.\d+|\d+.\d*)$", value):
            raise ValueError("not a float")
        return float(value)


class String(SerializerType):
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


class Boolean(SerializerType):
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


class ISODateTime(SerializerType):
    """a datetime.datetime object that serializes to an ISO string"""

    def __call__(self, value):
        if not isinstance(value, datetime):
            try:
                value = datetime.fromisoformat(value)
            except TypeError as err:
                raise ValueError(err) from None
        return value

    def serialize(self, value):
        return value.isoformat()


class ISODate(ISODateTime):
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


class OneOf(SerializerType):
    """allow one item from *args"""

    def __init__(self, *args):
        self.valid = set(args)

    def __call__(self, value):
        if value not in self.valid:
            raise ValueError(f"not in {self.valid}")
        return value


class SomeOf(SerializerType):
    """allow an array of items that are a subset of *args"""

    def __init__(self, *args):
        self.choices = set(args)

    def __call__(self, value):
        value = set(value)
        if not value.issubset(self.choices):
            raise ValueError(f"not a subset of {self.choices}")
        return list(value)
