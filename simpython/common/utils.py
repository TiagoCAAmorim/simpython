"""
Assorted functions.
"""

from collections.abc import Iterable


@staticmethod
def is_iterable(obj):
    """Checks if object is iterable."""
    return isinstance(obj, Iterable)


@staticmethod
def is_iterable_not_str(obj):
    """Checks if object is iterable and not a string."""
    return is_iterable(obj) and not isinstance(obj, str)


@staticmethod
def is_vector(obj):
    """Checks if object is a vector of int or float."""
    if is_iterable(obj):
        if len(obj) > 0:
            if isinstance(obj[0], (int, float)):
                return True
    return False
