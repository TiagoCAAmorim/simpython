"""
Plotting utilities for rsimpy.
"""
import numpy as np
from bokeh.plotting import figure
from bokeh.models import (
    HoverTool, LinearColorMapper, LogColorMapper,
    ColorBar, BasicTicker, LogTicker, Select, ColumnDataSource, CustomJS
)
from bokeh.palettes import (
    Viridis256, Turbo256, Plasma256, Inferno256, Magma256,
    Cividis256, Greys256, Blues256, Greens256, Reds256,
    Oranges256, Purples256
)
from bokeh.layouts import column, row


def plot_polygon_grid(vertices, values, width=800, height=600,
                       palette='Viridis256', line_color='black', line_width=1,
                       colorbar=True, colorbar_label=None, log_scale=False,
                       title='Polygon Grid', labels=None,
                       color_limits=None, out_of_range_colors=None,
                       nan_inf_color=None, value_names=None):
    """
    Plot a grid of n-sided polygons in 2D with color-coded values using Bokeh.
    Interactive plot with hover functionality showing face number and value.

    Parameters
    ----------
    vertices : array-like, shape (n_polygons, n_vertices, 2) or list of such arrays
        Coordinates of polygon vertices. Each polygon can have any number of vertices
        (minimum 3), and each vertex has (x, y) coordinates.

        Single set (fixed polygons):
            vertices[i] contains all vertices of polygon i.
            vertices[i, j] contains the (x, y) coordinates of vertex j.
            Can be a list of arrays with varying sizes for mixed polygons.

        Multiple sets (dynamic polygons):
            List of lists where vertices[col_idx] contains the polygon set for column col_idx.
            When values is 2D with m columns, vertices must be a list of m polygon sets.
            Each inner list must have the same number of polygons as rows in values.
    values : array-like, shape (n_polygons,) or (n_polygons, m)
        Values associated with each polygon. These determine the fill color.
        Can be a 1D array or 2D matrix. If 2D, a dropdown control will be
        added to select which column to display.
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
        Tuple specifying the color scale limits. Either element can be None to use
        the data's min/max. If not provided, uses (data_min, data_max). For example:
        - (10, 100): color scale 10-100
        - (10, None): color scale 10 to data_max
        - (None, 100): color scale data_min to 100
        - None: color scale from data_min to data_max
    out_of_range_colors : str or tuple of (str, str), default=None
        Color(s) for polygons with values outside color_limits.
        - None (default): values outside limits get min/max colors from the palette
        - Single color (e.g., 'gray'): both below and above limits use this color
        - Tuple (e.g., ('blue', 'red')): (color_below_min, color_above_max)
        - Tuple with None: e.g., (None, 'red') means below-min uses palette min color,
          above-max uses red
    nan_inf_color : str or None, default=None
        Color for polygons with NaN or Inf values.
        - None (default): hide these polygons (not rendered)
        - Color string (e.g., 'gray'): display NaN/Inf polygons with this color
    value_names : array-like of str, optional
        Names for each column in the values matrix. Used as options in the
        dropdown selector when values is 2D. If None, uses 'Column 0', 'Column 1', etc.

    Returns
    -------
    panel : bokeh.layouts.LayoutDOM
        Bokeh panel (layout) object containing the plot.

    Examples
    --------
    >>> from bokeh.plotting import show
    >>> import numpy as np
    >>>
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

    >>> # With color limits and out-of-range colors
    >>> values = np.array([5, 15, 25, 35])
    >>> panel = plot_polygon_grid(
    ...     vertices, values,
    ...     color_limits=(10, 30),  # Scale from 10 to 30
    ...     out_of_range_colors=('blue', 'red'),  # Below=blue, Above=red
    ...     colorbar_label='Value'
    ... )
    >>> show(panel)  # Value 5 is blue, 15 and 25 colored, 35 is red

    >>> # Show NaN/Inf polygons in gray
    >>> values = np.array([1, np.nan, 3, np.inf])
    >>> panel = plot_polygon_grid(
    ...     vertices, values,
    ...     nan_inf_color='gray',  # Show NaN/Inf as gray
    ...     colorbar_label='Value'
    ... )
    >>> show(panel)  # All polygons shown, NaN and Inf are gray

    >>> # Hide NaN/Inf polygons (default)
    >>> values = np.array([1, np.nan, 3, np.inf])
    >>> panel = plot_polygon_grid(
    ...     vertices, values,
    ...     nan_inf_color=None,  # Don't show NaN/Inf (default)
    ...     colorbar_label='Value'
    ... )
    >>> show(panel)  # Only polygons 0 and 2 are shown

    >>> # N-sided polygons: triangles
    >>> triangles = np.array([
    ...     [[0, 0], [1, 0], [0.5, 0.9]],  # Triangle 1
    ...     [[1, 0], [2, 0], [1.5, 0.9]],  # Triangle 2
    ... ])
    >>> values_tri = np.array([10, 20])
    >>> panel = plot_polygon_grid(triangles, values_tri)
    >>> show(panel)

    >>> # N-sided polygons: hexagons (or any n-sided)
    >>> import math
    >>> def make_hexagon(cx, cy, r):
    ...     return np.array([[cx + r*math.cos(i*math.pi/3),
    ...                       cy + r*math.sin(i*math.pi/3)]
    ...                      for i in range(6)])
    >>> hexagons = np.array([make_hexagon(0, 0, 1), make_hexagon(1.5, 0, 1)])
    >>> panel = plot_polygon_grid(hexagons, np.array([1, 2]))
    >>> show(panel)

    >>> # Mixed polygons with different number of vertices
    >>> mixed_polygons = [
    ...     np.array([[0, 0], [1, 0], [0.5, 1]]),  # Triangle
    ...     np.array([[1.5, 0], [2.5, 0], [2.5, 1], [1.5, 1]]),  # Square
    ...     np.array([[3, 0], [3.5, 0], [3.7, 0.5], [3.5, 1], [3, 1], [2.8, 0.5]]),  # Hexagon
    ... ]
    >>> values_mixed = np.array([5, 10, 15])
    >>> panel = plot_polygon_grid(mixed_polygons, values_mixed)
    >>> show(panel)

    >>> # Matrix values with interactive selector
    >>> values_matrix = np.array([
    ...     [10, 100, 0.2],  # Temperature, Pressure, Porosity for cell 0
    ...     [20, 200, 0.3],
    ...     [30, 300, 0.4],
    ...     [40, 400, 0.5]
    ... ])
    >>> panel = plot_polygon_grid(
    ...     vertices, values_matrix,
    ...     value_names=['Temp', 'Press', 'Poro'],
    ...     color_limits=(15, 35),  # Applied to each column
    ...     colorbar_label='Value'
    ... )
    >>> show(panel)  # Dropdown selector will appear to choose columns
    """
    values = np.asarray(values)

    # Check if values is a matrix
    is_matrix = values.ndim == 2
    if is_matrix:
        n_polygons, n_columns = values.shape
    else:
        if values.ndim == 1:
            values = values.reshape(-1, 1)
            n_columns = 1
            n_polygons = values.shape[0]
        else:
            raise ValueError("values must be 1D or 2D array")

    # Parse vertices structure to determine if we have multiple polygon sets
    # Three cases:
    # 1. Single uniform array: (n_polygons, n_vertices, 2)
    # 2. Single list of polygons: [(n_vertices_0, 2), (n_vertices_1, 2), ...]
    # 3. Multiple lists (one per column): [[(n_vertices, 2), ...], [(n_vertices, 2), ...], ...]

    vertices_are_multi_set = False

    if isinstance(vertices, (list, tuple)) and len(vertices) > 0:
        first_elem = vertices[0]
        # Check if first element is itself a list/array of polygons or a single polygon
        if isinstance(first_elem, (list, tuple)):
            # Could be case 2 or 3
            # Check if first_elem[0] is a polygon or a vertex
            if len(first_elem) > 0:
                second_elem = first_elem[0]
                if isinstance(second_elem, (list, tuple, np.ndarray)):
                    second_elem_arr = np.asarray(second_elem)
                    if second_elem_arr.ndim == 2 and second_elem_arr.shape[1] == 2:
                        # first_elem[0] is a polygon -> case 3 (multi-set)
                        vertices_are_multi_set = True
                    elif second_elem_arr.ndim == 1 and len(second_elem_arr) == 2:
                        # first_elem[0] is a vertex -> case 2 (single list)
                        vertices_are_multi_set = False
                    else:
                        # Ambiguous, check shape
                        vertices_are_multi_set = False
        elif isinstance(first_elem, np.ndarray):
            # first_elem is an array
            if first_elem.ndim == 2 and first_elem.shape[1] == 2:
                # first_elem is a single polygon -> case 2
                vertices_are_multi_set = False
            elif first_elem.ndim == 3:
                # Unusual case: might be trying case 3 with arrays
                vertices_are_multi_set = True
            elif first_elem.ndim == 1:
                # first_elem might be a list of polygons as arrays
                vertices_are_multi_set = False

    # Now parse vertices based on the determined structure
    if vertices_are_multi_set:
        # Case 3: Multiple polygon sets (one per column)
        if len(vertices) != n_columns:
            raise ValueError(
                f"When providing multiple polygon sets, must have {n_columns} sets "
                f"(one per data column), got {len(vertices)}"
            )

        # Parse each set
        all_vertices_lists = []
        for col_idx, vert_set in enumerate(vertices):
            vert_list = []
            if isinstance(vert_set, np.ndarray):
                if vert_set.ndim == 3:
                    # Uniform array for this column
                    if vert_set.shape[0] != n_polygons:
                        raise ValueError(
                            f"vertices[{col_idx}] must have {n_polygons} polygons, "
                            f"got {vert_set.shape[0]}"
                        )
                    for i in range(n_polygons):
                        vert_list.append(vert_set[i])
                else:
                    raise ValueError(
                        f"vertices[{col_idx}] array must have 3 dimensions, got {vert_set.ndim}"
                    )
            elif isinstance(vert_set, (list, tuple)):
                # List of polygons
                if len(vert_set) != n_polygons:
                    raise ValueError(
                        f"vertices[{col_idx}] must have {n_polygons} polygons, "
                        f"got {len(vert_set)}"
                    )
                for i, poly in enumerate(vert_set):
                    poly_arr = np.asarray(poly)
                    if poly_arr.ndim != 2 or poly_arr.shape[1] != 2:
                        raise ValueError(
                            f"vertices[{col_idx}][{i}] must have shape (n_vertices, 2), "
                            f"got {poly_arr.shape}"
                        )
                    if poly_arr.shape[0] < 3:
                        raise ValueError(
                            f"vertices[{col_idx}][{i}] must have at least 3 vertices"
                        )
                    vert_list.append(poly_arr)
            else:
                raise ValueError(f"vertices[{col_idx}] must be array or list")

            all_vertices_lists.append(vert_list)

        # Start with first column's polygons
        vertices_list = all_vertices_lists[0]

    else:
        # Cases 1 & 2: Single polygon set (used for all columns)
        if isinstance(vertices, (list, tuple)) and len(vertices) > 0:
            # Check if it's a list of arrays with potentially different sizes
            if isinstance(vertices[0], np.ndarray) or isinstance(vertices[0], (list, tuple)):
                # Each element is a polygon with potentially different number of vertices
                vertices_list = [np.asarray(v) for v in vertices]
                n_poly = len(vertices_list)
                # Validate each polygon
                for i, v in enumerate(vertices_list):
                    if v.ndim != 2 or v.shape[1] != 2:
                        raise ValueError(
                            f"vertices[{i}] must have shape (n_vertices, 2), got {v.shape}"
                        )
                    if v.shape[0] < 3:
                        raise ValueError(
                            f"vertices[{i}] must have at least 3 vertices, got {v.shape[0]}"
                        )
            else:
                # It's a regular array
                vertices = np.asarray(vertices)
                if vertices.ndim != 3 or vertices.shape[2] != 2:
                    raise ValueError(
                        f"vertices must have shape (n_polygons, n_vertices, 2), got {vertices.shape}"
                    )
                if vertices.shape[1] < 3:
                    raise ValueError(
                        f"Each polygon must have at least 3 vertices, got {vertices.shape[1]}"
                    )
                n_poly = vertices.shape[0]
                # Convert to list for uniform processing
                vertices_list = [vertices[i] for i in range(n_poly)]
        else:
            vertices = np.asarray(vertices)
            if vertices.ndim != 3 or vertices.shape[2] != 2:
                raise ValueError(
                    f"vertices must have shape (n_polygons, n_vertices, 2), got {vertices.shape}"
                )
            if vertices.shape[1] < 3:
                raise ValueError(
                    f"Each polygon must have at least 3 vertices, got {vertices.shape[1]}"
                )
            n_poly = vertices.shape[0]
            # Convert to list for uniform processing
            vertices_list = [vertices[i] for i in range(n_poly)]

        if n_poly != n_polygons:
            raise ValueError(
                f"Number of polygons ({n_poly}) must match number of values ({n_polygons})"
            )

        # Replicate for all columns
        all_vertices_lists = [vertices_list for _ in range(n_columns)]

    if value_names is None:
        value_names = [f'Column {i}' for i in range(n_columns)]
    else:
        if len(value_names) != n_columns:
            raise ValueError(
                f"value_names must have length {n_columns}, got {len(value_names)}"
            )

    # Validate labels if provided
    if labels is not None:
        labels = np.asarray(labels, dtype=str)
        if labels.shape[0] != n_polygons:
            raise ValueError(
                f"labels must have length {n_polygons}, got {labels.shape[0]}"
            )

    # Normalize out_of_range_colors to tuple format
    if out_of_range_colors is None:
        color_below_min = None
        color_above_max = None
    elif isinstance(out_of_range_colors, (tuple, list)):
        if len(out_of_range_colors) != 2:
            raise ValueError("out_of_range_colors tuple must have exactly 2 elements")
        color_below_min, color_above_max = out_of_range_colors
    else:
        # Single value - use for both
        color_below_min = out_of_range_colors
        color_above_max = out_of_range_colors

    # Handle color_limits parameter
    limit_min = None
    limit_max = None
    if color_limits is not None:
        if not isinstance(color_limits, (tuple, list)) or len(color_limits) != 2:
            raise ValueError("color_limits must be a tuple of (min, max)")
        limit_min, limit_max = color_limits

    # Filter out NaN and Inf values for color scale calculation
    finite_mask = np.isfinite(values)
    finite_values = values[finite_mask]

    if len(finite_values) == 0:
        raise ValueError("All values are NaN or Inf - cannot determine color scale")

    # Set color scale limits using finite values only
    if limit_min is None:
        limit_min = np.min(finite_values)
    if limit_max is None:
        limit_max = np.max(finite_values)

    vmin = limit_min
    vmax = limit_max

    # Handle log scale requirements
    if log_scale:
        if vmin <= 0:
            # Filter out non-positive values for log scale
            positive_values = finite_values[finite_values > 0]
            if len(positive_values) == 0:
                raise ValueError("Cannot use log scale with all non-positive values")
            vmin = np.min(positive_values)
            print(f"Warning: Adjusting vmin to {vmin} for log scale (was <= 0)")

    # Define available palettes
    palette_map = {
        'Viridis': Viridis256,
        'Turbo': Turbo256,
        'Plasma': Plasma256,
        'Inferno': Inferno256,
        'Magma': Magma256,
        'Cividis': Cividis256,
        'Greys': Greys256,
        'Blues': Blues256,
        'Greens': Greens256,
        'Reds': Reds256,
        'Oranges': Oranges256,
        'Purples': Purples256,
    }

    # For backward compatibility, also accept names with '256' suffix
    palette_map_with_suffix = {k + '256': v for k, v in palette_map.items()}
    palette_map.update(palette_map_with_suffix)

    if isinstance(palette, str) and palette in palette_map:
        color_palette = palette_map[palette]
    elif isinstance(palette, str):
        # Try to use it as is (user provided palette name)
        color_palette = palette
    else:
        color_palette = palette

    # Store initial palette name for selector
    if isinstance(palette, str):
        if palette.endswith('256'):
            initial_palette = palette[:-3]  # Remove '256' suffix
        else:
            initial_palette = palette if palette in palette_map else 'Viridis'
    else:
        initial_palette = 'Viridis'

    # Create color mapper
    if log_scale:
        mapper = LogColorMapper(palette=color_palette, low=vmin, high=vmax)
        ticker = LogTicker()
    else:
        mapper = LinearColorMapper(palette=color_palette, low=vmin, high=vmax)
        ticker = BasicTicker()

    # Prepare data for patches glyph - handle matrix case
    xs = []  # List of lists of x coordinates for each polygon
    ys = []  # List of lists of y coordinates for each polygon
    face_ids = []  # Face numbers
    label_list = []  # Labels for each polygon

    for i in range(n_polygons):
        # Extract x and y coordinates for this polygon
        poly_vertices = vertices_list[i]
        poly_x = poly_vertices[:, 0].tolist()
        poly_y = poly_vertices[:, 1].tolist()

        xs.append(poly_x)
        ys.append(poly_y)
        face_ids.append(i)
        if labels is not None:
            label_list.append(labels[i])
        else:
            label_list.append("")

    # Start with the first column (or only column)
    current_values = values[:, 0]

    # Separate NaN/Inf from out-of-range values
    finite_mask = np.isfinite(current_values)
    nan_inf_mask = ~finite_mask

    # For finite values, determine which are in range
    below_min_mask = np.zeros(n_polygons, dtype=bool)
    above_max_mask = np.zeros(n_polygons, dtype=bool)
    in_range_mask = np.zeros(n_polygons, dtype=bool)

    finite_indices = np.where(finite_mask)[0]
    for idx in finite_indices:
        val = current_values[idx]
        if val < vmin:
            below_min_mask[idx] = True
        elif val > vmax:
            above_max_mask[idx] = True
        else:
            in_range_mask[idx] = True

    # Calculate plot range with margins to encompass all possible polygon sets
    # Exclude NaN/Inf polygons from range calculation if they won't be rendered
    all_x_coords = []
    all_y_coords = []

    for col_idx in range(n_columns):
        col_vertices = all_vertices_lists[col_idx]
        col_values = values[:, col_idx]

        for poly_idx, poly_verts in enumerate(col_vertices):
            # Include polygon in range calculation if:
            # - It has finite value, OR
            # - It has NaN/Inf but will be rendered (nan_inf_color is not None)
            if np.isfinite(col_values[poly_idx]) or nan_inf_color is not None:
                all_x_coords.append(poly_verts[:, 0])
                all_y_coords.append(poly_verts[:, 1])

    if len(all_x_coords) == 0:
        # Fallback if no polygons to display
        all_x = np.array([0, 1])
        all_y = np.array([0, 1])
    else:
        all_x = np.concatenate(all_x_coords)
        all_y = np.concatenate(all_y_coords)

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

    # Create base data dictionary with all columns stored
    base_data = {
        'xs': xs,
        'ys': ys,
        'face': face_ids,
        'label': label_list,
    }

    # Add all value columns to the data
    for col_idx in range(n_columns):
        base_data[f'value_{col_idx}'] = values[:, col_idx].tolist()

    # Add all vertices columns to the data (for dynamic polygon updates)
    for col_idx in range(n_columns):
        col_vertices = all_vertices_lists[col_idx]
        xs_col = [v[:, 0].tolist() for v in col_vertices]
        ys_col = [v[:, 1].tolist() for v in col_vertices]
        base_data[f'xs_{col_idx}'] = xs_col
        base_data[f'ys_{col_idx}'] = ys_col

    # Set the active value column
    base_data['value'] = current_values.tolist()
    base_data['in_range'] = in_range_mask.tolist()

    # Create ColumnDataSource for dynamic updates
    source = ColumnDataSource(data=base_data)

    # Create data sources and patches for each category
    all_patches = []

    # 1. In-range polygons (with color mapping)
    in_range_indices = np.where(in_range_mask)[0]
    if len(in_range_indices) > 0:
        in_range_data = {
            'xs': [xs[i] for i in in_range_indices],
            'ys': [ys[i] for i in in_range_indices],
            'face': [face_ids[i] for i in in_range_indices],
            'value': [current_values[i] for i in in_range_indices],
            'label': [label_list[i] for i in in_range_indices],
        }
        source_in_range = ColumnDataSource(data=in_range_data)
        patches_in_range = p.patches(
            'xs', 'ys',
            source=source_in_range,
            fill_color={'field': 'value', 'transform': mapper},
            line_color=line_color,
            line_width=line_width,
        )
        all_patches.append(patches_in_range)
    else:
        source_in_range = None

    # 2. Below minimum (use color_below_min or palette min color)
    below_min_indices = np.where(below_min_mask)[0]
    if len(below_min_indices) > 0:
        below_min_data = {
            'xs': [xs[i] for i in below_min_indices],
            'ys': [ys[i] for i in below_min_indices],
            'face': [face_ids[i] for i in below_min_indices],
            'value': [current_values[i] for i in below_min_indices],
            'label': [label_list[i] for i in below_min_indices],
        }
        source_below_min = ColumnDataSource(data=below_min_data)
        if color_below_min is None:
            # Use palette color for vmin
            patches_below_min = p.patches(
                'xs', 'ys',
                source=source_below_min,
                fill_color={'field': 'value', 'transform': mapper},
                line_color=line_color,
                line_width=line_width,
            )
        else:
            patches_below_min = p.patches(
                'xs', 'ys',
                source=source_below_min,
                fill_color=color_below_min,
                line_color=line_color,
                line_width=line_width,
            )
        all_patches.append(patches_below_min)
    else:
        source_below_min = None

    # 3. Above maximum (use color_above_max or palette max color)
    above_max_indices = np.where(above_max_mask)[0]
    if len(above_max_indices) > 0:
        above_max_data = {
            'xs': [xs[i] for i in above_max_indices],
            'ys': [ys[i] for i in above_max_indices],
            'face': [face_ids[i] for i in above_max_indices],
            'value': [current_values[i] for i in above_max_indices],
            'label': [label_list[i] for i in above_max_indices],
        }
        source_above_max = ColumnDataSource(data=above_max_data)
        if color_above_max is None:
            # Use palette color for vmax
            patches_above_max = p.patches(
                'xs', 'ys',
                source=source_above_max,
                fill_color={'field': 'value', 'transform': mapper},
                line_color=line_color,
                line_width=line_width,
            )
        else:
            patches_above_max = p.patches(
                'xs', 'ys',
                source=source_above_max,
                fill_color=color_above_max,
                line_color=line_color,
                line_width=line_width,
            )
        all_patches.append(patches_above_max)
    else:
        source_above_max = None

    # 4. NaN/Inf polygons (show with specified color or hide)
    if nan_inf_color is not None:
        nan_inf_indices = np.where(nan_inf_mask)[0]
        if len(nan_inf_indices) > 0:
            nan_inf_data = {
                'xs': [xs[i] for i in nan_inf_indices],
                'ys': [ys[i] for i in nan_inf_indices],
                'face': [face_ids[i] for i in nan_inf_indices],
                'value': [current_values[i] for i in nan_inf_indices],
                'label': [label_list[i] for i in nan_inf_indices],
            }
            source_nan_inf = ColumnDataSource(data=nan_inf_data)
            patches_nan_inf = p.patches(
                'xs', 'ys',
                source=source_nan_inf,
                fill_color=nan_inf_color,
                line_color=line_color,
                line_width=line_width,
            )
            all_patches.append(patches_nan_inf)
        else:
            source_nan_inf = None
    else:
        source_nan_inf = None

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

    # Create palette selector
    palette_options = [
        'Viridis', 'Turbo', 'Plasma', 'Inferno', 'Magma', 'Cividis',
        'Greys', 'Blues', 'Greens', 'Reds', 'Oranges', 'Purples'
    ]
    # Add reversed versions
    palette_options_with_reversed = []
    for pal in palette_options:
        palette_options_with_reversed.append(pal)
        palette_options_with_reversed.append(pal + ' (reversed)')

    palette_select = Select(
        title="Color Palette:",
        value=initial_palette,
        options=palette_options_with_reversed,
        width=200
    )

    # Create JavaScript callback to update palette
    palette_callback = CustomJS(
        args=dict(
            mapper=mapper,
            palette_select=palette_select,
            palette_map={k: list(v) for k, v in palette_map.items() if not k.endswith('256')},
        ),
        code="""
            const palette_name = palette_select.value;
            let reversed = false;
            let base_name = palette_name;

            // Check if reversed
            if (palette_name.endsWith(' (reversed)')) {
                reversed = true;
                base_name = palette_name.replace(' (reversed)', '');
            }

            // Get the palette
            let palette = palette_map[base_name];

            if (palette) {
                // Reverse if needed
                if (reversed) {
                    palette = palette.slice().reverse();
                }

                // Update the mapper
                mapper.palette = palette;
            }
        """
    )

    palette_select.js_on_change('value', palette_callback)

    # If matrix values, add selector control
    if is_matrix and n_columns > 1:
        # Create dropdown selector
        select = Select(
            title="Select Data Column:",
            value=value_names[0],
            options=list(value_names),
            width=200
        )

        # Create JavaScript callback to update data when selection changes
        callback = CustomJS(
            args=dict(
                source=source,
                source_in=source_in_range,
                source_below=source_below_min,
                source_above=source_above_max,
                source_nan=source_nan_inf,
                select=select,
                value_names=value_names,
                n_columns=n_columns,
                vmin=vmin,
                vmax=vmax,
                nan_inf_color=nan_inf_color,
            ),
            code="""
                // Find which column was selected
                const col_name = select.value;
                const col_idx = value_names.indexOf(col_name);

                // Get the data from the source
                const data = source.data;
                const n_polygons = data['xs_0'].length;  // Use stored vertices count

                // Update the active value and vertices columns
                const new_values = data['value_' + col_idx];
                const new_xs = data['xs_' + col_idx];
                const new_ys = data['ys_' + col_idx];

                data['value'] = new_values;
                data['xs'] = new_xs;
                data['ys'] = new_ys;

                // Categorize polygons
                const in_range = new Array(n_polygons);
                const below_min = new Array(n_polygons);
                const above_max = new Array(n_polygons);
                const nan_inf = new Array(n_polygons);

                for (let i = 0; i < n_polygons; i++) {
                    const val = new_values[i];
                    if (!isFinite(val)) {
                        nan_inf[i] = true;
                        in_range[i] = false;
                        below_min[i] = false;
                        above_max[i] = false;
                    } else if (val < vmin) {
                        below_min[i] = true;
                        in_range[i] = false;
                        above_max[i] = false;
                        nan_inf[i] = false;
                    } else if (val > vmax) {
                        above_max[i] = true;
                        in_range[i] = false;
                        below_min[i] = false;
                        nan_inf[i] = false;
                    } else {
                        in_range[i] = true;
                        below_min[i] = false;
                        above_max[i] = false;
                        nan_inf[i] = false;
                    }
                }

                // Helper function to update a source
                function updateSource(src, mask) {
                    if (src === null) return;
                    const src_data = src.data;
                    const src_xs = [];
                    const src_ys = [];
                    const src_face = [];
                    const src_value = [];
                    const src_label = [];

                    for (let i = 0; i < n_polygons; i++) {
                        if (mask[i]) {
                            src_xs.push(new_xs[i]);
                            src_ys.push(new_ys[i]);
                            src_face.push(data['face'][i]);
                            src_value.push(new_values[i]);
                            src_label.push(data['label'][i]);
                        }
                    }

                    src_data['xs'] = src_xs;
                    src_data['ys'] = src_ys;
                    src_data['face'] = src_face;
                    src_data['value'] = src_value;
                    src_data['label'] = src_label;
                    src.change.emit();
                }

                // Update all sources
                updateSource(source_in, in_range);
                updateSource(source_below, below_min);
                updateSource(source_above, above_max);
                if (nan_inf_color !== null) {
                    updateSource(source_nan, nan_inf);
                }

                source.change.emit();
            """
        )

        select.js_on_change('value', callback)

        # Create layout with selectors and plot
        controls = row(select, palette_select)
        panel = column(controls, p)
    else:
        # Return as a panel with palette selector
        panel = column(palette_select, p)

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
    vertices1 = [
        [[0.5, 0.5], [1, 0], [1, 1]],
        [[1, 0], [2, 0], [2, 1], [1, 1]],
        [[0, 1], [1, 1], [1, 2], [0, 2]],
        [[1, 1], [2, 1], [2, 2], [1, 2]],
        [[2, 0], [3, 0], [3, 1], [2, 1]],
        [[2, 1], [3.2, 1], [3, 2], [2, 2.2]],
    ]
    vertices2 = [
        [[0, 0], [1, 0], [1, 1], [0, 1]],
        [[1, 0], [2, 0], [2, 1], [1, 1]],
        [[0, 1], [1, 1], [1, 2], [0, 2]],
        [[1, 1], [2, 1], [2, 2], [1, 2]],
        [[2, 0], [3, 0], [3, 1], [2, 1]],
        [[2, 1], [3.2, 1], [3, 2], [2, 2.2]],
    ]
    values = np.array([[5, 15, 25, np.nan, 45, 55],[15, 115, 125, 135, 145, 155]]).T
    labels = np.array(['V=5', 'V=15', 'V=25', 'V=35', 'V=45', 'V=55'])

    panel_limits = plot_polygon_grid(
        vertices=[vertices1, vertices2],
        values=values,
        labels=labels,
        palette='Turbo',
        color_limits=(20, 50),
        out_of_range_colors=('blue', 'red'),
        nan_inf_color=None,
        colorbar_label='Value',
        title='Map Example'
    )
    show(panel_limits)
