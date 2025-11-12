"""
Plotting utilities for rsimpy.
"""
import numpy as np
from bokeh.plotting import figure
from bokeh.models import (
    HoverTool, LinearColorMapper, LogColorMapper,
    ColorBar, BasicTicker, LogTicker
)
from bokeh.palettes import Viridis256, Turbo256, Plasma256, Inferno256, Magma256
from bokeh.layouts import column


def plot_polygon_grid(vertices, values, width=800, height=600,
                       palette='Viridis256', line_color='black', line_width=1,
                       vmin=None, vmax=None, colorbar=True,
                       colorbar_label=None, log_scale=False,
                       title='Polygon Grid', labels=None,
                       color_limits=None, out_of_range_color='gray'):
    """
    Plot a grid of 4-sided polygons in 2D with color-coded values using Bokeh.
    Interactive plot with hover functionality showing face number and value.

    Parameters
    ----------
    vertices : array-like, shape (n_polygons, 4, 2)
        Coordinates of polygon vertices. Each polygon has 4 vertices,
        and each vertex has (x, y) coordinates.
        vertices[i] contains the 4 vertices of polygon i.
        vertices[i, j] contains the (x, y) coordinates of vertex j.
    values : array-like, shape (n_polygons,)
        Values associated with each polygon. These determine the fill color.
    width : int, default=800
        Width of the plot in pixels.
    height : int, default=600
        Height of the plot in pixels.
    palette : str, default='Viridis256'
        Color palette name. Options: 'Viridis256', 'Turbo256', 'Plasma256',
        'Inferno256', 'Magma256', or any Bokeh palette.
    line_color : str, default='black'
        Color of polygon borders.
    line_width : float, default=1
        Width of polygon borders.
    vmin : float, optional
        Minimum value for color scale. If None, uses min(values).
    vmax : float, optional
        Maximum value for color scale. If None, uses max(values).
    colorbar : bool, default=True
        Whether to add a colorbar to the plot.
    colorbar_label : str, optional
        Label for the colorbar.
    log_scale : bool, default=False
        Whether to use logarithmic color scale.
    title : str, default='Polygon Grid'
        Title of the plot.
    labels : array-like of str, optional
        Array of string labels for each polygon. If provided, these will be
        displayed in the hover tooltip. Length must match number of polygons.
    color_limits : tuple of (min, max), optional
        Tuple specifying the color scale limits. Values outside these limits
        will be displayed in out_of_range_color. Either element can be None
        to use the data's min/max. For example:
        - (10, 100): values < 10 or > 100 are gray
        - (10, None): only values < 10 are gray
        - (None, 100): only values > 100 are gray
    out_of_range_color : str, default='gray'
        Color to use for polygons with values outside color_limits.

    Returns
    -------
    panel : bokeh.layouts.LayoutDOM
        Bokeh panel (layout) object containing the plot.

    Examples
    --------
    >>> from bokeh.plotting import show
    >>> # Create a simple 2x2 grid
    >>> vertices = np.array([
    ...     [[0, 0], [1, 0], [1, 1], [0, 1]],  # bottom-left
    ...     [[1, 0], [2, 0], [2, 1], [1, 1]],  # bottom-right
    ...     [[0, 1], [1, 1], [1, 2], [0, 2]],  # top-left
    ...     [[1, 1], [2, 1], [2, 2], [1, 2]],  # top-right
    ... ])
    >>> values = np.array([1, 2, 3, 4])
    >>> panel = plot_polygon_grid(vertices, values, colorbar_label='Value')
    >>> show(panel)
    """
    # Convert to numpy arrays
    vertices = np.asarray(vertices)
    values = np.asarray(values)

    # Validate inputs
    if vertices.ndim != 3 or vertices.shape[1] != 4 or vertices.shape[2] != 2:
        raise ValueError(
            f"vertices must have shape (n_polygons, 4, 2), got {vertices.shape}"
        )

    n_polygons = vertices.shape[0]
    if values.shape[0] != n_polygons:
        raise ValueError(
            f"values must have length {n_polygons}, got {values.shape[0]}"
        )

    # Validate labels if provided
    if labels is not None:
        labels = np.asarray(labels, dtype=str)
        if labels.shape[0] != n_polygons:
            raise ValueError(
                f"labels must have length {n_polygons}, got {labels.shape[0]}"
            )

    # Handle color_limits parameter
    limit_min = None
    limit_max = None
    if color_limits is not None:
        if not isinstance(color_limits, (tuple, list)) or len(color_limits) != 2:
            raise ValueError("color_limits must be a tuple of (min, max)")
        limit_min, limit_max = color_limits

    # Set color scale limits
    if vmin is None:
        vmin = np.nanmin(values) if limit_min is None else limit_min
    if vmax is None:
        vmax = np.nanmax(values) if limit_max is None else limit_max

    # Override with color_limits if provided
    if limit_min is not None:
        vmin = limit_min
    if limit_max is not None:
        vmax = limit_max

    # Handle log scale requirements
    if log_scale:
        if vmin <= 0:
            # Filter out non-positive values for log scale
            positive_values = values[values > 0]
            if len(positive_values) == 0:
                raise ValueError("Cannot use log scale with all non-positive values")
            vmin = np.nanmin(positive_values)
            print(f"Warning: Adjusting vmin to {vmin} for log scale (was <= 0)")

    # Get palette
    palette_map = {
        'Viridis256': Viridis256,
        'Turbo256': Turbo256,
        'Plasma256': Plasma256,
        'Inferno256': Inferno256,
        'Magma256': Magma256,
    }

    if isinstance(palette, str) and palette in palette_map:
        color_palette = palette_map[palette]
    elif isinstance(palette, str):
        # Try to use it as is (user provided palette name)
        color_palette = palette
    else:
        color_palette = palette

    # Create color mapper
    if log_scale:
        mapper = LogColorMapper(palette=color_palette, low=vmin, high=vmax)
        ticker = LogTicker()
    else:
        mapper = LinearColorMapper(palette=color_palette, low=vmin, high=vmax)
        ticker = BasicTicker()

    # Determine which values are in range
    in_range_mask = np.ones(n_polygons, dtype=bool)
    if color_limits is not None:
        if limit_min is not None:
            in_range_mask &= (values >= limit_min)
        if limit_max is not None:
            in_range_mask &= (values <= limit_max)

    # Prepare data for patches glyph
    xs = []  # List of lists of x coordinates for each polygon
    ys = []  # List of lists of y coordinates for each polygon
    face_ids = []  # Face numbers
    value_list = []  # Values for each polygon
    label_list = []  # Labels for each polygon
    fill_colors = []  # Fill colors for each polygon

    for i in range(n_polygons):
        # Extract x and y coordinates for this polygon
        poly_x = vertices[i, :, 0].tolist()
        poly_y = vertices[i, :, 1].tolist()

        xs.append(poly_x)
        ys.append(poly_y)
        face_ids.append(i)
        value_list.append(values[i])
        if labels is not None:
            label_list.append(labels[i])
        else:
            label_list.append("")

        # Determine fill color based on whether value is in range
        if in_range_mask[i]:
            # Will use color mapper
            fill_colors.append(None)
        else:
            # Out of range - use gray
            fill_colors.append(out_of_range_color)

    # Calculate plot range with margins
    all_x = vertices[:, :, 0].flatten()
    all_y = vertices[:, :, 1].flatten()
    x_range = all_x.max() - all_x.min()
    y_range = all_y.max() - all_y.min()
    x_margin = x_range * 0.02 if x_range > 0 else 1
    y_margin = y_range * 0.02 if y_range > 0 else 1

    # Create figure with equal axis scaling for map visualization
    p = figure(
        width=width,
        height=height,
        title=title,
        x_axis_label='X',
        y_axis_label='Y',
        match_aspect=True,
        aspect_scale=1,
        x_range=(all_x.min() - x_margin, all_x.max() + x_margin),
        y_range=(all_y.min() - y_margin, all_y.max() + y_margin),
        tools='pan,wheel_zoom,box_zoom,reset,save'
    )

    # Create data source dictionary
    source_data = {
        'xs': xs,
        'ys': ys,
        'face': face_ids,
        'value': value_list,
        'label': label_list,
        'in_range': in_range_mask.tolist()
    }

    # Add patches for in-range polygons (with color mapping)
    in_range_indices = np.where(in_range_mask)[0]
    if len(in_range_indices) > 0:
        in_range_data = {
            'xs': [xs[i] for i in in_range_indices],
            'ys': [ys[i] for i in in_range_indices],
            'face': [face_ids[i] for i in in_range_indices],
            'value': [value_list[i] for i in in_range_indices],
            'label': [label_list[i] for i in in_range_indices],
        }
        patches_in_range = p.patches(
            'xs', 'ys',
            source=in_range_data,
            fill_color={'field': 'value', 'transform': mapper},
            line_color=line_color,
            line_width=line_width,
        )
    else:
        patches_in_range = None

    # Add patches for out-of-range polygons (with fixed gray color)
    out_of_range_indices = np.where(~in_range_mask)[0]
    if len(out_of_range_indices) > 0:
        out_of_range_data = {
            'xs': [xs[i] for i in out_of_range_indices],
            'ys': [ys[i] for i in out_of_range_indices],
            'face': [face_ids[i] for i in out_of_range_indices],
            'value': [value_list[i] for i in out_of_range_indices],
            'label': [label_list[i] for i in out_of_range_indices],
        }
        patches_out_of_range = p.patches(
            'xs', 'ys',
            source=out_of_range_data,
            fill_color=out_of_range_color,
            line_color=line_color,
            line_width=line_width,
        )
    else:
        patches_out_of_range = None

    # Collect all patch renderers for hover tool
    all_patches = [r for r in [patches_in_range, patches_out_of_range] if r is not None]

    # Add hover tool
    tooltips = [
        ('Face', '@face'),
        ('Value', '@value{0.0000}')
    ]
    if labels is not None:
        tooltips.append(('Label', '@label'))

    hover = HoverTool(
        renderers=all_patches,
        tooltips=tooltips
    )
    p.add_tools(hover)

    # Add colorbar if requested
    if colorbar:
        color_bar = ColorBar(
            color_mapper=mapper,
            ticker=ticker,
            label_standoff=12,
            border_line_color=None,
            location=(0, 0),
            title=colorbar_label if colorbar_label else 'Value'
        )
        p.add_layout(color_bar, 'right')

    # Style the plot
    p.grid.grid_line_alpha = 0.3
    p.toolbar.logo = None

    # Return as a panel (layout)
    panel = column(p)

    return panel

if __name__ == "__main__":
    from bokeh.plotting import show

    # Example: 2x2 grid of squares
    # vertices = np.array([
    #     [[0, 0], [1, 0], [1, 1], [0, 1]],  # bottom-left
    #     [[1, 0], [2, 0], [2, 1], [1, 1]],  # bottom-right
    #     [[0, 1], [1, 1], [1, 2], [0, 2]],  # top-left
    #     [[1, 1], [2, 1], [2, 2], [1, 2]],  # top-right
    # ])
    # values = np.array([1, 2, 3, 4])

    # panel = plot_polygon_grid(vertices, values, colorbar_label='Value')
    # show(panel)

    # # Example with log scale and labels
    # vertices_log = np.array([
    #     [[0, 0], [1, 0], [1, 1], [0, 1]],
    #     [[1, 0], [2, 0], [2, 1], [1, 1]],
    #     [[0, 1], [1, 1], [1, 2], [0, 2]],
    #     [[1, 1], [2, 1], [2, 2], [1, 2]],
    # ])
    # values_log = np.array([1, 10, 100, 1000])
    # labels_log = np.array(['Low', 'Medium', 'High', 'Very High'])

    # panel_log = plot_polygon_grid(
    #     vertices_log, values_log,
    #     labels=labels_log,
    #     colorbar_label='Value (log scale)',
    #     log_scale=True,
    #     title='Polygon Grid - Log Scale with Labels'
    # )
    # show(panel_log)

    # Example with color limits
    vertices_limits = np.array([
        [[0.5, 0.5], [1, 0], [1, 1], [0, 1]],
        [[1, 0], [2, 0], [2, 1], [1, 1]],
        [[0, 1], [1, 1], [1, 2], [0, 2]],
        [[1, 1], [2, 1], [2, 2], [1, 2]],
        [[2, 0], [3, 0], [3, 1], [2, 1]],
        [[2, 1], [3.2, 1], [3, 2], [2, 2.2]],
    ])
    values_limits = np.array([5, 15, 25, 35, 45, 55])
    labels_limits = np.array(['V=5', 'V=15', 'V=25', 'V=35', 'V=45', 'V=55'])

    panel_limits = plot_polygon_grid(
        vertices_limits, values_limits,
        labels=labels_limits,
        color_limits=(20, 40),
        colorbar_label='Value',
        title='Color Limits Example (20-40, others gray)'
    )
    show(panel_limits)
