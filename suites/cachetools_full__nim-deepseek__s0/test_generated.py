import pytest
import cachetools


class TestCache:
    def test_init_negative_maxsize(self):
        with pytest.raises(ValueError):
            cachetools.Cache(-1)

    def test_init_zero_maxsize(self):
        c = cachetools.Cache(0)
        assert c.maxsize == 0
        assert c.currsize == 0
        assert len(c) == 0

    def test_setitem_zero_maxsize(self):
        c = cachetools.Cache(0)
        with pytest.raises(ValueError):
            c["a"] = 1

    def test_setitem_getitem(self):
        c = cachetools.Cache(10)
        c["a"] = 1
        assert c["a"] == 1
        assert c.currsize == 1
        assert len(c) == 1

    def test_getitem_missing(self):
        c = cachetools.Cache(10)
        with pytest.raises(KeyError):
            c["missing"]

    def test_contains(self):
        c = cachetools.Cache(10)
        assert "a" not in c
        c["a"] = 1
        assert "a" in c

    def test_delitem(self):
        c = cachetools.Cache(10)
        c["a"] = 1
        del c["a"]
        assert "a" not in c
        assert c.currsize == 0

    def test_delitem_missing(self):
        c = cachetools.Cache(10)
        with pytest.raises(KeyError):
            del c["missing"]

    def test_iter(self):
        c = cachetools.Cache(10)
        c["a"] = 1
        c["b"] = 2
        assert set(iter(c)) == {"a", "b"}

    def test_get(self):
        c = cachetools.Cache(10)
        c["a"] = 1
        assert c.get("a") == 1
        assert c.get("b") is None
        assert c.get("b", 42) == 42

    def test_pop(self):
        c = cachetools.Cache(10)
        c["a"] = 1
        assert c.pop("a") == 1
        assert "a" not in c
        assert c.pop("b", 42) == 42
        with pytest.raises(KeyError):
            c.pop("b")

    def test_setdefault(self):
        c = cachetools.Cache(10)
        assert c.setdefault("a", 1) == 1
        assert c["a"] == 1
        assert c.setdefault("a", 2) == 1

    def test_clear(self):
        c = cachetools.Cache(10)
        c["a"] = 1
        c["b"] = 2
        c.clear()
        assert len(c) == 0
        assert c.currsize == 0

    def test_eviction(self):
        c = cachetools.Cache(2)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        assert len(c) == 2
        assert c.currsize == 2

    def test_getsizeof(self):
        c = cachetools.Cache(10, getsizeof=lambda v: v)
        c["a"] = 3
        assert c.currsize == 3
        c["b"] = 5
        assert c.currsize == 8

    def test_getsizeof_too_large(self):
        c = cachetools.Cache(5, getsizeof=lambda v: v)
        with pytest.raises(ValueError):
            c["a"] = 10

    def test_getsizeof_negative(self):
        c = cachetools.Cache(5, getsizeof=lambda v: -1)
        with pytest.raises(ValueError):
            c["a"] = 1

    def test_getsizeof_update(self):
        c = cachetools.Cache(10, getsizeof=lambda v: v)
        c["a"] = 3
        c["a"] = 5
        assert c.currsize == 5

    def test_repr(self):
        c = cachetools.Cache(10)
        assert "Cache" in repr(c)
        assert "maxsize=10" in repr(c)

    def test_getsizeof_static(self):
        assert cachetools.Cache.getsizeof(42) == 1


class TestFIFOCache:
    def test_popitem_order(self):
        c = cachetools.FIFOCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        assert c.popitem() == ("a", 1)
        assert c.popitem() == ("b", 2)

    def test_popitem_empty(self):
        c = cachetools.FIFOCache(3)
        with pytest.raises(KeyError):
            c.popitem()

    def test_eviction_fifo(self):
        c = cachetools.FIFOCache(2)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        assert "a" not in c
        assert "b" in c
        assert "c" in c

    def test_update_does_not_change_order(self):
        c = cachetools.FIFOCache(3)
        c["a"] = 1
        c["b"] = 2
        c["a"] = 10
        assert c.popitem() == ("a", 10)

    def test_clear(self):
        c = cachetools.FIFOCache(3)
        c["a"] = 1
        c.clear()
        assert len(c) == 0
        with pytest.raises(KeyError):
            c.popitem()


class TestLFUCache:
    def test_popitem_empty(self):
        c = cachetools.LFUCache(3)
        with pytest.raises(KeyError):
            c.popitem()

    def test_eviction_lfu(self):
        c = cachetools.LFUCache(2)
        c["a"] = 1
        c["b"] = 2
        _ = c["a"]
        _ = c["a"]
        c["c"] = 3
        assert "a" in c
        assert "b" not in c
        assert "c" in c

    def test_popitem(self):
        c = cachetools.LFUCache(3)
        c["a"] = 1
        c["b"] = 2
        _ = c["a"]
        key, value = c.popitem()
        assert key == "b"
        assert value == 2

    def test_clear(self):
        c = cachetools.LFUCache(3)
        c["a"] = 1
        c.clear()
        assert len(c) == 0
        with pytest.raises(KeyError):
            c.popitem()

    def test_getitem_missing(self):
        c = cachetools.LFUCache(3)
        with pytest.raises(KeyError):
            c["missing"]


class TestLRUCache:
    def test_popitem_empty(self):
        c = cachetools.LRUCache(3)
        with pytest.raises(KeyError):
            c.popitem()

    def test_eviction_lru(self):
        c = cachetools.LRUCache(2)
        c["a"] = 1
        c["b"] = 2
        _ = c["a"]
        c["c"] = 3
        assert "a" in c
        assert "b" not in c
        assert "c" in c

    def test_popitem(self):
        c = cachetools.LRUCache(3)
        c["a"] = 1
        c["b"] = 2
        _ = c["a"]
        assert c.popitem() == ("b", 2)

    def test_clear(self):
        c = cachetools.LRUCache(3)
        c["a"] = 1
        c.clear()
        assert len(c) == 0
        with pytest.raises(KeyError):
            c.popitem()


class TestRRCache:
    def test_popitem_empty(self):
        c = cachetools.RRCache(3)
        with pytest.raises(KeyError):
            c.popitem()

    def test_popitem(self):
        c = cachetools.RRCache(3, choice=lambda keys: keys[0])
        c["a"] = 1
        c["b"] = 2
        assert c.popitem() == ("a", 1)

    def test_choice_property(self):
        choice = lambda keys: keys[0]
        c = cachetools.RRCache(3, choice=choice)
        assert c.choice is choice

    def test_eviction(self):
        c = cachetools.RRCache(2, choice=lambda keys: keys[0])
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        assert len(c) == 2

    def test_clear(self):
        c = cachetools.RRCache(3)
        c["a"] = 1
        c.clear()
        assert len(c) == 0
        with pytest.raises(KeyError):
            c.popitem()

    def test_delitem(self):
        c = cachetools.RRCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        del c["b"]
        assert "b" not in c
        assert len(c) == 2


class TestTTLCache:
    def test_init(self):
        c = cachetools.TTLCache(10, ttl=100)
        assert c.ttl == 100
        assert c.maxsize == 10

    def test_setitem_getitem(self):
        c = cachetools.TTLCache(10, ttl=100)
        c["a"] = 1
        assert c["a"] == 1

    def test_expiry(self):
        time = [0.0]
        c = cachetools.TTLCache(10, ttl=5, timer=lambda: time[0])
        c["a"] = 1
        assert c["a"] == 1
        time[0] = 10.0
        with pytest.raises(KeyError):
            c["a"]

    def test_contains_expired(self):
        time = [0.0]
        c = cachetools.TTLCache(10, ttl=5, timer=lambda: time[0])
        c["a"] = 1
        assert "a" in c
        time[0] = 10.0
        assert "a" not in c

    def test_expire(self):
        time = [0.0]
        c = cachetools.TTLCache(10, ttl=5, timer=lambda: time[0])
        c["a"] = 1
        c["b"] = 2
        time[0] = 10.0
        expired = c.expire()
        assert set(k for k, v in expired) == {"a", "b"}

    def test_expire_fast_path(self):
        c = cachetools.TTLCache(10, ttl=100)
        assert c.expire() == []

    def test_popitem_empty(self):
        c = cachetools.TTLCache(10, ttl=100)
        with pytest.raises(KeyError):
            c.popitem()

    def test_popitem(self):
        c = cachetools.TTLCache(10, ttl=100)
        c["a"] = 1
        c["b"] = 2
        assert c.popitem() == ("a", 1)

    def test_clear(self):
        c = cachetools.TTLCache(10, ttl=100)
        c["a"] = 1
        c.clear()
        assert len(c) == 0
        with pytest.raises(KeyError):
            c.popitem()

    def test_iter(self):
        c = cachetools.TTLCache(10, ttl=100)
        c["a"] = 1
        c["b"] = 2
        assert set(iter(c)) == {"a", "b"}

    def test_delitem_expired(self):
        time = [0.0]
        c = cachetools.TTLCache(10, ttl=5, timer=lambda: time[0])
        c["a"] = 1
        time[0] = 10.0
        with pytest.raises(KeyError):
            del c["a"]

    def test_get(self):
        c = cachetools.TTLCache(10, ttl=100)
        c["a"] = 1
        assert c.get("a") == 1
        assert c.get("b", 42) == 42

    def test_pop(self):
        c = cachetools.TTLCache(10, ttl=100)
        c["a"] = 1
        assert c.pop("a") == 1
        assert c.pop("b", 42) == 42

    def test_setdefault(self):
        c = cachetools.TTLCache(10, ttl=100)
        assert c.setdefault("a", 1) == 1
        assert c.setdefault("a", 2) == 1

    def test_currsize_expires(self):
        time = [0.0]
        c = cachetools.TTLCache(10, ttl=5, timer=lambda: time[0])
        c["a"] = 1
        assert c.currsize == 1
        time[0] = 10.0
        assert c.currsize == 0


class TestTLRUCache:
    def test_init(self):
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 100)
        assert c.maxsize == 10

    def test_setitem_getitem(self):
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 100)
        c["a"] = 1
        assert c["a"] == 1

    def test_expiry(self):
        time = [0.0]
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=lambda: time[0])
        c["a"] = 1
        assert c["a"] == 1
        time[0] = 10.0
        with pytest.raises(KeyError):
            c["a"]

    def test_contains_expired(self):
        time = [0.0]
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=lambda: time[0])
        c["a"] = 1
        assert "a" in c
        time[0] = 10.0
        assert "a" not in c

    def test_expire(self):
        time = [0.0]
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=lambda: time[0])
        c["a"] = 1
        c["b"] = 2
        time[0] = 10.0
        expired = c.expire()
        assert set(k for k, v in expired) == {"a", "b"}

    def test_expire_fast_path(self):
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 100)
        assert c.expire() == []

    def test_popitem_empty(self):
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 100)
        with pytest.raises(KeyError):
            c.popitem()

    def test_popitem(self):
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 100)
        c["a"] = 1
        c["b"] = 2
        assert c.popitem() == ("a", 1)

    def test_clear(self):
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 100)
        c["a"] = 1
        c.clear()
        assert len(c) == 0
        with pytest.raises(KeyError):
            c.popitem()

    def test_iter(self):
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 100)
        c["a"] = 1
        c["b"] = 2
        assert set(iter(c)) == {"a", "b"}

    def test_ttu_property(self):
        ttu = lambda k, v, t: t + 100
        c = cachetools.TLRUCache(10, ttu=ttu)
        assert c.ttu is ttu

    def test_setitem_already_expired(self):
        time = [0.0]
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t - 1, timer=lambda: time[0])
        c["a"] = 1
        assert "a" not in c

    def test_update_existing(self):
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 100)
        c["a"] = 1
        c["a"] = 2
        assert c["a"] == 2

    def test_delitem_expired(self):
        time = [0.0]
        c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=lambda: time[0])
        c["a"] = 1
        time[0] = 10.0
        with pytest.raises(KeyError):
            del c["a"]


class TestCached:
    def test_basic(self):
        c = cachetools.Cache(10)
        calls = [0]

        @cachetools.cached(c)
        def f(x):
            calls[0] += 1
            return x * 2

        assert f(2) == 4
        assert f(2) == 4
        assert calls[0] == 1

    def test_cache_none_deprecated(self):
        with pytest.warns(DeprecationWarning):
            @cachetools.cached(None)
            def f(x):
                return x

        assert f(1) == 1

    def test_info(self):
        c = cachetools.Cache(10)

        @cachetools.cached(c, info=True)
        def f(x):
            return x * 2

        f(2)
        f(2)
        info = f.cache_info()
        assert info.hits == 1
        assert info.misses == 1
        assert info.maxsize == 10
        assert info.currsize == 1

    def test_cache_clear(self):
        c = cachetools.Cache(10)

        @cachetools.cached(c)
        def f(x):
            return x * 2

        f(2)
        assert len(c) == 1
        f.cache_clear()
        assert len(c) == 0

    def test_cache_attribute(self):
        c = cachetools.Cache(10)

        @cachetools.cached(c)
        def f(x):
            return x

        assert f.cache is c

    def test_value_too_large(self):
        c = cachetools.Cache(1, getsizeof=lambda v: v)

        @cachetools.cached(c)
        def f(x):
            return x

        assert f(10) == 10
        assert len(c) == 0


class TestCachedMethod:
    def test_basic(self):
        class A:
            def __init__(self):
                self.cache = cachetools.Cache(10)
                self.calls = 0

            @cachetools.cachedmethod(lambda self: self.cache)
            def f(self, x):
                self.calls += 1
                return x * 2

        a = A()
        assert a.f(2) == 4
        assert a.f(2) == 4
        assert a.calls == 1

    def test_info(self):
        class A:
            def __init__(self):
                self.cache = cachetools.Cache(10)

            @cachetools.cachedmethod(lambda self: self.cache, info=True)
            def f(self, x):
                return x * 2

        a = A()
        a.f(2)
        a.f(2)
        info = a.f.cache_info()
        assert info.hits == 1
        assert info.misses == 1

    def test_cache_clear(self):
        class A:
            def __init__(self):
                self.cache = cachetools.Cache(10)

            @cachetools.cachedmethod(lambda self: self.cache)
            def f(self, x):
                return x * 2

        a = A()
        a.f(2)
        assert len(a.cache) == 1
        a.f.cache_clear()
        assert len(a.cache) == 0


class TestKeys:
    def test_hashkey_no_kwargs(self):
        k = cachetools.keys.hashkey(1, 2, 3)
        assert k == (1, 2, 3)

    def test_hashkey_with_kwargs(self):
        k1 = cachetools.keys.hashkey(1, a=2, b=3)
        k2 = cachetools.keys.hashkey(1, b=3, a=2)
        assert k1 == k2

    def test_hashkey_empty(self):
        k = cachetools.keys.hashkey()
        assert k == ()

    def test_typedkey_no_kwargs(self):
        k1 = cachetools.keys.typedkey(1)
        k2 = cachetools.keys.typedkey(1.0)
        assert k1 != k2

    def test_typedkey_with_kwargs(self):
        k1 = cachetools.keys.typedkey(a=1)
        k2 = cachetools.keys.typedkey(a=1.0)
        assert k1 != k2

    def test_typedkey_empty(self):
        k = cachetools.keys.typedkey()
        assert k == ()

    def test_methodkey(self):
        k = cachetools.keys.methodkey(object(), 1, 2)
        assert k == (1, 2)

    def test_typedmethodkey(self):
        k1 = cachetools.keys.typedmethodkey(object(), 1)
        k2 = cachetools.keys.typedmethodkey(object(), 1.0)
        assert k1 != k2


class TestFunc:
    def test_lru_cache_basic(self):
        calls = [0]

        @cachetools.func.lru_cache(maxsize=10)
        def f(x):
            calls[0] += 1
            return x * 2

        assert f(2) == 4
        assert f(2) == 4
        assert calls[0] == 1

    def test_lru_cache_none(self):
        calls = [0]

        @cachetools.func.lru_cache(maxsize=None)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_lru_cache_bare(self):
        calls = [0]

        @cachetools.func.lru_cache
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_lru_cache_typed(self):
        calls = [0]

        @cachetools.func.lru_cache(maxsize=10, typed=True)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1.0)
        assert calls[0] == 2

    def test_lru_cache_info(self):
        @cachetools.func.lru_cache(maxsize=10)
        def f(x):
            return x

        f(1)
        f(1)
        info = f.cache_info()
        assert info.hits == 1
        assert info.misses == 1
        assert info.maxsize == 10

    def test_lru_cache_clear(self):
        @cachetools.func.lru_cache(maxsize=10)
        def f(x):
            return x

        f(1)
        f.cache_clear()
        info = f.cache_info()
        assert info.hits == 0
        assert info.misses == 0

    def test_lru_cache_parameters(self):
        @cachetools.func.lru_cache(maxsize=10, typed=True)
        def f(x):
            return x

        assert f.cache_parameters() == {"maxsize": 10, "typed": True}

    def test_fifo_cache(self):
        calls = [0]

        @cachetools.func.fifo_cache(maxsize=10)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_lfu_cache(self):
        calls = [0]

        @cachetools.func.lfu_cache(maxsize=10)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_rr_cache(self):
        calls = [0]

        @cachetools.func.rr_cache(maxsize=10)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_ttl_cache(self):
        calls = [0]

        @cachetools.func.ttl_cache(maxsize=10, ttl=100)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_ttl_cache_none(self):
        calls = [0]

        @cachetools.func.ttl_cache(maxsize=None, ttl=100)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1
        assert f.cache_info().maxsize is None

    def test_fifo_cache_none(self):
        calls = [0]

        @cachetools.func.fifo_cache(maxsize=None)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_lfu_cache_none(self):
        calls = [0]

        @cachetools.func.lfu_cache(maxsize=None)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_rr_cache_none(self):
        calls = [0]

        @cachetools.func.rr_cache(maxsize=None)
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_fifo_cache_bare(self):
        calls = [0]

        @cachetools.func.fifo_cache
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_lfu_cache_bare(self):
        calls = [0]

        @cachetools.func.lfu_cache
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_rr_cache_bare(self):
        calls = [0]

        @cachetools.func.rr_cache
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1

    def test_ttl_cache_bare(self):
        calls = [0]

        @cachetools.func.ttl_cache
        def f(x):
            calls[0] += 1
            return x

        f(1)
        f(1)
        assert calls[0] == 1


class TestVersion:
    def test_version(self):
        assert isinstance(cachetools.__version__, str)
        assert cachetools.__version__

    def test_all(self):
        for name in cachetools.__all__:
            assert hasattr(cachetools, name)