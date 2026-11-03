import pytest
from cachetools.keys import _hash_key, _normalize_key, _make_key


@pytest.mark.parametrize("key", [None, 0, -1, 1, "a", "", [], {}, (1, 2), {"a": 1}])
def test_normalize_key(key):
    result = _normalize_key(key)
    assert isinstance(result, tuple)
    assert len(result) > 0


@pytest.mark.parametrize("key", [None, 0, -1, 1, "a", "", [], {}, (1, 2), {"a": 1}])
def test_hash_key(key):
    result = _hash_key(key)
    assert isinstance(result, int)
    assert result >= 0


@pytest.mark.parametrize("key", [None, 0, -1, 1, "a", "", [], {}, (1, 2), {"a": 1}])
def test_make_key(key):
    result = _make_key(key)
    assert isinstance(result, tuple)
    assert len(result) > 0


@pytest.mark.parametrize("key", [None, 0, -1, 1, "a", "", [], {}, (1, 2), {"a": 1}])
def test_make_key_with_hash(key):
    result = _make_key(key)
    assert isinstance(result, tuple)
    assert len(result) > 0