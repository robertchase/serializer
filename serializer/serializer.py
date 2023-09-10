"""Constrained and serializable alternative to a dataclass

Use dataclass-like class-level field definitions to create an object which
enforces the typing of values based on field annotations. Available fields
are limited to those defined in the class.
"""
from serializer.fields import get_fields
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
        fields = get_fields(self)

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
        fields = get_fields(self)

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
        fields = get_fields(self)
        if not (field := fields.get(name)):
            raise UndefinedAttributeError(self, name)
        if field.is_readonly:
            raise ReadOnlyFieldError(name)
        del self.__dict__[name]

    def __repr__(self):
        """bad idea for sensitive data, but handy nonetheless"""
        return f"{self.__class__.__name__}: {self.__dict__}"

    def __serialize__(self):
        return serialize(self)


def serialize(item):
    """Turn item into dict

    Note that this is really an "as_dict" implementation whose result
    should json.dumps without issue. If non-primitive types are returned
    from any of the object hierachy's members' serialize methods, then
    special json.dumps handling may be necessary.
    """
    fields = get_fields(item)
    return {
        field.name: field.type.__serialize__(getattr(item, field.name))
        for field in fields.values()
        if hasattr(item, field.name)
    }
