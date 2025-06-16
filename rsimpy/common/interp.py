"""
Interpolation functions.
"""

import numpy as np
from scipy.interpolate import RegularGridInterpolator


@staticmethod
def interp_extrap(x, y, new_x, extrap=True):
    """
    Perform linear interpolation and extrapolation.

    Extrapolates using the two lowest or two largest points if new_x is outside x range.

    Parameters
    ----------
    x : array_like
        Known x-coordinates.
    y : array_like
        Known y-coordinates corresponding to x.
    new_x : array_like
        New x-coordinates where interpolation/extrapolation is desired.
    extrap : bool, optional
        If True, extrapolate outside the range of x. Default is True.

    Returns
    -------
    y_interp : ndarray
        Interpolated or extrapolated y-coordinates corresponding to new_x.
    """
    x = np.asarray(x)
    y = np.asarray(y)
    new_x = np.asarray(new_x)
    y_interp = np.interp(new_x, x, y)
    if not extrap:
        return y_interp

    below = new_x < x[0]
    if np.any(below):
        slope = (y[1] - y[0]) / (x[1] - x[0])
        y_interp[below] = y[0] + slope * (new_x[below] - x[0])

    above = new_x > x[-1]
    if np.any(above):
        slope = (y[-1] - y[-2]) / (x[-1] - x[-2])
        y_interp[above] = y[-1] + slope * (new_x[above] - x[-1])
    return y_interp


@staticmethod
def alt_interp1d(x, y, x_new, x_inversion=-np.inf, inverse_smaller=True, extrap=True):
    """
    1D interpolation part linear, part linear to the inverse.

    Parameters
    ----------
    x : array_like
        The x-coordinates of the data points.
    y : array_like
        The y-coordinates of the data points.
    x_new : array_like
        The x-coordinates where the interpolation is evaluated.
    x_inversion : float, optional
        The x-coordinate where the interpolation switches from linear to inverse.
        Default is -np.inf, meaning no switch.
    inverse_smaller : bool, optional
        If True, the inverse interpolation is applied for x values smaller than x_inversion.
        If False, it is applied for x values larger than x_inversion.
        Default is True.
    extrap : bool, optional
        If True, extrapolation is performed for x values outside the range of x.
        If False, values outside the range will not be extrapolated.
        Default is True.
    Returns
    -------
    y_interp : array_like
        The interpolated y-coordinates corresponding to the input x values.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    if inverse_smaller:
        mask = x_new < x_inversion
    else:
        mask = x_new > x_inversion

    y_interp = np.zeros_like(x_new)
    y_interp[mask] = 1/interp_extrap(x, 1/y, x_new[mask], extrap=extrap)
    y_interp[~mask] = interp_extrap(x, y, x_new[~mask], extrap=extrap)

    return y_interp


@staticmethod
def interp2d(x, y, new_x, interpolator=None, extrap=True):
    """
    Control extrapolation behavior for 2D interpolation.

    Parameters
    ----------
    x : list of array_like
        Known x-coordinates for each dimension.
    y : array_like
        Known y-coordinates corresponding to the grid defined by x.
    new_x : array_like
        New x-coordinates where interpolation/extrapolation is desired.
    interpolator : RegularGridInterpolator, optional
        An instance of RegularGridInterpolator to use for interpolation.
        If None, a new interpolator will be created.
    extrap : bool, optional
        If True, extrapolate outside the range of x. An array of booleans
        can also be provided to specify extrapolation for each dimension.
        Default is True.
    Returns
    -------
    y_interp : ndarray
        Interpolated or extrapolated y-coordinates corresponding to new_x.
    """
    x_ = []
    for xi in x:
        x_.append(np.asarray(xi))
    y = np.asarray(y)

    extrap = np.asarray(extrap, dtype=bool)
    if extrap.ndim == 0:
        extrap = np.full(len(x_), extrap, dtype=bool)
    elif extrap.shape[0] == 1:
        extrap = np.full(len(x_), extrap, dtype=bool)

    new_x = np.asarray(new_x).copy()

    if interpolator is None:
        interpolator = RegularGridInterpolator(x_, y, bounds_error=False, fill_value=None)

    for i in range(new_x.shape[1]):
        if not extrap[i]:
            below = new_x[:,i] < x_[i][0]
            if np.any(below):
                new_x[below,i] = x_[i][0]
            above = new_x[:,i] > x_[i][-1]
            if np.any(above):
                new_x[above,i] = x_[i][-1]

    return interpolator(new_x)



def main():
    """Example usage"""

    import matplotlib.pyplot as plt # pylint: disable=import-outside-toplevel

    x = np.linspace(1, 10, 100)
    y = 1/x
    x_new = np.linspace(-10, 200, 5000)
    y_linear = alt_interp1d(x, y, x_new, x_inversion=-np.inf, inverse_smaller=True, extrap=True)
    y_inv = alt_interp1d(x, y, x_new, x_inversion=-np.inf, inverse_smaller=False, extrap=True)
    y_alt = alt_interp1d(x, y, x_new, x_inversion=x.mean(), inverse_smaller=False, extrap=True)

    plt.plot(x, y, 'o', label='Data')
    plt.plot(x_new, y_linear, label='Interpolated (Linear)')
    plt.plot(x_new, y_inv, label='Interpolated (Inverse)')
    plt.plot(x_new, y_alt, '--', label='Interpolated (Alternative)')
    plt.axvline(x.mean(), color='k', linestyle='--', alpha=0.5, label='Inversion Point')

    plt.ylim(y_linear.min(), y_linear.max())
    plt.xlabel('x')
    plt.ylabel('y')
    plt.legend()
    plt.title('1D Interpolation with Inversion')
    plt.grid()
    plt.show()


    # Example usage of interp_2D
    x = np.array([1, 2, 3, 4, 5, 6])
    y = np.array([10, 20, 30])
    z = np.array([
        [10, 20, 30, 40, 50, 60],
        [110, 120, 130, 140, 150, 160],
        [210, 220, 230, 240, 250, 260],
        ]).T
    new_x = np.array([[1.5, 25], [2, 500], [0,0]])
    interpolator = RegularGridInterpolator((x, y), z, bounds_error=False, fill_value=None)
    result = interp2d((x, y), z, new_x, interpolator=interpolator, extrap=True)
    print("Interpolated result:", result)
    result = interp2d((x, y), z, new_x, interpolator=interpolator, extrap=[True])
    print("Interpolated result:", result)

    result2 = interp2d((x, y), z, new_x, extrap=[True,True])
    print("Interpolated result:", result2)
    result2 = interp2d((x, y), z, new_x, extrap=[False,True])
    print("Interpolated result:", result2)
    result2 = interp2d((x, y), z, new_x, extrap=[True, False])
    print("Interpolated result:", result2)
    result2 = interp2d((x, y), z, new_x, extrap=[False,False])
    print("Interpolated result:", result2)

if __name__ == "__main__":
    main()
