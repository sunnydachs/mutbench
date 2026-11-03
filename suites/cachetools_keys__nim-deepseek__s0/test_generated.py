import pytest

import cachetools.keys


class TestHashkey:
    def test_empty_args_kwargs(self):
        assert cachetools.keys.hashkey() == cachetools.keys.hashkey()

    def test_single_arg(self):
        assert cachetools.keys.hashkey(1) == cachetools.keys.hashkey(1)

    def test_different_args_differ(self):
        assert cachetools.keys.hashkey(1) != cachetools.keys.hashkey(2)

    def test_zero_and_one(self):
        assert cachetools.keys.hashkey(0) != cachetools.keys.hashkey(1)

    def test_negative(self):
        assert cachetools.keys.hashkey(-1) == cachetools.keys.hashkey(-1)

    def test_empty_string(self):
        assert cachetools.keys.hashkey("") == cachetools.keys.hashkey("")

    def test_empty_collection(self):
        assert cachetools.keys.hashkey([]) == cachetools.keys.hashkey([])

    def test_kwargs(self):
        assert cachetools.keys.hashkey(a=1) == cachetools.keys.hashkey(a=1)

    def test_kwargs_differ(self):
        assert cachetools.keys.hashkey(a=1) != cachetools.keys.hashkey(a=2)

    def test_kwargs_order_independent(self):
        assert cachetools.keys.hashkey(a=1, b=2) == cachetools.keys.hashkey(b=2, a=1)

    def test_args_and_kwargs(self):
        assert cachetools.keys.hashkey(1, a=2) == cachetools.keys.hashkey(1, a=2)

    def test_args_vs_kwargs_differ(self):
        assert cachetools.keys.hashkey(1) != cachetools.keys.hashkey(a=1)

    def test_unhashable_arg_raises(self):
        with pytest.raises(TypeError):
            cachetools.keys.hashkey([])

    def test_unhashable_kwarg_raises(self):
        with pytest.raises(TypeError):
            cachetools.keys.hashkey(a=[])

    def test_hashable(self):
        assert hash(cachetools.keys.hashkey(1)) == hash(cachetools.keys.hashkey(1))

    def test_usable_as_dict_key(self):
        d = {cachetools.keys.hashkey(1): "a"}
        assert d[cachetools.keys.hashkey(1)] == "a"


class TestMethodkey:
    def test_basic(self):
        assert cachetools.keys.methodkey(1) == cachetools.keys.methodkey(1)

    def test_different_self(self):
        assert cachetools.keys.methodkey(1) != cachetools.keys.methodkey(2)

    def test_with_args(self):
        assert cachetools.keys.methodkey(1, 2) == cachetools.keys.methodkey(1, 2)

    def test_with_kwargs(self):
        assert cachetools.keys.methodkey(1, a=2) == cachetools.keys.methodkey(1, a=2)

    def test_kwargs_order_independent(self):
        assert cachetools.keys.methodkey(1, a=2, b=3) == cachetools.keys.methodkey(1, b=3, a=2)

    def test_self_only(self):
        assert cachetools.keys.methodkey(0) == cachetools.keys.methodkey(0)

    def test_unhashable_self_raises(self):
        with pytest.raises(TypeError):
            cachetools.keys.methodkey([])

    def test_unhashable_arg_raises(self):
        with pytest.raises(TypeError):
            cachetools.keys.methodkey(1, [])

    def test_unhashable_kwarg_raises(self):
        with pytest.raises(TypeError):
            cachetools.keys.methodkey(1, a=[])

    def test_usable_as_dict_key(self):
        d = {cachetools.keys.methodkey(1, 2): "x"}
        assert d[cachetools.keys.methodkey(1, 2)] == "x"


class TestTypedkey:
    def test_basic(self):
        assert cachetools.keys.typedkey(1) == cachetools.keys.typedkey(1)

    def test_different_args(self):
        assert cachetools.keys.typedkey(1) != cachetools.keys.typedkey(2)

    def test_type_sensitive(self):
        assert cachetools.keys.typedkey(1) != cachetools.keys.typedkey(1.0)

    def test_bool_vs_int(self):
        assert cachetools.keys.typedkey(True) != cachetools.keys.typedkey(1)

    def test_kwargs(self):
        assert cachetools.keys.typedkey(a=1) == cachetools.keys.typedkey(a=1)

    def test_kwargs_type_sensitive(self):
        assert cachetools.keys.typedkey(a=1) != cachetools.keys.typedkey(a=1.0)

    def test_kwargs_order_independent(self):
        assert cachetools.keys.typedkey(a=1, b=2) == cachetools.keys.typedkey(b=2, a=1)

    def test_empty(self):
        assert cachetools.keys.typedkey() == cachetools.keys.typedkey()

    def test_empty_string(self):
        assert cachetools.keys.typedkey("") == cachetools.keys.typedkey("")

    def test_empty_collection(self):
        assert cachetools.keys.typedkey(()) == cachetools.keys.typedkey(())

    def test_unhashable_arg_raises(self):
        with pytest.raises(TypeError):
            cachetools.keys.typedkey([])

    def test_unhashable_kwarg_raises(self):
        with pytest.raises(TypeError):
            cachetools.keys.typedkey(a=[])

    def test_usable_as_dict_key(self):
        d = {cachetools.keys.typedkey(1): "a"}
        assert d[cachetools.keys.typedkey(1)] == "a"

    def test_hashable(self):
        assert hash(cachetools.keys.typedkey(1)) == hash(cachetools.keys.typedkey(1))