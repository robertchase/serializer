"""tests for serializer"""
# pylint: disable=missing-function-docstring, missing-class-docstring
import pytest

from serializer import Serializable, ReadOnly, Optional
from serializer.serializer import (
    ExtraAttributeError,
    DuplicateAttributeError,
    UndefinedAttributeError,
    RequiredAttributeError,
    ReadOnlyFieldError,
)


class Basic(Serializable):
    # pylint: disable=too-few-public-methods
    attr_a: int


def test_extra_attribute():
    Basic(1)
    with pytest.raises(ExtraAttributeError):
        Basic(1, 2)


def test_duplicate_attribute():
    Basic(attr_a=10)
    with pytest.raises(DuplicateAttributeError):
        Basic(1, attr_a=10)


def test_undefined_attribute_init():
    with pytest.raises(UndefinedAttributeError):
        Basic(attr_a=10, attr_b=10)


def test_required_attribute():
    with pytest.raises(RequiredAttributeError):
        Basic()


def test_invalid_attribute_get():
    instance = Basic(1)
    with pytest.raises(AttributeError):
        instance.attr_b = 0  # pylint: disable=attribute-defined-outside-init


def test_undefined_attribute_set():
    instance = Basic(1)
    with pytest.raises(UndefinedAttributeError):
        instance.attr_b = "error"  # pylint: disable=attribute-defined-outside-init


class BasicReadOnly(Serializable):
    # pylint: disable=too-few-public-methods
    attr_a: int = ReadOnly


def test_read_only_attribute():
    instance = BasicReadOnly(1)
    with pytest.raises(ReadOnlyFieldError):
        instance.attr_a = 2


class BasicPrimitive(Serializable):
    # pylint: disable=too-few-public-methods
    attr_b: float = Optional
    attr_c: bool = Optional


def test_invalid_int_value():
    expect = "invalid <int> value (hello) for field 'attr_a': not an integer"
    with pytest.raises(ValueError) as err:
        Basic(attr_a="hello")
    assert err.value.args[0] == expect


def test_invalid_float_value():
    expect = "invalid <float> value (hello) for field 'attr_b': not a float"
    with pytest.raises(ValueError) as err:
        BasicPrimitive(attr_b="hello")
    assert err.value.args[0] == expect


def test_invalid_bool_value():
    expect = "invalid <bool> value (hello) for field 'attr_c': not a boolean"
    with pytest.raises(ValueError) as err:
        BasicPrimitive(attr_c="hello")
    assert err.value.args[0] == expect


class BooleanFalseDefault(Serializable):  # pylint: disable=too-few-public-methods
    attr_a: bool = False


def test_false_default():
    instance = BooleanFalseDefault()
    assert hasattr(instance, "attr_a")
