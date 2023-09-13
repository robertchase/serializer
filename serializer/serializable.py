"""Constrained and serializable alternative to a dataclass

Use dataclass-like class-level field definitions to create an object which
enforces the typing of values based on field annotations. Available fields
are limited to those defined in the class.
"""
import inspect

from serializer import defaults
from serializer import get_type


class ExtraAttributeError(AttributeError):
    """indicate too many attributes specified on init"""

    def __init__(self, names):
        self.args = (f"extra attribute(s): {', '.join(str(name) for name in names)}",)


class DuplicateAttributeError(AttributeError):
    """indicate attribute defined in both args and kwargs"""

    def __init__(self, name):
        self.args = (f"duplicate attribute: {name}",)


class UndefinedAttributeError(AttributeError):
    """indicate use of undefined attribute"""

    def __init__(self, instance, name):
        class_ = instance.__class__.__name__
        self.args = (f"'{class_}' object has no attribute '{name}'",)


class RequiredAttributeError(AttributeError):
    """indicate missing required attribute"""

    def __init__(self, name):
        self.args = (f"missing required attribute: {name}",)


class ReadOnlyFieldError(ValueError):
    """indicate illegal use of read-only field"""

    def __init__(self, name):
        self.args = (f"field '{name}' is read-only",)


class Serializable(get_type.Serializable):
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

    def __init__(self, *args, **kwargs):  # pylint: disable=too-many-branches
        fields = self.fields_

        if len(args) > len(fields):
            raise ExtraAttributeError(args[len(fields) :])

        for value, field in zip(args, fields.values()):
            if field.name in kwargs:
                raise DuplicateAttributeError(field.name)
            kwargs[field.name] = value  # convert args to kwargs

        for name in kwargs:
            if name not in fields:
                raise UndefinedAttributeError(self, name)

        for field in fields.values():
            if field.is_required:
                if not field.has_default:
                    if field.name not in kwargs:
                        raise RequiredAttributeError(field.name)
            if field.has_default:
                if field.name not in kwargs:
                    kwargs[field.name] = field.default

        for field in fields.values():
            if field.name in kwargs:
                self._setattr(field, kwargs[field.name])

    def __setattr__(self, name, value):
        fields = self.fields_

        if not (field := fields.get(name)):
            raise UndefinedAttributeError(self, name)
        if field.is_readonly:
            raise ReadOnlyFieldError(name)

        self._setattr(field, value)

    def _setattr(self, field, value):
        try:
            normalized = field.type(value)
        except (AttributeError, ValueError) as err:
            type_name = getattr(field.type, "__name__", field.type.__class__.__name__)
            error = (
                f"invalid <{type_name}> value ({value}) for field '{field.name}'"
                f": {str(err)}"
            )
            err.args = (error,)
            raise
        self.__dict__[field.name] = normalized

    def __delattr__(self, name):
        fields = self.fields_
        if not (field := fields.get(name)):
            raise UndefinedAttributeError(self, name)
        if field.is_readonly:
            raise ReadOnlyFieldError(name)
        del self.__dict__[name]

    def __repr__(self):
        """bad idea for sensitive data, but handy nonetheless"""
        return f"{self.__class__.__name__}: {self.__dict__}"

    def serialize_(self):
        """serialize method

        added underbar to keep object namespace clean
        """
        return {
            field.name: field.type.serialize(getattr(self, field.name))
            for field in self.fields_.values()
            if hasattr(self, field.name)
        }

    @property
    def fields_(self):
        """derive list of fields from class annotations

        Run once, caching results in class.
        """

        class AnnotatedField:  # pylint: disable=too-few-public-methods
            """container for field definition"""

            def __init__(
                self, name, type_, is_required, is_readonly, has_default, default
            ):  # pylint: disable=too-many-arguments
                self.name = name
                self.type = type_
                self.is_required = is_required
                self.is_readonly = is_readonly
                self.has_default = has_default
                self.default = default

        class_ = self.__class__
        if hasattr(class_, "__serializable__"):
            return class_.__serializable__

        # first time through, create a new dict of AnnotationFields in the class
        fields = class_.__serializable__ = {}

        for nam, typ in inspect.get_annotations(class_).items():
            # normalize type
            type_ = get_type.get_type(typ)

            # basic field characteristics
            is_required = False
            is_readonly = False
            has_default = False
            default = None

            # adjust field characteristics based on specified default values
            # default values are stored as class attributes
            if hasattr(class_, nam):
                setting = getattr(class_, nam)

                if setting == defaults.ReadOnly:  # class
                    is_readonly = True
                    is_required = True
                elif isinstance(setting, defaults.ReadOnly):  # instance
                    is_readonly = True
                    has_default = True
                    default = setting.default
                elif setting == defaults.Optional:
                    pass
                elif setting == defaults.OptionalReadOnly:
                    is_readonly = True
                else:
                    has_default = True
                    default = setting

                delattr(class_, nam)  # don't need to keep these around
            else:
                is_required = True

            # bundle up the field
            fields[nam] = AnnotatedField(
                nam, type_, is_required, is_readonly, has_default, default
            )

        return fields


def serialize(item):
    """convenience function for serialization"""
    return item.serialize_()