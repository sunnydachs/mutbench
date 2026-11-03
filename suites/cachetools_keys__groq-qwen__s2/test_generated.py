import pytest
import cachetools.keys


def test_hashed_returns_tuple():
    result = cachetools.keys.hashed(1, 2, 3)
    assert isinstance(result, tuple)
    assert len(result) == 3


def test_hashed_with_no_args():
    result = cachetools.keys.hashed()
    assert isinstance(result, tuple)
    assert len(result) == 0


def test_hashed_with_single_arg():
    result = cachetools.keys.hashed(42)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_string():
    result = cachetools.keys.hashed("hello")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_none():
    result = cachetools.keys.hashed(None)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_list():
    result = cachetools.keys.hashed([1, 2, 3])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_dict():
    result = cachetools.keys.hashed({"a": 1})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_empty_string():
    result = cachetools.keys.hashed("")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_zero():
    result = cachetools.keys.hashed(0)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_negative_number():
    result = cachetools.keys.hashed(-1)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_float():
    result = cachetools.keys.hashed(3.14)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_boolean():
    result = cachetools.keys.hashed(True)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_tuple():
    result = cachetools.keys.hashed((1, 2))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_set():
    result = cachetools.keys.hashed({1, 2, 3})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_empty_list():
    result = cachetools.keys.hashed([])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_empty_dict():
    result = cachetools.keys.hashed({})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_empty_set():
    result = cachetools.keys.hashed(set())
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_empty_tuple():
    result = cachetools.keys.hashed(())
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_multiple_args():
    result = cachetools.keys.hashed(1, "two", 3.0, None, [4])
    assert isinstance(result, tuple)
    assert len(result) == 5


def test_hashed_result_is_hashable():
    result = cachetools.keys.hashed(1, 2, 3)
    try:
        hash(result)
    except TypeError:
        pytest.fail("hashed() result should be hashable")


def test_hashed_different_args_different_results():
    result1 = cachetools.keys.hashed(1, 2)
    result2 = cachetools.keys.hashed(2, 1)
    assert result1 != result2


def test_hashed_same_args_same_result():
    result1 = cachetools.keys.hashed(1, 2, 3)
    result2 = cachetools.keys.hashed(1, 2, 3)
    assert result1 == result2


def test_hashed_with_large_number():
    result = cachetools.keys.hashed(10**18)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_small_number():
    result = cachetools.keys.hashed(10**-18)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_nested_structure():
    result = cachetools.keys.hashed([1, [2, [3]]])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_bytes():
    result = cachetools.keys.hashed(b"hello")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_empty_bytes():
    result = cachetools.keys.hashed(b"")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_complex():
    result = cachetools.keys.hashed(1 + 2j)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_frozenset():
    result = cachetools.keys.hashed(frozenset([1, 2, 3]))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_empty_frozenset():
    result = cachetools.keys.hashed(frozenset())
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_many_args():
    args = list(range(100))
    result = cachetools.keys.hashed(*args)
    assert isinstance(result, tuple)
    assert len(result) == 100


def test_hashed_result_elements_are_hashable():
    result = cachetools.keys.hashed(1, 2, 3)
    for elem in result:
        try:
            hash(elem)
        except TypeError:
            pytest.fail("Each element in hashed() result should be hashable")


def test_hashed_with_mixed_types():
    result = cachetools.keys.hashed(1, "two", 3.0, None, True, [4], (5, 6), {7: 8}, {9, 10})
    assert isinstance(result, tuple)
    assert len(result) == 9


def test_hashed_with_unicode_string():
    result = cachetools.keys.hashed("héllo wörld")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_long_string():
    long_str = "a" * 10000
    result = cachetools.keys.hashed(long_str)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_nested_dict():
    result = cachetools.keys.hashed({"a": {"b": {"c": 1}}})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_nested_list():
    result = cachetools.keys.hashed([[[[1]]]])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_mixed_nested():
    result = cachetools.keys.hashed({"a": [1, {"b": (2, 3)}]})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_empty_nested():
    result = cachetools.keys.hashed({"a": []})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_none_in_list():
    result = cachetools.keys.hashed([None, None, None])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_zero_length_string():
    result = cachetools.keys.hashed("")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_whitespace_string():
    result = cachetools.keys.hashed("   ")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_special_chars():
    result = cachetools.keys.hashed("!@#$%^&*()")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_newline_string():
    result = cachetools.keys.hashed("line1\nline2")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_tab_string():
    result = cachetools.keys.hashed("col1\tcol2")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_null_byte_string():
    result = cachetools.keys.hashed("a\x00b")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_infinity():
    result = cachetools.keys.hashed(float("inf"))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_negative_infinity():
    result = cachetools.keys.hashed(float("-inf"))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_nan():
    result = cachetools.keys.hashed(float("nan"))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_max_int():
    result = cachetools.keys.hashed(2**63 - 1)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_min_int():
    result = cachetools.keys.hashed(-(2**63))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_very_large_float():
    result = cachetools.keys.hashed(1e308)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_very_small_float():
    result = cachetools.keys.hashed(1e-308)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_complex_zero():
    result = cachetools.keys.hashed(0j)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_complex_pure_real():
    result = cachetools.keys.hashed(5 + 0j)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_complex_pure_imaginary():
    result = cachetools.keys.hashed(0 + 5j)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_bytes_empty():
    result = cachetools.keys.hashed(b"")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_bytes_long():
    result = cachetools.keys.hashed(b"a" * 1000)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_bytes_special():
    result = cachetools.keys.hashed(b"\x00\x01\x02")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_frozenset_empty():
    result = cachetools.keys.hashed(frozenset())
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_frozenset_single():
    result = cachetools.keys.hashed(frozenset([1]))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_frozenset_multiple():
    result = cachetools.keys.hashed(frozenset([1, 2, 3]))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_tuple_empty():
    result = cachetools.keys.hashed(())
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_tuple_single():
    result = cachetools.keys.hashed((1,))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_tuple_multiple():
    result = cachetools.keys.hashed((1, 2, 3))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_list_empty():
    result = cachetools.keys.hashed([])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_list_single():
    result = cachetools.keys.hashed([1])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_list_multiple():
    result = cachetools.keys.hashed([1, 2, 3])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_dict_empty():
    result = cachetools.keys.hashed({})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_dict_single():
    result = cachetools.keys.hashed({"a": 1})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_dict_multiple():
    result = cachetools.keys.hashed({"a": 1, "b": 2})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_set_empty():
    result = cachetools.keys.hashed(set())
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_set_single():
    result = cachetools.keys.hashed({1})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_set_multiple():
    result = cachetools.keys.hashed({1, 2, 3})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_bool_true():
    result = cachetools.keys.hashed(True)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_bool_false():
    result = cachetools.keys.hashed(False)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_none_only():
    result = cachetools.keys.hashed(None)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_multiple_none():
    result = cachetools.keys.hashed(None, None, None)
    assert isinstance(result, tuple)
    assert len(result) == 3


def test_hashed_with_zero_and_one():
    result = cachetools.keys.hashed(0, 1)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_hashed_with_negative_and_positive():
    result = cachetools.keys.hashed(-1, 1)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_hashed_with_float_zero():
    result = cachetools.keys.hashed(0.0)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_float_negative_zero():
    result = cachetools.keys.hashed(-0.0)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_int_zero():
    result = cachetools.keys.hashed(0)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_int_one():
    result = cachetools.keys.hashed(1)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_int_negative_one():
    result = cachetools.keys.hashed(-1)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_string_single_char():
    result = cachetools.keys.hashed("a")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_string_multiple_chars():
    result = cachetools.keys.hashed("abc")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_string_unicode_single():
    result = cachetools.keys.hashed("é")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_string_unicode_multiple():
    result = cachetools.keys.hashed("éàü")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_bytes_single():
    result = cachetools.keys.hashed(b"a")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_bytes_multiple():
    result = cachetools.keys.hashed(b"abc")
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_frozenset_single_element():
    result = cachetools.keys.hashed(frozenset([1]))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_frozenset_multiple_elements():
    result = cachetools.keys.hashed(frozenset([1, 2, 3]))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_tuple_single_element():
    result = cachetools.keys.hashed((1,))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_tuple_multiple_elements():
    result = cachetools.keys.hashed((1, 2, 3))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_list_single_element():
    result = cachetools.keys.hashed([1])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_list_multiple_elements():
    result = cachetools.keys.hashed([1, 2, 3])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_dict_single_entry():
    result = cachetools.keys.hashed({"a": 1})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_dict_multiple_entries():
    result = cachetools.keys.hashed({"a": 1, "b": 2})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_set_single_element():
    result = cachetools.keys.hashed({1})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_set_multiple_elements():
    result = cachetools.keys.hashed({1, 2, 3})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_complex_single():
    result = cachetools.keys.hashed(1 + 2j)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_complex_zero_real():
    result = cachetools.keys.hashed(0 + 2j)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_complex_zero_imag():
    result = cachetools.keys.hashed(1 + 0j)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_complex_both_zero():
    result = cachetools.keys.hashed(0 + 0j)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_float_large():
    result = cachetools.keys.hashed(1e100)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_float_small():
    result = cachetools.keys.hashed(1e-100)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_float_negative_large():
    result = cachetools.keys.hashed(-1e100)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_float_negative_small():
    result = cachetools.keys.hashed(-1e-100)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_int_large():
    result = cachetools.keys.hashed(10**100)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_int_negative_large():
    result = cachetools.keys.hashed(-(10**100))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_string_very_long():
    result = cachetools.keys.hashed("a" * 100000)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_bytes_very_long():
    result = cachetools.keys.hashed(b"a" * 100000)
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_list_very_long():
    result = cachetools.keys.hashed(list(range(10000)))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_dict_very_long():
    result = cachetools.keys.hashed({i: i for i in range(10000)})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_set_very_long():
    result = cachetools.keys.hashed(set(range(10000)))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_frozenset_very_long():
    result = cachetools.keys.hashed(frozenset(range(10000)))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_tuple_very_long():
    result = cachetools.keys.hashed(tuple(range(10000)))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_nested_very_deep():
    result = cachetools.keys.hashed([[[[[[[[[[1]]]]]]]]]])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_nested_very_wide():
    result = cachetools.keys.hashed([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_mixed_nested_deep():
    result = cachetools.keys.hashed({"a": [1, {"b": (2, 3), "c": [4, 5]}]})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_mixed_nested_wide():
    result = cachetools.keys.hashed([1, "two", 3.0, None, True, [4], (5, 6), {7: 8}, {9, 10}])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_all_types():
    result = cachetools.keys.hashed(
        1, "two", 3.0, None, True, [4], (5, 6), {7: 8}, {9, 10}, b"eleven", 12 + 13j
    )
    assert isinstance(result, tuple)
    assert len(result) == 11


def test_hashed_with_empty_collections():
    result = cachetools.keys.hashed([], {}, set(), frozenset(), (), "")
    assert isinstance(result, tuple)
    assert len(result) == 6


def test_hashed_with_none_and_empty_collections():
    result = cachetools.keys.hashed(None, [], {}, set(), frozenset(), (), "")
    assert isinstance(result, tuple)
    assert len(result) == 7


def test_hashed_with_all_empty():
    result = cachetools.keys.hashed()
    assert isinstance(result, tuple)
    assert len(result) == 0


def test_hashed_with_single_empty_collection():
    result = cachetools.keys.hashed([])
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_single_empty_dict():
    result = cachetools.keys.hashed({})
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_single_empty_set():
    result = cachetools.keys.hashed(set())
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_hashed_with_single_empty_frozenset():
    result = cachetools.keys.hashed(frozenset())
    assert isinstance(result, tuple)
    assert len(result) == 1