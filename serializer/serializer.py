from functools import namedtuple
import inspect

from serializer import types


class Optional:
    pass


class ReadOnly:
    def __init__(self, default):
        self.default = default


class OptionalReadOnly:
    pass


class Serializable:
    # TODO: add __delattr__
    # TODO: add AttributeError subclasses

    def __init__(self, *args, **kwargs):
        fields = annotate(self)

        if len(args) > len(fields):
            raise AttributeError(f"extra attribute error {args[len(fields):]}")

        for value, field in zip(args, fields.values()):
            if field.name in kwargs:
                raise AttributeError(f"duplicate attribute error {field.name}")
            kwargs[field.name] = value  # convert args to kwargs

        for name in kwargs.keys():
            if name not in fields:
                raise AttributeError(f"undefined field name '{name}'")

        for field in fields.values():
            if field.is_required:
                if not field.has_default:
                    if field.name not in kwargs:
                        raise AttributeError(
                            f"missing required attribute '{field.name}'")
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
                f"assignment {field.name}={value} failed: {str(err)}") from None
        self.__dict__[field.name] = normalized

    def __repr__(self):
        return f"{self.__class__.__name__}: {self.__dict__}"

    def serialize(self):
        fields = annotate(self)
        return {
            field.name: field.type.serialize(getattr(self, field.name))
            for field in fields.values()
            if hasattr(self, field.name)
        }


class Nested:

    def __init__(self, type_):
        self.type_ = type_

    def __call__(self, *args, **kwargs):
        if not kwargs and len(args) == 1:
            arg0 = args[0]
            if isinstance(arg0, self.type_):
                return arg0
            if isinstance(arg0, dict):
                kwargs = arg0
                args = []
            elif isinstance(arg0, list):
                args = arg0
        return self.type_(*args, **kwargs)

    def serialize(self, instance):
        return self.type_.serialize(instance)


AnnotationField = namedtuple(
    "AnnotationField",
    "name, type, is_required, is_readonly, has_default, default")


def annotate(item):

    # lazy, cached AnnotationField dict
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
            type_ = types.map(typ)

        # basic field characteristics
        is_required = False
        is_readonly = False
        has_default = False
        default = None

        # adjust field characteristics based on specified default values
        # default values are stored as class attributes
        if (setting := getattr(class_, nam, None)):

            if setting == ReadOnly:
                is_readonly = True
                is_required = True
            elif isinstance(setting, ReadOnly):
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
            nam, type_, is_required, is_readonly, has_default, default)

    return fields
