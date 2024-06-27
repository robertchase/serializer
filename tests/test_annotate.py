"""tests for field annotations

these tests are tied to implementation, particularly how __serializable__ is
used and when default values are removed from the class. if any of these things
change, the resulting behavior would be hard to debug.
"""

import serializer


class A(serializer.Serializable):  # pylint: disable=invalid-name
    """single level serializable"""

    attr_a: int
    attr_b: str = "a"


def test_one_level():
    """test default field behavior"""
    assert "attr_b" in A.__dict__
    item = A(10)
    assert item.attr_a == 10
    assert item.attr_b == "a"
    assert len(item.fields_) == 2
    assert "attr_b" not in A.__dict__  # default value removed from class


class B(serializer.Serializable):  # pylint: disable=invalid-name
    """base serializable"""

    attr_a: int
    attr_b: str = "b"


class C(B):  # pylint: disable=invalid-name
    """nested serializable"""

    attr_b: str = "c"


def test_two_level():
    """test nested serializable objects"""
    assert "attr_b" in C.__dict__  # default value present in "C"
    item = C(20)
    assert item.attr_a == 20
    assert item.attr_b == "c"
    assert hasattr(B, "attr_b")
    # default value removed from "C" but not from B
    assert "attr_b" in B.__dict__
    assert "attr_b" not in C.__dict__
    # __serializable__ added to "C" but not to "B"
    assert "__serializable__" in C.__dict__
    assert "__serializable__" not in B.__dict__

    item = B(30)
    assert item.attr_a == 30
    assert item.attr_b == "b"
    # default value removed from "B" and __serializable__ added to "B"
    assert "attr_b" not in B.__dict__
    assert "__serializable__" in B.__dict__
