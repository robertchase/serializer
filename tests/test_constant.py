"""tests for Constant"""

import pytest

from serializer import types
import serializer


class _constant(serializer.Serializable):
    """Basic Serializable with Constant attribute."""

    a: types.Constant = "A"


class _constant_missing_default(serializer.Serializable):
    """Serializable with Constant attribute missing a default value."""

    a: types.Constant


def test_constant():
    """Test happy path behavior."""
    test = _constant()
    assert test.a == "A"


def test_constant_missing_default():
    """Test missing default."""
    with pytest.raises(serializer.serializable.ConstantMissingDefaultError):
        _constant_missing_default()

    with pytest.raises(serializer.serializable.ConstantMissingDefaultError):
        _constant_missing_default(a="HI")


def test_constant_read_only():
    """Test that Constant field is read-only."""

    test = _constant()
    with pytest.raises(serializer.serializable.ReadOnlyFieldError):
        test.a = "B"

    with pytest.raises(serializer.serializable.ReadOnlyFieldError):
        _constant(a="B")
