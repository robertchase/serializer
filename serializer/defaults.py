"""special default values for Serializable classes"""


class Optional:  # pylint: disable=too-few-public-methods
    """Special default signifier for "optional" fields.

    Usage:
        age: int = Optional

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

    Usage:
        age: int = ReadOnly
        from_another_planet: bool = ReadOnly(False)

    Read-only fields can be set at init, but are not allowed to be changed
    after init.

    Includes a optional default value.
    """

    def __init__(self, default):
        self.default = default


class OptionalReadOnly:  # pylint: disable=too-few-public-methods
    """Special default signifier that combines "optional" and "read only"."""
