import logging
from functools import wraps
from time import time
from pathlib import Path
from typing import Union, List, Set

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


def find_files(directory: Union[str, Path], extensions: Set[str], recursive: bool = True) -> List[Path]:
    """File discovery in directory given a list of allowed extensions."""
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    pattern = "**/*" if recursive else "*"
    return [
        f for f in directory.glob(pattern) 
        if f.is_file() and f.suffix.lower() in extensions
    ]