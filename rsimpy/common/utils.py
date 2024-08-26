"""
Assorted functions.
"""

from collections.abc import Iterable
import numpy as np


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


@staticmethod
def _n2ijk(nijk, n):
    """Returns (i,j,k) coordinates of the n-th cell."""
    n_ = np.array(n)
    if np.any(n_ < 0):
        msg = "Cell number must be positive."
        raise ValueError(msg)

    ni, nj, nk = nijk

    if np.any(n_ > ni*nj*nk - 1):
        msg = "Cell number must be smaller than number of values - 1."
        raise ValueError(msg)

    k = (n_ // (ni * nj)) + 1
    j = ((n_ // ni) - (k - 1) * nj) + 1
    i = n_ - (k - 1) * ni * nj - (j - 1) * ni + 1

    if is_iterable_not_str(n):
        return np.array((i, j, k)).T
    return i, j, k


@staticmethod
def _ijk2n(nijk, ijk):
    """Returns cell number of the (i,j,k) cell."""
    ijk_ = np.array(ijk)
    if len(ijk_.shape) == 1:
        ijk_ = np.expand_dims(ijk_, axis=0)

    if np.any(ijk_ < 1):
        msg = "Coordinates number must be greater than or equal to 1."
        raise ValueError(msg)

    ni, nj, nk = nijk

    if np.any(ijk_[:,0] > ni) or np.any(ijk_[:,1] > nj) or np.any(ijk_[:,2] > nk):
        msg = "Coordinates number must be smaller than or equal to grid sizes."
        raise ValueError(msg)

    return (ijk_[:,2] - 1)*ni*nj + (ijk_[:,1] - 1)*ni + ijk_[:,0] - 1
