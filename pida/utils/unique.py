import time
from random import randint
import threading

def create_unique_id():
    return '%s.%s' % (time.time(), randint(0,10000))

def counter(start=0):
    """Create a thread safe counter starting at ``start``."""

    def inc():
        """Increment the counter and return the new value."""
        inc.lock.acquire()
        inc.counter += 1
        rv = inc.counter
        inc.lock.release()
        return rv

    inc.counter = start
    inc.lock = threading.Lock()
    return inc

GLOBAL_COUNTER = counter()
