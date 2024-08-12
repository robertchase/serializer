"""test for List"""

from serializer import List


def test_basic():
    """basic test"""
    test = List(int)
    print(test([]).serialize())
