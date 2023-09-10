"""(de-)serializing type objects"""
from datetime import date, datetime, time
import re


def get_type(type_):
    """map a type to a subclass of SerializerType"""
    if isinstance(type_, List):
        return type_
    if isinstance(type_, type) and issubclass(type_, Serializable):
        return Nested(type_)
    if isinstance(type_, Serializable):
        return Nested(type_)
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


class Nested:
    """enable nested Serializable objects"""

    def __init__(self, type_):
        self.type_ = type_
        self.__name__ = getattr(type_, "__name__", type_.__class__.__name__)

    def __call__(self, *args, **kwargs):
        # special case handling of single argument calls
        if not kwargs and len(args) == 1:
            arg0 = args[0]

            if isinstance(arg0, self.type_):  # already the right shape
                return arg0

            if isinstance(arg0, dict):  # treat dict as **kwargs
                kwargs = arg0
                args = []

            elif isinstance(arg0, list):  # treat list as *args
                args = arg0

        return self.type_(*args, **kwargs)

    def serialize(self, instance):
        """defer to type_'s serialize"""
        return self.type_.serialize(instance)


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

    def __init__(self, minimum=None, maximum=None, name=None):
        self.min = int(minimum) if minimum is not None else None
        self.max = int(maximum) if maximum is not None else None

        if minimum is None and maximum is None:
            self.__name__ = "int"

        if name:
            self.__name__ = name

    def __call__(self, value):
        if not re.match(r"[-+]?\d+$", str(value)):
            raise ValueError("not an integer")
        value = int(value)
        if self.min is not None:
            if value < self.min:
                raise ValueError(f"not >= {self.min}")
        if self.max is not None:
            if value > self.max:
                raise ValueError(f"not <= {self.max}")
        return value


class Float(SerializerType):
    """float type (automatically assigned to float annotations)"""

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

        if (
            minimum is None
            and maximum is None
            and not exclusive_min
            and not exclusive_max
        ):
            self.__name__ = "float"

        if name:
            self.__name__ = name

    def __call__(self, value):
        if not re.match(r"[-+]?(\d+|\.\d+|\d+.\d*)$", str(value)):
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

    def __init__(self, *args, name=None):
        self.valid = set(args)

        if name:
            self.__name__ = name

    def __call__(self, value):
        if value not in self.valid:
            raise ValueError(f"not in {self.valid}")
        return value


class SomeOf(SerializerType):
    """allow an array of items that are a subset of *args"""

    def __init__(self, *args, name=None):
        self.choices = set(args)

        if name:
            self.__name__ = name

    def __call__(self, value):
        value = set(value)
        if not value.issubset(self.choices):
            raise ValueError(f"not a subset of {self.choices}")
        return list(value)
