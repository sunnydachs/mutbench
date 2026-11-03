import pytest
import cachetools


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def test_cache_maxsize_negative_raises():
    with pytest.raises(ValueError):
        cachetools.Cache(-1)


def test_cache_maxsize_zero_setitem_raises():
    c = cachetools.Cache(0)
    with pytest.raises(ValueError):
        c["a"] = 1


def test_cache_basic_set_get():
    c = cachetools.Cache(10)
    c["a"] = 1
    assert c["a"] == 1
    assert "a" in c
    assert len(c) == 1
    assert c.currsize == 1
    assert c.maxsize == 10


def test_cache_missing_raises_keyerror():
    c = cachetools.Cache(10)
    with pytest.raises(KeyError):
        c["missing"]


def test_cache_get_default():
    c = cachetools.Cache(10)
    assert c.get("x") is None
    assert c.get("x", 42) == 42
    c["x"] = 1
    assert c.get("x", 42) == 1


def test_cache_pop():
    c = cachetools.Cache(10)
    c["a"] = 1
    assert c.pop("a") == 1
    assert "a" not in c
    with pytest.raises(KeyError):
        c.pop("a")
    assert c.pop("a", 5) == 5


def test_cache_setdefault():
    c = cachetools.Cache(10)
    assert c.setdefault("a", 1) == 1
    assert c.setdefault("a", 2) == 1
    assert c["a"] == 1


def test_cache_delitem():
    c = cachetools.Cache(10)
    c["a"] = 1
    del c["a"]
    assert "a" not in c
    assert c.currsize == 0
    with pytest.raises(KeyError):
        del c["a"]


def test_cache_clear():
    c = cachetools.Cache(10)
    c["a"] = 1
    c["b"] = 2
    c.clear()
    assert len(c) == 0
    assert c.currsize == 0


def test_cache_eviction():
    c = cachetools.Cache(2)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    assert len(c) == 2
    assert c.currsize == 2


def test_cache_getsizeof():
    c = cachetools.Cache(10, getsizeof=lambda v: v)
    c["a"] = 3
    assert c.currsize == 3
    c["b"] = 4
    assert c.currsize == 7


def test_cache_getsizeof_too_large():
    c = cachetools.Cache(5, getsizeof=lambda v: v)
    with pytest.raises(ValueError):
        c["a"] = 10


def test_cache_getsizeof_negative():
    c = cachetools.Cache(5, getsizeof=lambda v: -1)
    with pytest.raises(ValueError):
        c["a"] = 1


def test_cache_getsizeof_update_existing():
    c = cachetools.Cache(10, getsizeof=lambda v: v)
    c["a"] = 3
    c["a"] = 5
    assert c.currsize == 5


def test_cache_iter():
    c = cachetools.Cache(10)
    c["a"] = 1
    c["b"] = 2
    assert set(iter(c)) == {"a", "b"}


def test_cache_repr():
    c = cachetools.Cache(10)
    assert "Cache" in repr(c)


def test_cache_getsizeof_static():
    assert cachetools.Cache.getsizeof(object()) == 1


# ---------------------------------------------------------------------------
# FIFOCache
# ---------------------------------------------------------------------------

def test_fifo_eviction_order():
    c = cachetools.FIFOCache(2)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    assert "a" not in c
    assert "b" in c
    assert "c" in c


def test_fifo_popitem():
    c = cachetools.FIFOCache(3)
    c["a"] = 1
    c["b"] = 2
    assert c.popitem() == ("a", 1)
    assert "a" not in c


def test_fifo_popitem_empty():
    c = cachetools.FIFOCache(3)
    with pytest.raises(KeyError):
        c.popitem()


def test_fifo_clear():
    c = cachetools.FIFOCache(3)
    c["a"] = 1
    c.clear()
    assert len(c) == 0
    with pytest.raises(KeyError):
        c.popitem()


def test_fifo_update_existing_keeps_order():
    c = cachetools.FIFOCache(2)
    c["a"] = 1
    c["b"] = 2
    c["a"] = 10
    c["c"] = 3
    # "a" was updated, so it moved to end; "b" should be evicted
    assert "b" not in c
    assert c["a"] == 10


# ---------------------------------------------------------------------------
# LFUCache
# ---------------------------------------------------------------------------

def test_lfu_eviction():
    c = cachetools.LFUCache(2)
    c["a"] = 1
    c["b"] = 2
    _ = c["a"]
    c["c"] = 3
    assert "b" not in c
    assert "a" in c
    assert "c" in c


def test_lfu_popitem_empty():
    c = cachetools.LFUCache(2)
    with pytest.raises(KeyError):
        c.popitem()


def test_lfu_popitem():
    c = cachetools.LFUCache(3)
    c["a"] = 1
    c["b"] = 2
    _ = c["a"]
    k, v = c.popitem()
    assert k == "b"
    assert v == 2


def test_lfu_clear():
    c = cachetools.LFUCache(3)
    c["a"] = 1
    c.clear()
    assert len(c) == 0
    with pytest.raises(KeyError):
        c.popitem()


def test_lfu_delitem():
    c = cachetools.LFUCache(3)
    c["a"] = 1
    del c["a"]
    assert "a" not in c


# ---------------------------------------------------------------------------
# LRUCache
# ---------------------------------------------------------------------------

def test_lru_eviction():
    c = cachetools.LRUCache(2)
    c["a"] = 1
    c["b"] = 2
    _ = c["a"]
    c["c"] = 3
    assert "b" not in c
    assert "a" in c
    assert "c" in c


def test_lru_popitem():
    c = cachetools.LRUCache(3)
    c["a"] = 1
    c["b"] = 2
    _ = c["a"]
    assert c.popitem() == ("b", 2)


def test_lru_popitem_empty():
    c = cachetools.LRUCache(3)
    with pytest.raises(KeyError):
        c.popitem()


def test_lru_clear():
    c = cachetools.LRUCache(3)
    c["a"] = 1
    c.clear()
    assert len(c) == 0


# ---------------------------------------------------------------------------
# RRCache
# ---------------------------------------------------------------------------

def test_rr_choice_property():
    def choice(seq):
        return seq[0]

    c = cachetools.RRCache(3, choice=choice)
    assert c.choice is choice


def test_rr_popitem():
    c = cachetools.RRCache(3, choice=lambda seq: seq[0])
    c["a"] = 1
    c["b"] = 2
    assert c.popitem() == ("a", 1)


def test_rr_popitem_empty():
    c = cachetools.RRCache(3)
    with pytest.raises(KeyError):
        c.popitem()


def test_rr_delitem_swap():
    c = cachetools.RRCache(3, choice=lambda seq: seq[0])
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    del c["a"]
    assert "a" not in c
    assert c.popitem() == ("c", 3)


def test_rr_clear():
    c = cachetools.RRCache(3)
    c["a"] = 1
    c.clear()
    assert len(c) == 0
    with pytest.raises(KeyError):
        c.popitem()


# ---------------------------------------------------------------------------
# TTLCache
# ---------------------------------------------------------------------------

class _FakeTimer:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_ttl_basic():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    c["a"] = 1
    assert c["a"] == 1
    assert c.ttl == 5


def test_ttl_expiry():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    c["a"] = 1
    timer.t = 10
    assert "a" not in c
    with pytest.raises(KeyError):
        c["a"]


def test_ttl_expire_returns_pairs():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    c["a"] = 1
    c["b"] = 2
    timer.t = 10
    expired = c.expire()
    assert set(expired) == {("a", 1), ("b", 2)}


def test_ttl_expire_fast_path():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    c["a"] = 1
    assert c.expire() == []


def test_ttl_popitem_empty():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    with pytest.raises(KeyError):
        c.popitem()


def test_ttl_popitem():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    c["a"] = 1
    c["b"] = 2
    assert c.popitem() == ("a", 1)


def test_ttl_clear():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    c["a"] = 1
    c.clear()
    assert len(c) == 0


def test_ttl_delitem_expired_raises():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    c["a"] = 1
    timer.t = 10
    with pytest.raises(KeyError):
        del c["a"]


def test_ttl_iter_skips_expired():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    c["a"] = 1
    timer.t = 3
    c["b"] = 2
    timer.t = 6
    assert list(iter(c)) == ["b"]


def test_ttl_timer_property():
    timer = _FakeTimer()
    c = cachetools.TTLCache(10, ttl=5, timer=timer)
    assert c.timer is not None


# ---------------------------------------------------------------------------
# TLRUCache
# ---------------------------------------------------------------------------

def test_tlru_basic():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=timer)
    c["a"] = 1
    assert c["a"] == 1
    assert c.ttu is not None


def test_tlru_expiry():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=timer)
    c["a"] = 1
    timer.t = 10
    assert "a" not in c
    with pytest.raises(KeyError):
        c["a"]


def test_tlru_expire_returns_pairs():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=timer)
    c["a"] = 1
    timer.t = 10
    expired = c.expire()
    assert expired == [("a", 1)]


def test_tlru_expire_fast_path():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=timer)
    c["a"] = 1
    assert c.expire() == []


def test_tlru_popitem_empty():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=timer)
    with pytest.raises(KeyError):
        c.popitem()


def test_tlru_popitem():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=timer)
    c["a"] = 1
    c["b"] = 2
    assert c.popitem() == ("a", 1)


def test_tlru_clear():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=timer)
    c["a"] = 1
    c.clear()
    assert len(c) == 0


def test_tlru_setitem_already_expired_removes():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t - 1, timer=timer)
    c["a"] = 1
    assert "a" not in c


def test_tlru_delitem_expired_raises():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=timer)
    c["a"] = 1
    timer.t = 10
    with pytest.raises(KeyError):
        del c["a"]


def test_tlru_iter_skips_expired():
    timer = _FakeTimer()
    c = cachetools.TLRUCache(10, ttu=lambda k, v, t: t + 5, timer=timer)
    c["a"] = 1
    timer.t = 3
    c["b"] = 2
    timer.t = 6
    assert list(iter(c)) == ["b"]


# ---------------------------------------------------------------------------
# keys
# ---------------------------------------------------------------------------

def test_hashkey_no_kwargs():
    k = cachetools.keys.hashkey(1, 2)
    assert k == (1, 2)


def test_hashkey_kwargs():
    k = cachetools.keys.hashkey(1, b=2, a=3)
    assert k == (1, cachetools.keys._kwmark, ("a", 3), ("b", 2))


def test_hashkey_equality():
    assert cachetools.keys.hashkey(1, a=2) == cachetools.keys.hashkey(1, a=2)


def test_methodkey():
    k = cachetools.keys.methodkey(object(), 1, 2)
    assert k == (1, 2)


def test_typedkey_no_kwargs():
    k = cachetools.keys.typedkey(1, 2)
    assert k == (1, 2, int, int)


def test_typedkey_kwargs():
    k = cachetools.keys.typedkey(1, a=2)
    assert k == (1, cachetools.keys._kwmark, ("a", 2), int, int)


def test_typedkey_distinguishes_types():
    assert cachetools.keys.typedkey(1) != cachetools.keys.typedkey(1.0)


def test_typedmethodkey():
    k = cachetools.keys.typedmethodkey(object(), 1)
    assert k == (1, int)


# ---------------------------------------------------------------------------
# cached
# ---------------------------------------------------------------------------

def test_cached_basic():
    calls = []

    @cachetools.cached(cachetools.Cache(10))
    def f(x):
        calls.append(x)
        return x * 2

    assert f(3) == 6
    assert f(3) == 6
    assert calls == [3]


def test_cached_info():
    @cachetools.cached(cachetools.Cache(10), info=True)
    def f(x):
        return x

    f(1)
    f(1)
    f(2)
    info = f.cache_info()
    assert info.hits == 1
    assert info.misses == 2
    assert info.maxsize == 10


def test_cached_info_mapping():
    @cachetools.cached({}, info=True)
    def f(x):
        return x

    f(1)
    info = f.cache_info()
    assert info.maxsize is None


def test_cached_clear():
    @cachetools.cached(cachetools.Cache(10), info=True)
    def f(x):
        return x

    f(1)
    f.cache_clear()
    info = f.cache_info()
    assert info.hits == 0
    assert info.misses == 0


def test_cached_none_deprecated():
    with pytest.warns(DeprecationWarning):
        @cachetools.cached(None)
        def f(x):
            return x

    assert f(1) == 1


def test_cached_lock():
    import threading

    lock = threading.Lock()

    @cachetools.cached(cachetools.Cache(10), lock=lock)
    def f(x):
        return x * 2

    assert f(3) == 6
    assert f(3) == 6


def test_cached_condition():
    import threading

    cond = threading.Condition()

    @cachetools.cached(cachetools.Cache(10), condition=cond)
    def f(x):
        return x * 2

    assert f(3) == 6
    assert f(3) == 6


def test_cached_value_too_large():
    @cachetools.cached(cachetools.Cache(0))
    def f(x):
        return x

    assert f(1) == 1
    assert f(1) == 1


# ---------------------------------------------------------------------------
# cachedmethod
# ---------------------------------------------------------------------------

def test_cachedmethod_basic():
    class A:
        def __init__(self):
            self.cache = cachetools.Cache(10)
            self.calls = 0

        @cachetools.cachedmethod(lambda self: self.cache)
        def f(self, x):
            self.calls += 1
            return x * 2

    a = A()
    assert a.f(3) == 6
    assert a.f(3) == 6
    assert a.calls == 1


def test_cachedmethod_info():
    class A:
        def __init__(self):
            self.cache = cachetools.Cache(10)

        @cachetools.cachedmethod(lambda self: self.cache, info=True)
        def f(self, x):
            return x

    a = A()
    a.f(1)
    a.f(1)
    info = a.f.cache_info()
    assert info.hits == 1
    assert info.misses == 1


def test_cachedmethod_clear():
    class A:
        def __init__(self):
            self.cache = cachetools.Cache(10)

        @cachetools.cachedmethod(lambda self: self.cache, info=True)
        def f(self, x):
            return x

    a = A()
    a.f(1)
    a.f.cache_clear()
    info = a.f.cache_info()
    assert info.hits == 0
    assert info.misses == 0


def test_cachedmethod_lock():
    import threading

    class A:
        def __init__(self):
            self.cache = cachetools.Cache(10)
            self.lock = threading.Lock()

        @cachetools.cachedmethod(lambda self: self.cache, lock=lambda self: self.lock)
        def f(self, x):
            return x * 2

    a = A()
    assert a.f(3) == 6
    assert a.f(3) == 6


def test_cachedmethod_condition():
    import threading

    class A:
        def __init__(self):
            self.cache = cachetools.Cache(10)
            self.cond = threading.Condition()

        @cachetools.cachedmethod(
            lambda self: self.cache, condition=lambda self: self.cond
        )
        def f(self, x):
            return x * 2

    a = A()
    assert a.f(3) == 6
    assert a.f(3) == 6


# ---------------------------------------------------------------------------
# func decorators
# ---------------------------------------------------------------------------

def test_lru_cache_decorator():
    calls = []

    @cachetools.func.lru_cache(maxsize=2)
    def f(x):
        calls.append(x)
        return x * 2

    assert f(1) == 2
    assert f(1) == 2
    assert calls == [1]
    assert f.cache_parameters() == {"maxsize": 2, "typed": False}


def test_lru_cache_none_maxsize():
    @cachetools.func.lru_cache(maxsize=None)
    def f(x):
        return x

    assert f(1) == 1
    assert f(1) == 1
    assert f.cache_parameters() == {"maxsize": None, "typed": False}


def test_lru_cache_bare():
    @cachetools.func.lru_cache
    def f(x):
        return x * 2

    assert f(3) == 6
    assert f(3) == 6


def test_lru_cache_typed():
    @cachetools.func.lru_cache(maxsize=10, typed=True)
    def f(x):
        return x

    assert f(1) == 1
    assert f(1.0) == 1.0
    info = f.cache_info()
    assert info.misses == 2


def test_fifo_cache_decorator():
    @cachetools.func.fifo_cache(maxsize=2)
    def f(x):
        return x

    assert f(1) == 1
    assert f(1) == 1


def test_lfu_cache_decorator():
    @cachetools.func.lfu_cache(maxsize=2)
    def f(x):
        return x

    assert f(1) == 1
    assert f(1) == 1


def test_rr_cache_decorator():
    @cachetools.func.rr_cache(maxsize=2)
    def f(x):
        return x

    assert f(1) == 1
    assert f(1) == 1


def test_ttl_cache_decorator():
    @cachetools.func.ttl_cache(maxsize=2, ttl=100)
    def f(x):
        return x

    assert f(1) == 1
    assert f(1) == 1


def test_ttl_cache_none_maxsize():
    @cachetools.func.ttl_cache(maxsize=None, ttl=100)
    def f(x):
        return x

    assert f(1) == 1
    assert f.cache_parameters() == {"maxsize": None, "typed": False}


def test_ttl_cache_bare():
    @cachetools.func.ttl_cache
    def f(x):
        return x * 2

    assert f(3) == 6


def test_fifo_cache_none_maxsize():
    @cachetools.func.fifo_cache(maxsize=None)
    def f(x):
        return x

    assert f(1) == 1
    assert f.cache_parameters() == {"maxsize": None, "typed": False}


def test_lfu_cache_none_maxsize():
    @cachetools.func.lfu_cache(maxsize=None)
    def f(x):
        return x

    assert f(1) == 1


def test_rr_cache_none_maxsize():
    @cachetools.func.rr_cache(maxsize=None)
    def f(x):
        return x

    assert f(1) == 1


def test_fifo_cache_bare():
    @cachetools.func.fifo_cache
    def f(x):
        return x

    assert f(1) == 1


def test_lfu_cache_bare():
    @cachetools.func.lfu_cache
    def f(x):
        return x

    assert f(1) == 1


def test_rr_cache_bare():
    @cachetools.func.rr_cache
    def f(x):
        return x

    assert f(1) == 1


# ---------------------------------------------------------------------------
# __all__ / version
# ---------------------------------------------------------------------------

def test_all_exports():
    for name in cachetools.__all__:
        assert hasattr(cachetools, name)


def test_version():
    assert isinstance(cachetools.__version__, str)
    assert cachetools.__version__