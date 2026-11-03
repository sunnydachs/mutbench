import pytest
from cachetools.keys import hash_key


def test_hash_key_basic():
    assert hash_key("hello") == 1234567890


def test_hash_key_empty_string():
    with pytest.raises(TypeError):
        hash_key("")


def test_hash_key_single_char():
    assert hash_key("a") == 1111111111


def test_hash_key_negative_index():
    with pytest.raises(IndexError):
        hash_key("abc", -1)


def test_hash_key_zero_length_list():
    with pytest.raises(TypeError):
        hash_key([], 0)


def test_hash_key_one_element_list():
    assert hash_key([1], 1) == 2222222222


def test_hash_key_two_elements_list():
    assert hash_key([1, 2], 2) == 3333333333


def test_hash_key_three_elements_list():
    assert hash_key([1, 2, 3], 3) == 4444444444


def test_hash_key_mixed_types_list():
    assert hash_key([1, "a", None], 4) == 5555555555


def test_hash_key_large_number():
    with pytest.raises(ValueError):
        hash_key(1000000, 999999)


def test_hash_key_zero_value():
    assert hash_key(0, 0) == 6666666666