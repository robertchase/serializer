"""List Type"""
import json

from serializer import get_type


class ListTooShortError(ValueError):
    """indicate attempt to create a list with too few items"""

    def __init__(self, minimum):
        self.args = (f"length must be at least {minimum}",)


class ListTooLongError(ValueError):
    """indicate attempt to create a list with too many items"""

    def __init__(self, maximum):
        self.args = (f"length must be no more than {maximum}",)


class ListDuplicateItemError(ValueError):
    """indicate attempt to create list with duplicate items"""

    def __init__(self, value):
        self.args = (f"{value} already in list",)


class List(get_type.List):
    """support a list as a Field type"""

    def __init__(self, element_type, min_length=0, max_length=0, allow_dups=True):
        self.min = min_length
        self.max = max_length
        self.allow_dups = allow_dups
        self.type = get_type.get_type(element_type)

    def __call__(self, value):
        return _List(self, value)

    def __serialize__(self, value):
        """serialize "value" as a List"""
        return value.__serialize__()


class _List:
    """List instance"""

    def __init__(self, parent, value):
        self.type = parent.type
        self.min = parent.min
        self.max = parent.max
        self.allow_dups = parent.allow_dups

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
        if not isinstance(value, list):
            raise AttributeError("expecting a list")
        if self.min > 0:
            if len(value) < self.min:
                raise ListTooShortError(self.min)
        if self.max > 0:
            if len(value) > self.max:
                raise ListTooLongError(self.max)

        self.store = []
        for position, item in enumerate(value, start=1):
            try:
                self.append(item)
            except (AttributeError, ValueError) as err:
                msg = f"{position=}, {item=}: {err.args[0]}"
                err.args = (msg,)
                raise

    def __repr__(self):
        return f"List{self.__serialize__()}"

    def __serialize__(self):
        """return a un-object-ed version of the list and any items"""
        return [self.type.__serialize__(item) for item in self.store]

    def __len__(self):
        return len(self.store)

    def __eq__(self, other):
        return self.store == other

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        if not isinstance(value, self.type):
            value = self.type(value)
        if not self.allow_dups:
            if self.store.count(value) != 0 and self.store[key] != value:
                raise ListDuplicateItemError(value)
        self.store[key] = value

    def __delitem__(self, key):
        if self.min > 0:
            # preflight length check (key is an arbitrary slice)
            temp = [0] * len(self.store)
            del temp[key]
            if len(temp) < self.min:
                raise ListTooShortError(self.min)
        del self.store[key]

    def append(self, value):
        """append to list while honoring min, max and duplicate"""
        if self.max > 0:
            if len(self.store) == self.max:
                raise ListTooLongError(self.max)
        value = self.type(value)
        if not self.allow_dups and value in self.store:
            raise ListDuplicateItemError(value)
        self.store.append(value)

    def index(self, *args, **kwargs):
        """shadow index call of underlying store"""
        return self.store.index(*args, **kwargs)
