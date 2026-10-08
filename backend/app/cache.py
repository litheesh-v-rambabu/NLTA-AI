import threading
import time
from collections import OrderedDict


class TTLCache:
    """In-memory LRU cache whose entries also expire after ttl_seconds."""

    def __init__(self, max_size=10_000, ttl_seconds=3600, clock=time.monotonic):
        self._data = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                self.misses += 1
                return None
            value, expires_at = item
            if self._clock() >= expires_at:
                del self._data[key]
                self.misses += 1
                return None
            self._data.move_to_end(key)
            self.hits += 1
            return value

    def set(self, key, value):
        with self._lock:
            self._data[key] = (value, self._clock() + self._ttl)
            self._data.move_to_end(key)
            while len(self._data) > self._max_size:
                self._data.popitem(last=False)