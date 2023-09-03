"""(de-)serializing type objects"""
from datetime import date, datetime, time
import re


def get_type(type_):
    """map a type to a subclass of SerializerType"""
    if isinstance(type_, type) and issubclass(type_, SerializerType):
        return type_()
    if isinstance(type_, SerializerType):
        return type_

    return {
        int: Integer,
        float: Float,
        str: String,
        bool: Boolean,
    }.get(type_, SerializerType)()


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
        if isinstance(value, int):
            return value
        if not re.match(r"\d+", value):
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

    # TODO: add min and max length

    def __call__(self, value):
        return str(value)


class Boolean(SerializerType):
    """bool type (automatically assigned to bool annotations)"""

    __name__ = "bool"

    def __call__(self, value):
        if isinstance(value, str) and value.lower() == "true":
            return True
        if value in (1, "1"):
            return True
        if isinstance(value, str) and value.lower() == "false":
            return False
        if value in (0, "0"):
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
