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
def _n2ijk(nijk, n, has_fracture=False):
    """Returns (i,j,k) coordinates of the n-th cell.

    Cell index starts from 1.
    If has_fracture is True, returns (i,j,k,element).
    'element' is 1 for matrix and 2 for fractures.
    """
    n_ = np.array(n)
    if np.any(n_ < 1):
        msg = "Cell number must be greater than zero."
        raise ValueError(msg)

    ni, nj, nk = nijk

    if has_fracture:
        f = 2
    else:
        f = 1
    if np.any(n_ > f*ni*nj*nk):
        msg = "Cell number must be smaller than number of values."
        raise ValueError(msg)

    n_ -= 1
    k = (n_ // (ni * nj)) + 1
    j = ((n_ // ni) - (k - 1) * nj) + 1
    i = n_ - (k - 1) * ni * nj - (j - 1) * ni + 1

    if not has_fracture:
        if is_iterable_not_str(n):
            return np.array((i, j, k)).T.astype(int)
        return int(i), int(j), int(k)

    element = np.where(k <= nk, 1, 2)
    k = np.where(k <= nk, k, k - nk)
    if is_iterable_not_str(n):
        return np.array((i, j, k, element)).T.astype(int)
    return int(i), int(j), int(k), int(element)


@staticmethod
def _ijk2n(nijk, ijk):
    """Returns cell number of the (i,j,k) cell.

    If has a 4th value, assumes the format (i,j,k,element).
    'element' is 1 for matrix and 2 for fractures.
    """
    ijk_ = np.array(ijk)
    if len(ijk_.shape) == 1:
        ijk_ = np.expand_dims(ijk_, axis=0)

    ni, nj, nk = nijk
    if ijk_.shape[1] == 4:
        n0 = np.where(ijk_[:,3] == 1, 0, ni*nj*nk)
        ijk_ = ijk_[:,:3].astype(int)
    else:
        n0 = np.zeros(ijk_.shape[0])

    if np.any(ijk_ < 1):
        msg = "Coordinates number must be greater than or equal to 1."
        raise ValueError(msg)

    if np.any(ijk_[:,0] > ni) or np.any(ijk_[:,1] > nj) or np.any(ijk_[:,2] > nk):
        msg = "Coordinates number must be smaller than or equal to grid sizes."
        raise ValueError(msg)

    n = (ijk_[:,2] - 1)*ni*nj + (ijk_[:,1] - 1)*ni + ijk_[:,0] + n0

    if isinstance(ijk[0], int):
        return int(n[0])
    return n.astype(int)


@staticmethod
def _is_neighbor(ijk1, ijk2):
    """Checks if two cells are neighbors."""
    ijk1 = np.array(ijk1)
    ijk2 = np.array(ijk2)
    if ijk1.shape != ijk2.shape:
        raise ValueError("Both arguments must have the same shape.")
    if len(ijk1.shape) == 1:
        return np.sum(np.abs(ijk1-ijk2)) == 1
    return np.sum(np.abs(ijk1-ijk2), axis=1) == 1
