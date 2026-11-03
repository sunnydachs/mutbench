import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from hashkey import hashkey


def test_hashkey_basic():
    assert hashkey("hello") == hashkey("hello")


def test_hashkey_different():
    assert hashkey("hello") != hashkey("world")


def test_hashkey_empty():
    assert isinstance(hashkey(""), int)


def test_hashkey_returns_int():
    assert isinstance(hashkey("test"), int)


def test_hashkey_deterministic():
    results = [hashkey("abc") for _ in range(10)]
    assert len(set(results)) == 1


def test_hashkey_unicode():
    assert isinstance(hashkey("héllo"), int)


def test_hashkey_long_string():
    assert isinstance(hashkey("a" * 10000), int)


def test_hashkey_numeric_string():
    assert isinstance(hashkey("12345"), int)


def test_hashkey_special_chars():
    assert isinstance(hashkey("!@#$%^&*()"), int)


def test_hashkey_whitespace():
    assert hashkey(" ") != hashkey("  ")