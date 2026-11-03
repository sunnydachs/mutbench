import pytest
import cachetools.keys


def test_hashed_identity():
    """Test that hashed_identity returns a hashable value for various inputs."""
    # Test with simple values
    result = cachetools.keys.hashed_identity(1)
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == 1

    # Test with string
    result = cachetools.keys.hashed_identity("hello")
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == "hello"

    # Test with None
    result = cachetools.keys.hashed_identity(None)
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] is None

    # Test with empty string
    result = cachetools.keys.hashed_identity("")
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == ""

    # Test with zero
    result = cachetools.keys.hashed_identity(0)
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == 0

    # Test with negative number
    result = cachetools.keys.hashed_identity(-1)
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == -1


def test_hashed_identity_with_kwargs():
    """Test hashed_identity with keyword arguments."""
    result = cachetools.keys.hashed_identity(1, 2, 3, a=4, b=5)
    assert isinstance(result, tuple)
    # The result should contain the positional args and sorted kwargs
    assert 1 in result
    assert 2 in result
    assert 3 in result


def test_hashed_identity_consistency():
    """Test that hashed_identity produces consistent results for same inputs."""
    result1 = cachetools.keys.hashed_identity(1, 2, 3)
    result2 = cachetools.keys.hashed_identity(1, 2, 3)
    assert result1 == result2

    result3 = cachetools.keys.hashed_identity("a", "b", "c")
    result4 = cachetools.keys.hashed_identity("a", "b", "c")
    assert result3 == result4


def test_hashed_identity_different_inputs():
    """Test that different inputs produce different results."""
    result1 = cachetools.keys.hashed_identity(1)
    result2 = cachetools.keys.hashed_identity(2)
    assert result1 != result2

    result3 = cachetools.keys.hashed_identity("a")
    result4 = cachetools.keys.hashed_identity("b")
    assert result3 != result4


def test_hashed_identity_hashable():
    """Test that the result is hashable and can be used as a dict key."""
    result = cachetools.keys.hashed_identity(1, 2, 3)
    d = {}
    d[result] = "value"
    assert d[result] == "value"


def test_hashed_identity_with_list():
    """Test that lists are handled (converted to tuples for hashability)."""
    result = cachetools.keys.hashed_identity([1, 2, 3])
    assert isinstance(result, tuple)
    # Lists should be converted to tuples
    assert (1, 2, 3) in result


def test_hashed_identity_with_dict():
    """Test that dicts are handled (converted to sorted items for hashability)."""
    result = cachetools.keys.hashed_identity({"a": 1, "b": 2})
    assert isinstance(result, tuple)


def test_hashed_identity_with_set():
    """Test that sets are handled (converted to sorted tuples for hashability)."""
    result = cachetools.keys.hashed_identity({1, 2, 3})
    assert isinstance(result, tuple)


def test_hashed_identity_with_nested_structures():
    """Test that nested structures are handled correctly."""
    result = cachetools.keys.hashed_identity([1, [2, 3]], {"a": [4, 5]})
    assert isinstance(result, tuple)


def test_hashed_identity_with_empty_collections():
    """Test with empty collections."""
    result1 = cachetools.keys.hashed_identity([])
    assert isinstance(result1, tuple)

    result2 = cachetools.keys.hashed_identity(())
    assert isinstance(result2, tuple)

    result3 = cachetools.keys.hashed_identity({})
    assert isinstance(result3, tuple)

    result4 = cachetools.keys.hashed_identity(set())
    assert isinstance(result4, tuple)


def test_hashed_identity_with_mixed_types():
    """Test with mixed types."""
    result = cachetools.keys.hashed_identity(1, "two", 3.0, None, True)
    assert isinstance(result, tuple)
    assert len(result) >= 5


def test_hashed_identity_large_values():
    """Test with large values."""
    large_int = 10**18
    result = cachetools.keys.hashed_identity(large_int)
    assert isinstance(result, tuple)
    assert large_int in result


def test_hashed_identity_float_values():
    """Test with float values."""
    result = cachetools.keys.hashed_identity(3.14)
    assert isinstance(result, tuple)
    assert 3.14 in result

    result2 = cachetools.keys.hashed_identity(0.0)
    assert isinstance(result2, tuple)
    assert 0.0 in result2

    result3 = cachetools.keys.hashed_identity(-0.0)
    assert isinstance(result3, tuple)


def test_hashed_identity_boolean_values():
    """Test with boolean values."""
    result_true = cachetools.keys.hashed_identity(True)
    result_false = cachetools.keys.hashed_identity(False)
    assert result_true != result_false


def test_hashed_identity_none_value():
    """Test with None value."""
    result = cachetools.keys.hashed_identity(None)
    assert isinstance(result, tuple)
    assert None in result


def test_hashed_identity_with_bytes():
    """Test with bytes values."""
    result = cachetools.keys.hashed_identity(b"hello")
    assert isinstance(result, tuple)
    assert b"hello" in result


def test_hashed_identity_with_frozenset():
    """Test with frozenset values."""
    result = cachetools.keys.hashed_identity(frozenset([1, 2, 3]))
    assert isinstance(result, tuple)


def test_hashed_identity_with_tuple():
    """Test with tuple values."""
    result = cachetools.keys.hashed_identity((1, 2, 3))
    assert isinstance(result, tuple)


def test_hashed_identity_order_matters_for_positional():
    """Test that order matters for positional arguments."""
    result1 = cachetools.keys.hashed_identity(1, 2)
    result2 = cachetools.keys.hashed_identity(2, 1)
    assert result1 != result2


def test_hashed_identity_kwargs_order_independent():
    """Test that kwargs order doesn't matter."""
    result1 = cachetools.keys.hashed_identity(a=1, b=2)
    result2 = cachetools.keys.hashed_identity(b=2, a=1)
    assert result1 == result2


def test_hashed_identity_with_many_args():
    """Test with many positional arguments."""
    args = list(range(100))
    result = cachetools.keys.hashed_identity(*args)
    assert isinstance(result, tuple)
    assert len(result) >= 100


def test_hashed_identity_with_many_kwargs():
    """Test with many keyword arguments."""
    kwargs = {f"key{i}": i for i in range(50)}
    result = cachetools.keys.hashed_identity(**kwargs)
    assert isinstance(result, tuple)


def test_hashed_identity_unhashable_types_converted():
    """Test that unhashable types are converted to hashable equivalents."""
    # Lists should be converted to tuples
    result1 = cachetools.keys.hashed_identity([1, 2, 3])
    result2 = cachetools.keys.hashed_identity((1, 2, 3))
    assert result1 == result2

    # Sets should be converted to sorted tuples
    result3 = cachetools.keys.hashed_identity({1, 2, 3})
    result4 = cachetools.keys.hashed_identity((1, 2, 3))
    assert result3 == result4


def test_hashed_identity_dict_order_independent():
    """Test that dict key order doesn't affect the result."""
    result1 = cachetools.keys.hashed_identity({"a": 1, "b": 2})
    result2 = cachetools.keys.hashed_identity({"b": 2, "a": 1})
    assert result1 == result2


def test_hashed_identity_set_order_independent():
    """Test that set order doesn't affect the result."""
    result1 = cachetools.keys.hashed_identity({1, 2, 3})
    result2 = cachetools.keys.hashed_identity({3, 2, 1})
    assert result1 == result2


def test_hashed_identity_can_be_used_as_cache_key():
    """Test that the result can be used as a cache key in a dictionary."""
    cache = {}
    key1 = cachetools.keys.hashed_identity(1, 2, 3)
    key2 = cachetools.keys.hashed_identity(1, 2, 3)
    key3 = cachetools.keys.hashed_identity(4, 5, 6)

    cache[key1] = "value1"
    assert cache[key2] == "value1"
    assert key3 not in cache


def test_hashed_identity_with_complex_nested_structure():
    """Test with a complex nested structure."""
    complex_data = {
        "list": [1, 2, [3, 4]],
        "dict": {"a": 1, "b": [2, 3]},
        "set": {1, 2, 3},
        "tuple": (4, 5, 6),
    }
    result = cachetools.keys.hashed_identity(complex_data)
    assert isinstance(result, tuple)


def test_hashed_identity_with_empty_args():
    """Test with no arguments."""
    result = cachetools.keys.hashed_identity()
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_none():
    """Test with a single None argument."""
    result = cachetools.keys.hashed_identity(None)
    assert isinstance(result, tuple)
    assert result == (None,)


def test_hashed_identity_with_single_empty_string():
    """Test with a single empty string argument."""
    result = cachetools.keys.hashed_identity("")
    assert isinstance(result, tuple)
    assert result == ("",)


def test_hashed_identity_with_single_zero():
    """Test with a single zero argument."""
    result = cachetools.keys.hashed_identity(0)
    assert isinstance(result, tuple)
    assert result == (0,)


def test_hashed_identity_with_single_one():
    """Test with a single one argument."""
    result = cachetools.keys.hashed_identity(1)
    assert isinstance(result, tuple)
    assert result == (1,)


def test_hashed_identity_with_single_negative_one():
    """Test with a single negative one argument."""
    result = cachetools.keys.hashed_identity(-1)
    assert isinstance(result, tuple)
    assert result == (-1,)


def test_hashed_identity_with_single_empty_list():
    """Test with a single empty list argument."""
    result = cachetools.keys.hashed_identity([])
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_empty_tuple():
    """Test with a single empty tuple argument."""
    result = cachetools.keys.hashed_identity(())
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_empty_dict():
    """Test with a single empty dict argument."""
    result = cachetools.keys.hashed_identity({})
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_empty_set():
    """Test with a single empty set argument."""
    result = cachetools.keys.hashed_identity(set())
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_empty_frozenset():
    """Test with a single empty frozenset argument."""
    result = cachetools.keys.hashed_identity(frozenset())
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_empty_bytes():
    """Test with a single empty bytes argument."""
    result = cachetools.keys.hashed_identity(b"")
    assert isinstance(result, tuple)
    assert result == (b"",)


def test_hashed_identity_with_single_true():
    """Test with a single True argument."""
    result = cachetools.keys.hashed_identity(True)
    assert isinstance(result, tuple)
    assert result == (True,)


def test_hashed_identity_with_single_false():
    """Test with a single False argument."""
    result = cachetools.keys.hashed_identity(False)
    assert isinstance(result, tuple)
    assert result == (False,)


def test_hashed_identity_with_single_nan():
    """Test with a single NaN argument."""
    import math
    result = cachetools.keys.hashed_identity(float('nan'))
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_inf():
    """Test with a single infinity argument."""
    import math
    result = cachetools.keys.hashed_identity(float('inf'))
    assert isinstance(result, tuple)

    result2 = cachetools.keys.hashed_identity(float('-inf'))
    assert isinstance(result2, tuple)


def test_hashed_identity_with_single_complex():
    """Test with a single complex number argument."""
    result = cachetools.keys.hashed_identity(1 + 2j)
    assert isinstance(result, tuple)
    assert result == (1 + 2j,)


def test_hashed_identity_with_single_decimal():
    """Test with a single Decimal argument."""
    from decimal import Decimal
    result = cachetools.keys.hashed_identity(Decimal("1.23"))
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_fractions():
    """Test with a single Fraction argument."""
    from fractions import Fraction
    result = cachetools.keys.hashed_identity(Fraction(1, 2))
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_date():
    """Test with a single date argument."""
    from datetime import date
    result = cachetools.keys.hashed_identity(date(2023, 1, 1))
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_datetime():
    """Test with a single datetime argument."""
    from datetime import datetime
    result = cachetools.keys.hashed_identity(datetime(2023, 1, 1, 12, 0, 0))
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_timedelta():
    """Test with a single timedelta argument."""
    from datetime import timedelta
    result = cachetools.keys.hashed_identity(timedelta(days=1))
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_time():
    """Test with a single time argument."""
    from datetime import time
    result = cachetools.keys.hashed_identity(time(12, 0, 0))
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_uuid():
    """Test with a single UUID argument."""
    import uuid
    result = cachetools.keys.hashed_identity(uuid.uuid4())
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_ipaddress():
    """Test with a single IP address argument."""
    import ipaddress
    result = cachetools.keys.hashed_identity(ipaddress.ip_address("192.168.1.1"))
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_path():
    """Test with a single Path argument."""
    from pathlib import Path
    result = cachetools.keys.hashed_identity(Path("/tmp/test"))
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_bytesio():
    """Test that BytesIO is not directly hashable but should be handled."""
    import io
    # BytesIO is not hashable, so this might raise an error or be converted
    try:
        result = cachetools.keys.hashed_identity(io.BytesIO(b"test"))
        assert isinstance(result, tuple)
    except TypeError:
        # If it raises TypeError, that's acceptable behavior
        pass


def test_hashed_identity_with_single_file():
    """Test that file objects are not directly hashable."""
    import io
    # File objects are not hashable
    try:
        result = cachetools.keys.hashed_identity(io.StringIO("test"))
        assert isinstance(result, tuple)
    except TypeError:
        # If it raises TypeError, that's acceptable behavior
        pass


def test_hashed_identity_with_single_function():
    """Test that functions are not directly hashable."""
    def my_func():
        pass
    try:
        result = cachetools.keys.hashed_identity(my_func)
        assert isinstance(result, tuple)
    except TypeError:
        # If it raises TypeError, that's acceptable behavior
        pass


def test_hashed_identity_with_single_lambda():
    """Test that lambdas are not directly hashable."""
    try:
        result = cachetools.keys.hashed_identity(lambda: None)
        assert isinstance(result, tuple)
    except TypeError:
        # If it raises TypeError, that's acceptable behavior
        pass


def test_hashed_identity_with_single_class():
    """Test that classes are hashable."""
    class MyClass:
        pass
    result = cachetools.keys.hashed_identity(MyClass)
    assert isinstance(result, tuple)


def test_hashed_identity_with_single_instance_of_hashable_class():
    """Test with an instance of