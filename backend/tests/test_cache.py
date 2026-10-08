from app.cache import TTLCache


def test_set_and_get():
    cache = TTLCache()
    cache.set("a", "x")
    assert cache.get("a") == "x"
    assert cache.hits == 1


def test_missing_key_counts_a_miss():
    cache = TTLCache()
    assert cache.get("nope") is None
    assert cache.misses == 1


def test_least_recently_used_is_evicted():
    cache = TTLCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")  # "a" is now more recent than "b"
    cache.set("c", 3)  # over capacity: "b" goes
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_entries_expire():
    now = [1000.0]
    cache = TTLCache(ttl_seconds=60, clock=lambda: now[0])
    cache.set("a", "x")
    now[0] += 59
    assert cache.get("a") == "x"
    now[0] += 2
    assert cache.get("a") is None