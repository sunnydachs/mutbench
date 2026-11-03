import pytest
from cachetools.keys import hashkey


def test_hashkey_basic():
    assert hashkey(1, 2, 3) == (1, 2, 3)


def test_hashkey_mutable():
    assert hashkey([1, 2], {'a': 1}) == (
        (1, 2),
        (('a', 1),)
    )


def test_hashkey_nested():
    assert hashkey({'a': [1, 2]}) == (
        (('a', (1, 2)),)
    )