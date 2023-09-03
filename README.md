# serializer
a python serializer

[![Testing: pytest](https://img.shields.io/badge/testing-pytest-yellow)](https://docs.pytest.org)
[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit/)


## introduction

The `serializer` package adds serialization, type-enforcement, and other features to a python class.

By borrowing some of the syntax from the [dataclass](https://docs.python.org/3/library/dataclasses.html) package, `serializer` is able to leverage standard python, but with more nuanced control than that provided by a dataclass.

The dataclass package uses a decorator to automatically add methods to a class based on that class's fields and their annotations. By contrast, the `serializer` package is inherited and brings it's own *dunder* functions that provide features like: type-enforcement, attribute constraint, user-defined types, nested objects, read-only fields, optional fields with no default values, and *serialization*.

## example

```
class Apartment(Serializable):
    floor: int
    unit: str
    balcony: bool = Optional
    is_studio: bool = False
    
class Person(Serializable):
    name: str
    address: Apartment
```

Here two classes are defined.

#### Apartment

The `Apartment` class has four attributes, two of which are required&mdash;an `Apartment` can't be created that doesn't include `floor` and `unit`. Here is an `Apartment` being created in code (these produce equivalent instances):

```
apt = Apartment(3, "A")
apt = Apartment(floor=3, unit="A")
apt = Apartment("3", unit="A", is_studio=False)
```

The instance can be serialized to a dict:

```
>> apt.serialize()
{'floor': 3, 'unit': 'A', is_studio: False}
```

The instance fields operate as expected:

```
>> apt.balcony = True
>> apt.is_studio = True
>> apt.serialize()
{'floor': 3, 'unit': 'A', 'is_studio': True, 'balcony': True}

>> apt.bathrooms = 1
UndefinedAttributeError: 'Apartment' object has no attribute 'bathrooms'

apt.floor = "three"
ValueError: invalid <int> value (three) for field 'floor': not an integer
```

Optional fields only appear if assigned. Fields that are not defined in the class cannot be used. Values that don't match the annotation's type are not accepted.

#### Person

The `Person` class includes a field&mdash;`address`&mdash;whose type is `Apartment`. A `Serializable` class can be used as an annotated type, creating a nested object. These four ways to create a new `Person` are equivalent:

```
tenant = Person(name="John Doe", address={"floor": 3, "unit": "A"})
tenant = Person("John Doe", {"floor": 3, "unit": "A"})
tenant = Person("John Doe", [3, "A"])  # a list is treated as *args
apt = Apartment(3, "A")
tenant = Person("John Doe", apt)
```

Serialize the tenant:

```
tenant.serialize()
{'name': 'John Doe', 'address': {'floor': 3, 'unit': 'A', 'is_studio': False}}
```

The serialized version of an object can be used to create a new object&mdash;a method which even works with nested objects:

```
ser = tenant.serialize()
tenant = Person(**ser)
```

Access the `Apartment` attribute in the expected way:

```
print(tenant.address.unit)
A
```