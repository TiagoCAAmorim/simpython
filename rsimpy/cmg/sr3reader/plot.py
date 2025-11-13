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
from _no_sync.rsimpy.cmg.sr3reader import sr3
from rsimpy.common import plot_utils, utils


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


    def plot_map(self, element, property_name, days=None, layers=None, **kwargs):
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
        **kwargs : dict
            Additional keyword arguments to pass to plot_polygon_grid.
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

        value_names = None
        if len(days) > 1:
            value_names = [f"{day} d" for day in days]
        elif len(layers) > 1:
            value_names = [f"k={layer}" for layer in layers]

        # [n_cells, n_dates]
        values = self._sr3.data.get(
            element_type="grid",
            properties=property_name.upper(),
            elements=element.upper(),
            days=days,
            active_only=False
        )[property_name.upper()].values

        # Future: remove inactive columns from values and coords
        active_cells = self._sr3.grid.complete2active() > 0
        values[~active_cells] = np.nan

        values = values.reshape(nk, -1, len(days))
        layers_ = [layer - 1 for layer in layers]
        values = values[layers_, :, :]  # [n_layers, n_cells, n_dates]
        values = values.transpose(0, 2, 1)  # [n_layers, n_dates, n_cells]
        values = values.reshape(-1, values.shape[-1])  # [n_layers*n_dates, n_cells]

        # [n_cells, 4, 3], 4 vertices per cell, 3 coordinates (x,y,z)
        all_coords = self._sr3.grid.coordinates.get(face=4)
        coords_2d = all_coords[:, :, :2]
        coords_2d = coords_2d.reshape(nk, -1, 4, 2)
        coords_2d = coords_2d[layers_, :, :, :]  # [n_layers, n_cells, 4, 2]
        if coords_2d.shape[0] == 1:
            coords_2d = coords_2d[0]
        else:
            coords_2d = [coords_2d[i] for i,_ in enumerate(layers_)]

        panel = plot_utils.plot_polygon_grid(
            vertices=coords_2d,
            values=values,
            **kwargs
        )

        return panel

        # # Convert active cell indices to i,j,k coordinates
        # ijk_coords = self._grid.n2ijk(active_indices, as_active=False)  # Shape: (n_active_cells, 3 or 4)

        # # Extract k indices (1-indexed)
        # k_indices = ijk_coords[:, 2]  # Shape: (n_active_cells,)

        # # Reorganize data and coordinates by layer
        # # We need to group cells by their k-index

        # # Determine which data dimension represents multiple columns
        # n_days = len(days)
        # n_layers = len(layers)
        # n_columns = max(n_days, n_layers)

        # # Filter to requested layers
        # layer_masks = {}
        # for layer in layers:
        #     layer_masks[layer] = (k_indices == layer)

        # # Prepare vertices and values for plotting
        # if len(layers) > 1:
        #     # Multiple layers: each layer is a separate polygon set
        #     vertices = []
        #     values_list = []

        #     for layer in layers:
        #         mask = layer_masks[layer]
        #         layer_coords = active_coords[mask]
        #         layer_data = property_data[mask, 0]  # Use first (and only) day

        #         vertices.append(layer_coords)
        #         values_list.append(layer_data)

        #     # Stack values into columns (one column per layer)
        #     values = np.column_stack(values_list)  # Shape: (n_cells_in_all_layers, n_layers)

        #     # Set default value_names if not provided
        #     if 'value_names' not in kwargs:
        #         kwargs['value_names'] = [f"Layer {layer}" for layer in layers]

        # else:
        #     # Single layer: each day is a separate column
        #     layer = layers[0]
        #     mask = layer_masks[layer]
        #     vertices = active_coords[mask]
        #     values = property_data[mask, :]  # Shape: (n_cells_in_layer, n_days)

        #     # Set default value_names if not provided
        #     if 'value_names' not in kwargs and n_days > 1:
        #         kwargs['value_names'] = [f"Day {day}" for day in days]

        # # Set default title if not provided
        # if 'title' not in kwargs:
        #     if len(layers) > 1:
        #         kwargs['title'] = f"{property_name} - Day {days[0]}"
        #     else:
        #         kwargs['title'] = f"{property_name} - Layer {layers[0]}"

        # # Set default colorbar label if not provided
        # if 'colorbar_label' not in kwargs:
        #     # Try to get property description
        #     prop_desc = self._data._properties.description(property_name)
        #     if 'units' in prop_desc and prop_desc['units']:
        #         kwargs['colorbar_label'] = f"{property_name} ({prop_desc['units']})"
        #     else:
        #         kwargs['colorbar_label'] = property_name

        # # Call plot_polygon_grid with the prepared data
        # panel = plot_utils.plot_polygon_grid(
        #     vertices=vertices,
        #     values=values,
        #     **kwargs
        # )

        # return panel
