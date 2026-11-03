import pytest
from cachetools.keys import _hash_key, _normalize_key, _make_hashable


def test_hash_key_basic():
    key = "test"
    result = _hash_key(key)
    assert isinstance(result, int)


def test_hash_key_empty_string():
    key = ""
    result = _hash_key(key)
    assert isinstance(result, int)


def test_hash_key_negative_one():
    key = -1
    result = _hash_key(key)
    assert isinstance(result, int)


def test_hash_key_zero():
    key = 0
    result = _hash_key(key)
    assert isinstance(result, int)


def test_hash_key_none():
    key = None
    result = _hash_key(key)
    assert isinstance(result, int)


def test_normalize_key_basic():
    key = "test"
    result = _normalize_key(key)
    assert result == "test"


def test_normalize_key_empty_string():
    key = ""
    result = _normalize_key(key)
    assert result == ""


def test_normalize_key_none():
    key = None
    result = _normalize_key(key)
    assert result is None


def test_make_hashable_basic():
    obj = {"a": 1}
    result = _make_hashable(obj)
    assert isinstance(result, tuple)


def test_make_hashable_empty_dict():
    obj = {}
    result = _make_hashable(obj)
    assert isinstance(result, tuple)


def test_make_hashable_none():
    obj = None
    result = _make_hashable(obj)
    assert result is None


def test_make_hashable_list_of_dicts():
    obj = [{"a": 1}, {"b": 2}]
    result = _make_hashable(obj)
    assert isinstance(result, tuple)