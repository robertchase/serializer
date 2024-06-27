"""determine the proper "type" for an instance/class"""

from serializer import types


class List:  # pylint: disable=too-few-public-methods
    """base class "interface" for list.List

    prevents circular reference
    """


class Serializable:  # pylint: disable=too-few-public-methods
    """base class "interface" for serializable.Serializable

    prevents circular reference
    """


def get_type(type_):
    """map a type to a subclass of SerializableType"""
    if isinstance(type_, List):
        return type_
    if isinstance(type_, type) and issubclass(type_, Serializable):
        return Nested(type_)
    if isinstance(type_, Serializable):
        return Nested(type_)
    if isinstance(type_, type) and issubclass(type_, types.SerializableType):
        return type_()
    if isinstance(type_, types.SerializableType):
        return type_

    return {
        int: types.Integer,
        float: types.Float,
        str: types.String,
        bool: types.Boolean,
    }.get(type_, types.SerializableType)()


class Nested:
    """enable nested Serializable objects"""

    def __init__(self, type_):
        self.type = type_
        self.__name__ = getattr(type_, "__name__", type_.__class__.__name__)

    def __call__(self, *args, **kwargs):
        # special case handling of single argument calls
        if not kwargs and len(args) == 1:
            arg0 = args[0]

            if isinstance(arg0, self.type):  # already the right shape
                return arg0

            if isinstance(arg0, dict):  # treat dict as **kwargs
                kwargs = arg0
                args = []

            elif isinstance(arg0, (list, tuple)):  # treat list as *args
                args = arg0

        return self.type(*args, **kwargs)

    def serialize(self, instance):
        """defer to type's serialize_"""
        return self.type.serialize_(instance)
