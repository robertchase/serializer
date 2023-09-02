"""Constrained and serializable alternative to dataclass

Use dataclass-like class-level field definitions to create an object which
enforces the typing of values based on field annotations. Available fields
are limited to those defined in the class.
"""
from functools import namedtuple
import inspect

from serializer import types


class Optional:  # pylint: disable=too-few-public-methods
    """Special default signifier for "optional" fields.

    There is no "optional" indicator in python. A field without a default is
    "required", and a field with a default is optional (doesn't need to be
    specified at init), but will be supplied with the default value if not
    othewise supplied. This indicator allows an "optional" field with no
    default value.

    If no value is supplied at init, then no field exists in the object; it
    can be assigned at a later time.
    """


class ReadOnly:  # pylint: disable=too-few-public-methods
    """Special default signifier for "read only" fields.

    Read-only fields can be set at init, but are not allowed to be changed
    after init.

    Includes a optional default value.
    """

    def __init__(self, default):
        self.default = default


class OptionalReadOnly:  # pylint: disable=too-few-public-methods
    """Special default signifier that combines "optional" and "read only"."""


class Serializable:
    """Python object <-> dict mapper.

    Use dataclass-like class attribute definitions, for instance:

        name: str
        nickname: str = Optional
        score: int = 100

    to define the set of valid fields for an object. Field definitions include
    data types (standard and user-defined, simple and nested), defaults, and
    special handling like optional and read-only fields.

    A field's annotated type is enforced at init and whenever the field is
    changed. Only defined fields can be used in an instance.

    The resuling object can be "serialized" into a dict, and a dict can be
    used to instantiate a new object with MyObject(**dict).
    """

    # TODO: add __delattr__
    # TODO: add AttributeError subclasses

    def __init__(self, *args, **kwargs):  # pylint: disable=too-many-branches
        fields = annotate(self)

        if len(args) > len(fields):
            raise AttributeError(f"extra attribute error {args[len(fields):]}")

        for value, field in zip(args, fields.values()):
            if field.name in kwargs:
                raise AttributeError(f"duplicate attribute error {field.name}")
            kwargs[field.name] = value  # convert args to kwargs

        for name in kwargs:
            if name not in fields:
                raise AttributeError(f"undefined field name '{name}'")

        for field in fields.values():
            if field.is_required:
                if not field.has_default:
                    if field.name not in kwargs:
                        raise AttributeError(
                            f"missing required attribute '{field.name}'"
                        )
            if field.has_default:
                if field.name not in kwargs:
                    kwargs[field.name] = field.default

        for field in fields.values():
            if field.name in kwargs:
                self._setattr(field, kwargs[field.name])

    def __setattr__(self, name, value):
        fields = annotate(self)

        if not (field := fields.get(name)):
            raise AttributeError(f"invalid field '{name}'")
        if field.is_readonly:
            raise AttributeError(f"field '{name}' is read-only")

        self._setattr(field, value)

    def _setattr(self, field, value):
        try:
            normalized = field.type(value)
        except ValueError as err:
            raise AttributeError(
                f"assignment {field.name}={value} failed: {str(err)}"
            ) from None
        self.__dict__[field.name] = normalized

    def __repr__(self):
        """bad idea for sensitive data, but handy nonetheless"""
        return f"{self.__class__.__name__}: {self.__dict__}"

    def serialize(self):
        """Turn instance into dict

        Note that this is really an "as_dict" implementation whose result
        should json.dumps without issue. If non-primitive types are returned
        from any of the object hierachy's members' serialize methods, then
        special json.dumps handling may be necessary.
        """
        fields = annotate(self)
        return {
            field.name: field.type.serialize(getattr(self, field.name))
            for field in fields.values()
            if hasattr(self, field.name)
        }


class Nested:
    """enable nested Serializable objects"""

    def __init__(self, type_):
        self.type_ = type_

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


AnnotationField = namedtuple(
    "AnnotationField", "name, type, is_required, is_readonly, has_default, default"
)


def annotate(item):
    """derive list of fields from class annotations

    Run once, caching results in class.
    """
    class_ = item if isinstance(item, type) else item.__class__
    if hasattr(class_, "__serializable__"):
        return class_.__serializable__

    # first time through, create a new dict of AnnotationFields in the class
    fields = class_.__serializable__ = {}

    for nam, typ in inspect.get_annotations(class_).items():
        # normalize type
        if isinstance(typ, type) and issubclass(typ, Serializable):
            type_ = Nested(typ)
        elif isinstance(typ, Serializable):
            type_ = Nested(typ)
        else:
            type_ = types.get_type(typ)

        # basic field characteristics
        is_required = False
        is_readonly = False
        has_default = False
        default = None

        # adjust field characteristics based on specified default values
        # default values are stored as class attributes
        if setting := getattr(class_, nam, None):
            if setting == ReadOnly:  # class
                is_readonly = True
                is_required = True
            elif isinstance(setting, ReadOnly):  # instance
                is_readonly = True
                has_default = True
                default = setting.default
            elif setting == Optional:
                pass
            elif setting == OptionalReadOnly:
                is_readonly = True
            else:
                has_default = True
                default = setting

            delattr(class_, nam)  # don't need to keep these around
        else:
            is_required = True

        # bundle up the field
        fields[nam] = AnnotationField(
            nam, type_, is_required, is_readonly, has_default, default
        )

    return fields
