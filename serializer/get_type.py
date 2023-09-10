"""determine the proper "type" for an instance/class"""
from serializer import types


class List:  # pylint: disable=too-few-public-methods
    """base class "interface" for list.List

    prevents circular reference
    """


class Serializable:  # pylint: disable=too-few-public-methods
    """base class "interface" for serializer.Serializable

    prevents circular reference
    """


def get_type(type_):
    """map a type to a subclass of SerializerType"""
    if isinstance(type_, List):
        return type_
    if isinstance(type_, type) and issubclass(type_, Serializable):
        return Nested(type_)
    if isinstance(type_, Serializable):
        return Nested(type_)
    if isinstance(type_, type) and issubclass(type_, types.SerializerType):
        return type_()
    if isinstance(type_, types.SerializerType):
        return type_

    return {
        int: types.Integer,
        float: types.Float,
        str: types.String,
        bool: types.Boolean,
    }.get(type_, types.SerializerType)()


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

    def __serialize__(self, instance):
        """defer to type_'s __serialize__"""
        return self.type_.__serialize__(instance)
