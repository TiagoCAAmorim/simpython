# sr3reader/plot.py
"""
plot.py

This module provides functionality for plotting grid data.

Classes:
--------
PlotHandler
    A class to handle plotting of grid data.

Usage Example:
--------------
plot_handler = PlotHandler(data_handler, grid_handler, coord_handler)
panel = plot_handler.plot_map("matrix", "PRESSURE", days=100, layers=1)
"""

import numpy as np
from rsimpy.common import plot_utils, utils

INTERVALS = 20

class PlotHandler:
    """
    A class to handle plotting of data.

    Parameters
    ----------
    sr3_reader: sr3reader.Sr3Reader
        SR3 reader object.

    Methods
    -------
    plot_map(element, property, days=None, layers=None, **kwargs)
        Creates a map plot for the selected property, dates, and layers.
    """

    def __init__(self, sr3_reader):
        self._sr3 = sr3_reader


    def plot_map(self,
                 element,
                 property_name,
                 days=None, layers=None,
                 grid_property=None,
                 add_top=False,
                 add_connections=False,
                 **kwargs):
        """
        Creates a map plot for the selected property, dates, and layers.

        This function reads grid property data for specified dates and layers,
        then creates an interactive map visualization using polygon grids.

        Parameters
        ----------
        element : str
            Element type: 'matrix' or 'fracture'.
        property_name : str
            Property name to read from the grid data.
        days : float or list of float, optional
            Day(s) to read the grid data. If None, uses the first available day.
            If a list is provided, multiple dates will be plotted.
        layers : int or list of int, optional
            Layer(s) to read (1-indexed). If None, uses the first layer.
            If a list is provided, multiple layers will be plotted.
        grid_property : np.ndarray, optional
            A custom array of values to plot with size [n_cells, n_dates].
            If None, data will be read from the SR3 file.
            Default is None.
        add_top : bool, optional
            Whether to add contour lines to the plot.
            If True, uses the given contour_step. If contour_step is None,
            it will be estimated automatically.
            Default is False.
        add_connections : bool, optional
            Whether to add connections between grid cells.
            Only connections within the same layer are plotted.
            Only works for single layer plots.
            Default is False.
        **kwargs : dict
            Additional keyword arguments to pass to common.plot_utils.plot_polygon_grid.
            These can include: width, height, palette, line_color, line_width,
            colorbar, colorbar_label, log_scale, title, color_limits, etc.

        Returns
        -------
        panel : bokeh.layouts.LayoutDOM
            Bokeh panel (layout) object containing the plot.

        Raises
        ------
        ValueError
            If both days and layers are provided as lists.
        ValueError
            If element is not 'matrix' or 'fracture'.

        Examples
        --------
        >>> # Plot pressure for day 100, layer 1
        >>> panel = plot_handler.plot_map("matrix", "PRESSURE", days=100, layers=1)
        >>> from bokeh.plotting import show
        >>> show(panel)

        >>> # Plot multiple layers for a single date
        >>> panel = plot_handler.plot_map(
        ...     "matrix", "PRESSURE",
        ...     days=100,
        ...     layers=[1, 2, 3],
        ...     colorbar_label="Pressure (kgf/cm2)",
        ...     title="Pressure Distribution"
        ... )
        >>> show(panel)

        >>> # Plot multiple dates for a single layer
        >>> panel = plot_handler.plot_map(
        ...     "matrix", "SO",
        ...     days=[0, 100, 365],
        ...     layers=1,
        ...     colorbar_label="Oil Saturation",
        ...     value_names=["Initial", "100 days", "1 year"]
        ... )
        >>> show(panel)
        """
        if days is None:
            days = self._sr3.dates.get_days("grid")[:1]
        elif not utils.is_iterable(days):
            days = [days]

        ni, nj, nk = self._sr3.grid.get_size("nijk")
        if layers is None:
            if len(days) == 1:
                layers = list(range(1, nk+1))
            else:
                layers = [1]
        elif not utils.is_iterable(layers):
            layers = [layers]

        if len(days) > 1 and len(layers) > 1:
            raise ValueError(
                "Cannot provide multiple days and multiple layers. "
                "Please provide either one date with multiple layers, "
                "or one layer with multiple dates."
            )

        add_connections = add_connections and (len(layers) == 1)

        value_names = None
        if len(days) > 1:
            value_names = [f"{day} days" for day in days]
        elif len(layers) > 1:
            value_names = [f"k={layer}" for layer in layers]

        # [n_cells, n_dates]
        if grid_property is not None:
            values = grid_property
        else:
            values = self._sr3.data.get(
                element_type="grid",
                properties=property_name.upper(),
                elements=element.upper(),
                days=days,
                active_only=False
            )[property_name.upper()].values

            # Future: remove inactive columns from values and coords
            if not self._sr3.grid.is_complete(property_name):
                inactive_cells = self._sr3.grid.complete2active() == 0
                values[inactive_cells] = np.nan

        values = values.reshape(nk, -1, len(days)) # [nk, ni*nj, n_dates]
        layers_ = [layer - 1 for layer in layers]
        values = values[layers_, :, :]  # [n_layers, n_cells, n_dates]
        values = values.transpose(1, 0, 2)  # [n_cells, n_layers, n_dates]
        values = values.reshape(values.shape[0], -1)  # [n_cells, n_layers*n_dates]

        # [n_cells, 4, 3], 4 vertices per cell, 3 coordinates (x,y,z)
        all_coords = self._sr3.grid.coordinates.get(face=4)
        all_coords = all_coords.reshape(nk, -1, 4, all_coords.shape[2]) # [nk, ni*nj, 4, 3]
        all_coords = all_coords[layers_, :, :, :]  # [n_layers, ni*nj, 4, 3]

        kwargs['contour_step'] = self._estimate_contour_step(
            all_coords,
            values,
            add_top,
            kwargs.get('contour_step', None),
        )

        if all_coords.shape[0] == 1:
            all_coords = all_coords[0] # [ni*nj, 4, 3]

        if add_connections:
            self._get_connections(layers[0], kwargs)

        ijk = self._sr3.grid.n2ijk(np.arange(1, ni*nj+1))
        labels = [f"({ijk[i,0]}, {ijk[i,1]})" for i in range(ijk.shape[0])]

        if 'nan_inf_color' not in kwargs:
            kwargs['nan_inf_color'] = None

        if 'title' not in kwargs:
            if len(layers) > 1:
                kwargs['title'] = f"{property_name} - {days[0]} days"
            elif len(days) > 1:
                kwargs['title'] = f"{property_name} - Layer {layers[0]}"
            else:
                kwargs['title'] = f"{property_name} - Layer {layers[0]} at {days[0]} days"

        if 'colorbar_label' not in kwargs:
            unit = self._sr3.properties.unit(property_name=property_name.upper())
            kwargs['colorbar_label'] = f"{property_name} ({unit})"

        panel = plot_utils.plot_polygon_grid(
            vertices=all_coords,
            values=values,
            value_names=value_names,
            labels=labels,
            **kwargs
        )

        return panel

    def _get_connections(self, layer, kwargs):
        """Get connections for the specified layer and add to kwargs."""
        ni, nj, _ = self._sr3.grid.get_size("nijk")
        connections = self._sr3.connections.get_connections(as_active=False)
        ijk1 = self._sr3.grid.n2ijk(connections[:, 0])
        ijk2 = self._sr3.grid.n2ijk(connections[:, 1])
        filter_ = ijk1[:, 2] == ijk2[:, 2]
        filter_ = filter_ & (ijk1[:, 2] == layer)
        connections = connections[filter_]
        if len(connections) > 0:
            conns = connections[:,:2].T - ni*nj*(layer-1) - 1
            kwargs['connections'] = np.concat([conns, conns[[1,0]]], axis=1)
            conn_values = self._sr3.connections.get_transmissibilities(connections)
            kwargs['connection_values'] = np.concat([conn_values, conn_values], axis=0)
            kwargs['connection_log_scale'] = True
            kwargs['connection_colorbar_label'] = 'Transmissibility (mD.m)'

    def _estimate_contour_step(self, all_coords, values, add_top, contour_step):
        """Estimate contour step if not provided."""
        if not add_top:
            return None
        if add_top and contour_step is None:
            filter_ = np.any(~np.isnan(values), axis=1)
            all_z = all_coords[:, filter_, :, 2]
            min_z, max_z = np.nanmin(all_z), np.nanmax(all_z)
            z_range = max_z - min_z
            if z_range > 0:
                target_intervals = INTERVALS
                raw_step = z_range / target_intervals
                exp = np.floor(np.log10(raw_step))
                mant = raw_step / (10.0 ** exp)
                for factor in (1.0, 2.0, 5.0, 10.0):
                    if mant <= factor:
                        nice_step = factor * (10.0 ** exp)
                        break
                return float(nice_step)
            return None
        return contour_step
