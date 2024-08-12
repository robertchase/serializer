"""tests for types"""

import pytest

from serializer import types


@pytest.mark.parametrize(
    "value, is_valid, result",
    (
        (1, True, 1),
        ("1", True, 1),
        (0, True, 0),
        (True, False, None),
        ("1a", False, None),
        (None, False, None),
        ("abc", False, None),
        ("-1", True, -1),
        ("+1", True, 1),
        ("++1", False, None),
    ),
)
def test_integer(value, is_valid, result):
    """test integer operation"""
    if is_valid:
        assert types.Integer()(value) == result
    else:
        with pytest.raises(ValueError):
            types.Integer()(value)


@pytest.mark.parametrize(
    "value, minimum, maximum, is_valid",
    (
        (10, 5, 15, True),
        (10, 15, 15, False),
        (10, -15, 15, True),
        (0, -15, 15, True),
        (-1, -15, 15, True),
        (-16, -15, 15, False),
        (-10, -15, -5, True),
        (-4, -15, -5, False),
    ),
)
def test_min_max_integer(value, minimum, maximum, is_valid):
    """test integer operation with min/max"""
    type_ = types.Integer(minimum=minimum, maximum=maximum)
    if is_valid:
        assert type_(value) == value
    else:
        with pytest.raises(ValueError):
            type_(value)


@pytest.mark.parametrize(
    "value, minimum, maximum, actual",
    (
        (10, 5, 15, 10),
        (0, 5, 15, 5),
        (20, 5, 15, 15),
        (-100, -50, -15, -50),
        (-10, -50, -15, -15),
        (0, -50, -15, -15),
    ),
)
def test_min_max_force_integer(value, minimum, maximum, actual):
    """test integer operation with min/max using force"""
    type_ = types.Integer(minimum=minimum, maximum=maximum, force=True)
    assert type_(value) == actual


@pytest.mark.parametrize(
    "value, is_valid, result",
    (
        (1, True, 1),
        ("1", True, 1),
        (0, True, 0),
        (True, False, None),
        ("1a", False, None),
        (None, False, None),
        ("abc", False, None),
        ("-1", True, -1),
        ("+1", True, 1),
        ("++1", False, None),
        (".123", True, 0.123),
        ("0.123", True, 0.123),
        ("123.", True, 123.0),
        ("-123.456", True, -123.456),
    ),
)
def test_float(value, is_valid, result):
    """test float operation"""
    if is_valid:
        assert types.Float()(value) == result
    else:
        with pytest.raises(ValueError):
            types.Float()(value)


@pytest.mark.parametrize(
    "value, minimum, maximum, is_valid",
    (
        (10, 5, 15, True),
        (10, 15, 15, False),
        (15.1, 15, 15, False),
        (14.9999999999, 15, 15, False),
        (10, -15, 15, True),
        (0, -15, 15, True),
        (-1, -15, 15, True),
        (-16, -15, 15, False),
        (-15.0000000001, -15, 15, False),
        (-10, -15, -5, True),
        (-4, -15, -5, False),
        (-4.9999999999, -15, -5, False),
    ),
)
def test_min_max_float(value, minimum, maximum, is_valid):
    """test integer operation with min/max"""
    type_ = types.Float(minimum=minimum, maximum=maximum)
    if is_valid:
        assert type_(value) == value
    else:
        with pytest.raises(ValueError):
            type_(value)


@pytest.mark.parametrize(
    "value, minimum, maximum, is_valid",
    (
        (15, 15, 15, False),
        (14, 14, 16, False),
        (16, 14, 16, False),
        (15, 14, 16, True),
        (-15, -15, 15, False),
        (-14.9999999999, -15.0, 15, True),
        (0, -15.0, 15, True),
        (0, 0, 15, False),
        (0, -10, 0, False),
    ),
)
def test_exclusive_min_max_float(value, minimum, maximum, is_valid):
    """test integer operation with min/max exclusive"""
    type_ = types.Float(
        minimum=minimum, maximum=maximum, exclusive_min=True, exclusive_max=True
    )
    if is_valid:
        assert type_(value) == value
    else:
        with pytest.raises(ValueError):
            type_(value)


def test_string_ctor():
    """test String construction"""

    with pytest.raises(AttributeError):
        types.String(min_length=-1)

    with pytest.raises(AttributeError):
        types.String(min_length=5, max_length=3)


@pytest.mark.parametrize(
    "min_length,max_length,value,is_valid,result",
    (
        (0, None, "abc", True, "abc"),
        (0, None, 100, True, "100"),
        (0, None, None, True, "None"),
        (0, None, True, True, "True"),
        (0, None, False, True, "False"),
        (3, 3, "abc", True, "abc"),
        (0, 3, "abcde", False, None),
        (3, 5, "a", False, None),
    ),
)
def test_string(min_length, max_length, value, is_valid, result):
    """test String operation"""
    validator = types.String(min_length, max_length)
    if is_valid:
        assert validator(value) == result
    else:
        with pytest.raises(ValueError):
            validator(value)


@pytest.mark.parametrize(
    "value, is_valid, result",
    (
        (1, True, True),
        ("1", True, True),
        (True, True, True),
        ("true", True, True),
        ("TrUe", True, True),
        (2, False, None),
        (0, True, False),
        ("0", True, False),
        (False, True, False),
        ("false", True, False),
        ("FALse", True, False),
    ),
)
def test_boolean(value, is_valid, result):
    """test boolean operation"""
    if is_valid:
        assert types.Boolean()(value) == result
    else:
        with pytest.raises(ValueError):
            types.Boolean()(value)


@pytest.mark.parametrize(
    "value, default_offset, result",
    (
        ("2023-01-01T12:12:12.123456", None, "2023-01-01T12:12:12.123456"),
        ("2023-01-01T12:12:12.123456", "Z", "2023-01-01T12:12:12.123456+00:00"),
        ("2023-01-01T12:12:12.123456+01:00", None, "2023-01-01T12:12:12.123456+01:00"),
        ("2023-01-01T12:12:12.123456+01:00", "Z", "2023-01-01T12:12:12.123456+01:00"),
        ("2023-01-01T12:12:12.123456", "+05:00", "2023-01-01T12:12:12.123456+05:00"),
    ),
)
def test_isodatetime(value, default_offset, result):
    """Test ISODateTime operation."""
    type_ = types.ISODateTime(default_offset=default_offset)
    normal = type_(value)
    assert type_.serialize(normal) == result


# TODO: ISODate
# TODO: ISOTime
# TODO: OneOf
# TODO: SomeOf
