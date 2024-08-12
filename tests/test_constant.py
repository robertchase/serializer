"""tests for Constant"""

import pytest

from serializer import types
import serializer


class _constant(serializer.Serializable):
    """Basic Serializable with Constant attribute."""

    a: types.Constant = "A"


class ConstantMissingDefault(serializer.Serializable):
    """Serializable with Constant attribute missing a default value."""

    a: types.Constant


def test_constant():
    """Test happy path behavior."""
    test = _constant()
    assert test.a == "A"


def test_constant_with_int():
    """Test constant operation with int value."""
    value = 10

    class ContantInt(_constant):
        """Constant with an int value."""

        a: types.Constant = value

    test = ContantInt()
    assert test.a == value

    assert test.serialize_() == {"a": value}


def test_constant_missing_default():
    """Test missing default."""
    with pytest.raises(serializer.serializable.ConstantMissingDefaultError):
        ConstantMissingDefault()

    with pytest.raises(serializer.serializable.ConstantMissingDefaultError):
        ConstantMissingDefault(a="HI")


def test_constant_read_only():
    """Test that Constant field is read-only."""

    test = _constant()
    with pytest.raises(serializer.serializable.ReadOnlyFieldError):
        test.a = "B"

    with pytest.raises(serializer.serializable.ReadOnlyFieldError):
        _constant(a="B")
