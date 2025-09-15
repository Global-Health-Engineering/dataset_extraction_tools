import logging
from functools import wraps
from time import time

logger = logging.getLogger(__name__)

def timing(func):
    """Decorator to measure and log function execution time."""

    @wraps(func)
    def wrap(*args, **kw):
        ts = time()
        result = func(*args, **kw)
        te = time()
        logger.info(f"func:{func.__name__!r} took: {te - ts:2.4f} sec")
        return result

    return wrap