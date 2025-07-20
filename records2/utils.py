
from inspect import isclass


def isexception(obj):
    """Given an object, return a boolean indicating whether it is an instance or subclass of Exception."""
    if isinstance(obj, Exception):
        return True
    if isclass(obj) and issubclass(obj, Exception):
        return True
    return False


def _reduce_datetimes(row):
    # Placeholder for datetime reduction logic (copy from original if needed)
    return row


def print_bytes(content):
    if hasattr(content, "decode"):
        content = content.decode("utf-8")
    print(content)
