import pytest
from cachetools.keys import hashkey, methodkey, typedkey


class TestHashkey:
    def test_empty_args_returns_empty_tuple(self):
        assert hashkey() == ()

    def test_single_arg(self):
        assert hashkey(1) == (1,)

    def test_multiple_args(self):
        assert hashkey(1, 2, 3) == (1, 2, 3)

    def test_no_kwargs_returns_args_only(self):
        assert hashkey(1, 2) == (1, 2)

    def test_kwargs_sorted(self):
        assert hashkey(a=1, b=2) == (("a", 1), ("b", 2))

    def test_kwargs_reverse_order_sorted(self):
        assert hashkey(b=2, a=1) == (("a", 1), ("b", 2))

    def test_args_and_kwargs(self):
        assert hashkey(1, 2, a=3, b=4) == (1, 2, ("a", 3), ("b", 4))

    def test_empty_string_arg(self):
        assert hashkey("") == ("",)

    def test_zero_arg(self):
        assert hashkey(0) == (0,)

    def test_negative_arg(self):
        assert hashkey(-1) == (-1,)

    def test_empty_collection_arg(self):
        assert hashkey([]) == ([],)

    def test_none_arg(self):
        assert hashkey(None) == (None,)

    def test_kwargs_with_none_value(self):
        assert hashkey(a=None) == (("a", None),)

    def test_kwargs_empty_string_key(self):
        assert hashkey(**{"": 1}) == (("", 1),)

    def test_returns_tuple(self):
        assert isinstance(hashkey(1, 2, a=3), tuple)

    def test_kwargs_ordering_multiple(self):
        assert hashkey(z=1, a=2, m=3) == (("a", 2), ("m", 3), ("z", 1))

    def test_duplicate_values_different_keys(self):
        assert hashkey(a=1, b=1) == (("a", 1), ("b", 1))


class TestMethodkey:
    def test_self_only(self):
        class C:
            pass

        obj = C()
        assert methodkey(obj) == (id(obj),)

    def test_self_with_args(self):
        class C:
            pass

        obj = C()
        assert methodkey(obj, 1, 2) == (id(obj), 1, 2)

    def test_self_with_kwargs(self):
        class C:
            pass

        obj = C()
        assert methodkey(obj, a=1) == (id(obj), ("a", 1))

    def test_self_with_args_and_kwargs(self):
        class C:
            pass

        obj = C()
        assert methodkey(obj, 1, b=2) == (id(obj), 1, ("b", 2))

    def test_kwargs_sorted(self):
        class C:
            pass

        obj = C()
        assert methodkey(obj, b=2, a=1) == (id(obj), ("a", 1), ("b", 2))

    def test_self_none(self):
        assert methodkey(None) == (id(None),)

    def test_self_zero(self):
        assert methodkey(0) == (id(0),)

    def test_self_empty_string(self):
        assert methodkey("") == (id(""),)

    def test_returns_tuple(self):
        class C:
            pass

        obj = C()
        assert isinstance(methodkey(obj, 1, a=2), tuple)

    def test_different_objects_different_keys(self):
        class C:
            pass

        a = C()
        b = C()
        assert methodkey(a) != methodkey(b)

    def test_same_object_same_key(self):
        class C:
            pass

        obj = C()
        assert methodkey(obj, 1) == methodkey(obj, 1)


class TestTypedkey:
    def test_empty_args(self):
        assert typedkey() == ()

    def test_single_arg(self):
        assert typedkey(1) == (1,)

    def test_multiple_args(self):
        assert typedkey(1, 2, 3) == (1, 2, 3)

    def test_kwargs_sorted(self):
        assert typedkey(a=1, b=2) == (("a", 1), ("b", 2))

    def test_kwargs_reverse_order_sorted(self):
        assert typedkey(b=2, a=1) == (("a", 1), ("b", 2))

    def test_args_and_kwargs(self):
        assert typedkey(1, a=2) == (1, ("a", 2))

    def test_empty_string_arg(self):
        assert typedkey("") == ("",)

    def test_zero_arg(self):
        assert typedkey(0) == (0,)

    def test_negative_arg(self):
        assert typedkey(-1) == (-1,)

    def test_none_arg(self):
        assert typedkey(None) == (None,)

    def test_empty_collection_arg(self):
        assert typedkey([]) == ([],)

    def test_kwargs_with_none_value(self):
        assert typedkey(a=None) == (("a", None),)

    def test_returns_tuple(self):
        assert isinstance(typedkey(1, a=2), tuple)

    def test_kwargs_ordering_multiple(self):
        assert typedkey(z=1, a=2, m=3) == (("a", 2), ("m", 3), ("z", 1))

    def test_typedkey_differs_from_hashkey_for_int_float(self):
        assert typedkey(1) != typedkey(1.0)

    def test_typedkey_same_type_same_value(self):
        assert typedkey(1) == typedkey(1)

    def test_typedkey_differs_from_hashkey_for_bool_int(self):
        assert typedkey(True) != typedkey(1)

    def test_typedkey_string_vs_bytes(self):
        assert typedkey("a") != typedkey(b"a")

    def test_typedkey_kwargs_type_sensitive(self):
        assert typedkey(a=1) != typedkey(a=1.0)

    def test_typedkey_empty_string_vs_empty_bytes(self):
        assert typedkey("") != typedkey(b"")

    def test_typedkey_zero_int_vs_zero_float(self):
        assert typedkey(0) != typedkey(0.0)

    def test_typedkey_negative_int_vs_negative_float(self):
        assert typedkey(-1) != typedkey(-1.0)

    def test_typedkey_none_vs_zero(self):
        assert typedkey(None) != typedkey(0)

    def test_typedkey_empty_tuple_vs_empty_list(self):
        assert typedkey(()) != typedkey([])

    def test_typedkey_same_value_same_type_equal(self):
        assert typedkey(1, 2, a=3) == typedkey(1, 2, a=3)

    def test_typedkey_kwargs_sorted_with_types(self):
        assert typedkey(b=2.0, a=1) == (("a", 1), ("b", 2.0))