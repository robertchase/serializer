# serializer
a python serializer

[![Testing: pytest](https://img.shields.io/badge/testing-pytest-yellow)](https://docs.pytest.org)
[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit/)


## introduction

The `serializer` package adds type-enforcement&mdash;and other features&mdash;to a python class.

By borrowing some of the syntax from the [dataclass](https://docs.python.org/3/library/dataclasses.html) package, `serializer` is able to leverage standard python, but with more nuanced control than a dataclass.

The dataclass package uses a decorator to automatically add methods to a class based on class fields and their annotations. By contrast, the `serializer` package is inherited and brings it's own *dunder* functions that provide features like type-enforcement, user-defined types, nested objects, read-only fields, optional fields with no default values, and serialization&mdash;*hence the name*&mdash;to and from a json-able dict.