import time
from random import randint

def create_unique_id():
    return '%s.%s' % (time.time(), randint(0,10000))
