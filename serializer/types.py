from datetime import date, datetime, time
import re


def map(type_):

    if isinstance(type_, type) and issubclass(type_, SerializerType):
        return type_()
    if isinstance(type_, SerializerType):
        return type_

    return {
        int: IntegerType,
        float: FloatType,
        str: StringType,
        bool: BooleanType,
    }.get(type_, SerializerType)()


class SerializerType:

    def __call__(self, value):
        return value

    def serialize(self, value):
        return value


class IntegerType(SerializerType):

    def __call__(self, value):
        if isinstance(value, int):
            return value
        if not re.match(r"\d+", value):
            raise ValueError("not an integer")
        return int(value)


class FloatType(SerializerType):

    def __call__(self, value):
        if isinstance(value, (int, float)):
            return float(value)
        if re.match(r"(\d+|\.\d+|\d+.\d*)$", value):
            raise ValueError("not a float")
        return float(value)


class StringType(SerializerType):
    # TODO: add min and max length

    def __call__(self, value):
        return str(value)


class BooleanType(SerializerType):

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


class ISODateTimeType(SerializerType):

    def __call__(self, value):
        if not isinstance(value, datetime):
            try:
                value = datetime.fromisoformat(value)
            except TypeError as err:
                raise ValueError(err) from None
        return value

    def serialize(self, value):
        return value.isoformat()


class ISODateType(ISODateTimeType):

    def __call__(self, value):
        if not isinstance(value, date):
            try:
                value = date.fromisoformat(value)
            except TypeError as err:
                raise ValueError(err) from None
        return value

    def serialize(self, value):
        return value.isoformat()


class ISOTimeType(ISODateTimeType):

    def __call__(self, value):
        if not isinstance(value, time):
            try:
                value = time.fromisoformat(value)
            except TypeError as err:
                raise ValueError(err) from None
        return value


class OneOfType(SerializerType):

    def __init__(self, *args):
        self.valid = set(args)

    def __call__(self, value):
        if value not in self.valid:
            raise ValueError(f"not in {self.valid}")
        return value


class SomeOfType(SerializerType):

    def __init__(self, *args):
        self.choices = set(args)

    def __call__(self, value):
        value = set(value)
        if not value.issubset(self.choices):
            raise ValueError(f"not a subset of {self.choices}")
        return list(value)
