"""derive field list from annotated class"""
from functools import namedtuple
import inspect

from serializer import defaults
from serializer.get_type import get_type


AnnotationField = namedtuple(
    "AnnotationField", "name, type, is_required, is_readonly, has_default, default"
)


def get_fields(item):
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
        type_ = get_type(typ)

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
        fields[nam] = AnnotationField(
            nam, type_, is_required, is_readonly, has_default, default
        )

    return fields
