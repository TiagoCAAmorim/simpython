"""
Plotting utilities for rsimpy.
"""
import numpy as np
from bokeh.plotting import figure
from bokeh.models import (
    HoverTool, LinearColorMapper, LogColorMapper,
    ColorBar, BasicTicker, LogTicker, Select, ColumnDataSource, CustomJS, Slider
)
from bokeh.palettes import (
    Viridis256, Turbo256, Plasma256, Inferno256, Magma256,
    Cividis256, Greys256, Blues256, Greens256, Reds256,
    Oranges256, Purples256
)
from bokeh.layouts import column, row


def plot_polygon_grid(vertices, values=None, width=800, height=600,
                       palette='Viridis256', line_color='black', line_width=1,
                       colorbar=True, colorbar_label=None, log_scale=False,
                       title='Polygon Grid', labels=None,
                       color_limits=None, out_of_range_colors=None,
                       nan_inf_color=None, value_names=None,
                       connections=None, connection_values=None,
                       connection_width=3.0, connection_border_color='white',
                       connection_palette=None, connection_log_scale=None,
                       connection_color_limits=None, connection_colorbar_label=None):
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
    values : array-like, shape (n_polygons,) or (n_polygons, m), or None
        Values associated with each polygon. These determine the fill color.
        Can be a 1D array or 2D matrix. If 2D, a dropdown control will be
        added to select which column to display.
        If None, all values are set to 0 (useful for visualizing geometry only).
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
    connections : array-like, shape (2, n_connections) or (n_connections, 2), optional
        Array defining connections between polygons. Each column (or row) contains
        a pair of polygon indices [i, j] indicating a connection from polygon i to j.
        If provided, lines will be drawn between polygon centers.
    connection_values : array-like, shape (n_connections,) or (n_connections, m), optional
        Values associated with each connection. These determine the line colors.
        Can be 1D array or 2D matrix. If 2D, must match the number of columns in values.
        If None and connections is provided, all connection values are set to 0.
        Uses the same color scale as the polygons.
    connection_width : float, default=3.0
        Initial width of connection lines in pixels. Can be adjusted via a slider
        in the plot controls.
    connection_border_color : str, default='white'
        Color of the border around connection lines. This helps distinguish lines
        from colored polygons. Set to None for no border.
    connection_palette : str, optional
        Color palette name for connections. If None (default), uses the same palette
        as polygons. Options: 'Viridis256', 'Turbo256', 'Plasma256', etc.
    connection_log_scale : bool, optional
        Whether to use logarithmic color scale for connections. If None (default),
        uses the same log_scale setting as polygons.
    connection_color_limits : tuple of (min, max), optional
        Tuple specifying the color scale limits for connections. Either element can
        be None to use the connection data's min/max. If not provided, uses
        (conn_data_min, conn_data_max). Values outside these limits will be clamped
        to the min/max colors of the palette. For example:
        - (10, 100): connection color scale 10-100
        - (10, None): connection color scale 10 to conn_data_max
        - (None, 100): connection color scale conn_data_min to 100
        - None: connection color scale from conn_data_min to conn_data_max
    connection_colorbar_label : str, optional
        Label for the connection colorbar. Only used when connections have an
        independent color scale. If None, uses 'Connection Value'.

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

    >>> # Geometry-only visualization with values=None
    >>> hex_grid = [make_hexagon(i, j, 0.5) for i in range(3) for j in range(3)]
    >>> panel = plot_polygon_grid(
    ...     hex_grid,
    ...     values=None,  # All values set to 0
    ...     title='Hexagonal Grid Geometry'
    ... )
    >>> show(panel)  # Useful for mesh visualization without data

    >>> # With connections between polygons
    >>> connections = np.array([[0, 1], [1, 3], [0, 2], [2, 3]])  # Connect pairs
    >>> conn_values = np.array([10, 20, 15, 25])  # Flow rates
    >>> panel = plot_polygon_grid(
    ...     vertices, values,
    ...     connections=connections,
    ...     connection_values=conn_values,
    ...     connection_width=5.0,
    ...     title='Grid with Flow Connections'
    ... )
    >>> show(panel)  # Lines drawn between connected polygons

    >>> # With independent color scale for connections
    >>> polygon_values = np.array([10, 20, 30, 40])  # Low range
    >>> conn_values = np.array([1000, 5000, 10000, 50000])  # High range
    >>> panel = plot_polygon_grid(
    ...     vertices, polygon_values,
    ...     connections=connections,
    ...     connection_values=conn_values,
    ...     palette='Viridis',  # Polygons use Viridis
    ...     colorbar_label='Temperature (°C)',
    ...     connection_palette='Plasma',  # Connections use Plasma
    ...     connection_log_scale=True,  # Log scale for connections
    ...     connection_color_limits=(1000, 10000),  # Clamp to 1k-10k range
    ...     connection_colorbar_label='Flow Rate (m³/day)',  # Custom label
    ...     title='Independent Connection Color Scale'
    ... )
    >>> show(panel)  # Two colorbars shown when connection scale is independent
    """
    # Handle values=None case by inferring polygon count from vertices
    if values is None:
        # Need to parse vertices first to determine n_polygons
        # We'll do a preliminary parse to get the count
        if isinstance(vertices, np.ndarray):
            if vertices.ndim == 3:
                n_polygons = vertices.shape[0]
            else:
                raise ValueError(
                    "When values=None, vertices must be array with shape (n_polygons, n_vertices, 2) "
                    "or a list of polygon arrays"
                )
        elif isinstance(vertices, (list, tuple)) and len(vertices) > 0:
            # Check if it's a list of lists (multi-set) or list of polygons (single set)
            first_elem = vertices[0]
            if isinstance(first_elem, (list, tuple)):
                if len(first_elem) > 0:
                    second_elem = first_elem[0]
                    if isinstance(second_elem, (list, tuple, np.ndarray)):
                        second_elem_arr = np.asarray(second_elem)
                        if second_elem_arr.ndim == 2 and second_elem_arr.shape[1] == 2:
                            # Multi-set: first_elem[0] is a polygon
                            n_polygons = len(first_elem)
                        else:
                            # Single set: first_elem is a polygon
                            n_polygons = len(vertices)
                    else:
                        n_polygons = len(vertices)
                else:
                    n_polygons = len(vertices)
            elif isinstance(first_elem, np.ndarray):
                if first_elem.ndim == 2 and first_elem.shape[1] == 2:
                    # Single set: each element is a polygon
                    n_polygons = len(vertices)
                elif first_elem.ndim == 3:
                    # Multi-set: each element is an array of polygons
                    n_polygons = first_elem.shape[0]
                else:
                    n_polygons = len(vertices)
            else:
                n_polygons = len(vertices)
        else:
            raise ValueError("vertices must be an array or list")

        # Create values array of zeros
        values = np.zeros(n_polygons)

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

    # Process connections if provided
    has_connections = False
    if connections is not None:
        connections = np.asarray(connections)

        # Accept both (2, n) and (n, 2) formats
        if connections.ndim != 2:
            raise ValueError(f"connections must be 2D array, got shape {connections.shape}")

        if connections.shape[0] == 2:
            # Shape is (2, n_connections) - transpose to (n_connections, 2)
            connections = connections.T
        elif connections.shape[1] != 2:
            raise ValueError(
                f"connections must have shape (2, n_connections) or (n_connections, 2), "
                f"got {connections.shape}"
            )

        n_connections = connections.shape[0]
        has_connections = True

        # Validate connection indices
        if np.any(connections < 0) or np.any(connections >= n_polygons):
            raise ValueError(
                f"connection indices must be in range [0, {n_polygons}), "
                f"got min={connections.min()}, max={connections.max()}"
            )

        # Process connection values
        if connection_values is None:
            # Default to zeros, replicated for all columns
            connection_values = np.zeros((n_connections, n_columns))
        else:
            connection_values = np.asarray(connection_values)

            # Check if it's a matrix
            if connection_values.ndim == 2:
                if connection_values.shape[0] != n_connections:
                    raise ValueError(
                        f"connection_values must have {n_connections} rows, "
                        f"got {connection_values.shape[0]}"
                    )
                if connection_values.shape[1] != n_columns:
                    raise ValueError(
                        f"connection_values must have {n_columns} columns to match values, "
                        f"got {connection_values.shape[1]}"
                    )
            elif connection_values.ndim == 1:
                if len(connection_values) != n_connections:
                    raise ValueError(
                        f"connection_values must have length {n_connections}, "
                        f"got {len(connection_values)}"
                    )
                # Make it a column vector for consistency
                connection_values = connection_values.reshape(-1, 1)
                # Replicate for all columns if values is a matrix
                if n_columns > 1:
                    connection_values = np.tile(connection_values, (1, n_columns))
            else:
                raise ValueError("connection_values must be 1D or 2D array")

        # Preprocess bidirectional connections
        # Detect pairs where both (i,j) and (j,i) exist
        # Determine if we'll use log scale for connections (needed for mean calculation)
        conn_use_log_scale = connection_log_scale if connection_log_scale is not None else log_scale

        # Create a dictionary to track bidirectional pairs
        connection_map = {}  # (min_idx, max_idx) -> [list of connection indices]
        bidirectional_info = {}  # connection_idx -> (is_bidirectional, forward_val, reverse_val, is_primary)

        for conn_idx in range(n_connections):
            i, j = connections[conn_idx]
            # Always store with smaller index first for consistency
            key = (min(i, j), max(i, j))
            if key not in connection_map:
                connection_map[key] = []
            connection_map[key].append((conn_idx, i, j))

        # Process each unique connection pair
        processed_connections = []
        processed_values = []
        keep_connection = np.ones(n_connections, dtype=bool)

        for key, conn_list in connection_map.items():
            if len(conn_list) == 1:
                # Unidirectional connection
                conn_idx, i, j = conn_list[0]
                bidirectional_info[conn_idx] = {
                    'is_bidirectional': False,
                    'from': i,
                    'to': j,
                    'forward_value': connection_values[conn_idx, :],
                    'reverse_value': None,
                    'combined_value': connection_values[conn_idx, :],
                }
            elif len(conn_list) == 2:
                # Bidirectional connection - merge into one
                conn_idx_0, i0, j0 = conn_list[0]
                conn_idx_1, i1, j1 = conn_list[1]

                # Use the first one as the primary (keep it), discard the second
                kept_idx = conn_idx_0
                removed_idx = conn_idx_1

                # Get values for both directions
                val_0 = connection_values[conn_idx_0, :].copy()
                val_1 = connection_values[conn_idx_1, :].copy()

                # Now determine which value corresponds to which direction of the KEPT connection
                # The kept connection goes from i0 to j0
                # We need to find which value corresponds to (i0→j0) and which to (j0→i0)
                if i0 == conn_list[0][1] and j0 == conn_list[0][2]:
                    # conn_list[0] is (i0→j0), so val_0 is the i0→j0 value
                    value_i_to_j = val_0
                    value_j_to_i = val_1
                else:
                    # conn_list[0] is (j0→i0), so val_0 is the j0→i0 value
                    value_i_to_j = val_1
                    value_j_to_i = val_0

                # Mark reverse connection for removal
                keep_connection[removed_idx] = False

                # Store bidirectional info with correctly mapped values
                # forward_value: value for the kept connection direction (i0→j0)
                # reverse_value: value for the opposite direction (j0→i0)
                bidirectional_info[kept_idx] = {
                    'is_bidirectional': True,
                    'from': i0,
                    'to': j0,
                    'forward_value': value_i_to_j,
                    'reverse_value': value_j_to_i,
                }
            else:
                # More than 2 connections between same pair - shouldn't happen normally
                # Just keep the first one
                for idx, (conn_idx, i, j) in enumerate(conn_list):
                    if idx > 0:
                        keep_connection[conn_idx] = False

        # Filter out removed connections
        connections = connections[keep_connection]
        connection_values = connection_values[keep_connection]

        # Rebuild bidirectional_info with new indices
        old_to_new_idx = {}
        new_idx = 0
        for old_idx in range(n_connections):
            if keep_connection[old_idx]:
                old_to_new_idx[old_idx] = new_idx
                new_idx += 1

        new_bidirectional_info = {}
        for old_idx, info in bidirectional_info.items():
            if old_idx in old_to_new_idx:
                new_bidirectional_info[old_to_new_idx[old_idx]] = info

        bidirectional_info = new_bidirectional_info
        n_connections = connections.shape[0]
    else:
        n_connections = 0
        connection_values = np.zeros((0, n_columns))  # Empty array with correct shape
        bidirectional_info = {}

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

    # Calculate polygon centers for connections (for all polygon sets)
    if has_connections:
        # Store centers for each column's polygon set
        all_centers = []
        for col_idx in range(n_columns):
            col_vertices = all_vertices_lists[col_idx]
            centers = []
            for poly_verts in col_vertices:
                # Calculate centroid
                center_x = np.mean(poly_verts[:, 0])
                center_y = np.mean(poly_verts[:, 1])
                centers.append([center_x, center_y])
            all_centers.append(np.array(centers))

        # Prepare connection line data for first column
        current_centers = all_centers[0]
        conn_x0 = []
        conn_y0 = []
        conn_x1 = []
        conn_y1 = []
        conn_vals = []

        for conn_idx in range(n_connections):
            i, j = connections[conn_idx]
            conn_x0.append(current_centers[i, 0])
            conn_y0.append(current_centers[i, 1])
            conn_x1.append(current_centers[j, 0])
            conn_y1.append(current_centers[j, 1])
            # Use forward value (not the mean) for display
            if conn_idx in bidirectional_info:
                conn_vals.append(bidirectional_info[conn_idx]['forward_value'][0])
            else:
                conn_vals.append(connection_values[conn_idx, 0])

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
    # Create unified "name" field for polygons
    polygon_names = []
    for i in range(n_polygons):
        if labels is not None and labels[i]:
            polygon_names.append(labels[i])
        else:
            polygon_names.append(str(i))

    base_data = {
        'xs': xs,
        'ys': ys,
        'face': face_ids,
        'label': label_list,
        'name': polygon_names,
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
            'name': [polygon_names[i] for i in in_range_indices],
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
            'name': [polygon_names[i] for i in below_min_indices],
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
            'name': [polygon_names[i] for i in above_max_indices],
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
                'name': [polygon_names[i] for i in nan_inf_indices],
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

    # Add connection lines if provided
    connection_renderers = []
    if has_connections:
        # Prepare labels for connection hover (From/To)
        conn_from_labels = []
        conn_to_labels = []
        conn_names = []  # Unified name field
        conn_is_bidirectional = []
        conn_forward_vals = []
        conn_reverse_vals = []

        for conn_idx in range(n_connections):
            i, j = connections[conn_idx]
            # Use label if available, otherwise use polygon number
            if labels is not None and labels[i] and labels[j]:
                from_label = labels[i]
                to_label = labels[j]
                conn_name = f"{from_label} → {to_label}"
            else:
                from_label = str(i)
                to_label = str(j)
                conn_name = f"{i} → {j}"
            conn_from_labels.append(from_label)
            conn_to_labels.append(to_label)
            conn_names.append(conn_name)

            # Add bidirectional information
            if conn_idx in bidirectional_info:
                info = bidirectional_info[conn_idx]
                conn_is_bidirectional.append(info['is_bidirectional'])
                conn_forward_vals.append(info['forward_value'][0])  # First column for initial display
                if info['is_bidirectional']:
                    conn_reverse_vals.append(info['reverse_value'][0])
                else:
                    conn_reverse_vals.append(None)
            else:
                conn_is_bidirectional.append(False)
                conn_forward_vals.append(conn_vals[conn_idx])
                conn_reverse_vals.append(None)

        # Create data source for connections
        conn_data = {
            'x0': conn_x0,
            'y0': conn_y0,
            'x1': conn_x1,
            'y1': conn_y1,
            'value': conn_vals,
            'name': conn_names,  # Unified name field
            'conn_id': list(range(n_connections)),
            'from_label': conn_from_labels,
            'to_label': conn_to_labels,
            'is_bidirectional': conn_is_bidirectional,
            'forward_value': conn_forward_vals,
            'reverse_value': conn_reverse_vals,
        }

        # Store all connection data for column switching
        # Use forward values (not mean) for display
        for col_idx in range(n_columns):
            # Use forward value for display (not the combined mean)
            val_col = []
            forward_vals_col = []
            reverse_vals_col = []
            for conn_idx in range(n_connections):
                if conn_idx in bidirectional_info:
                    info = bidirectional_info[conn_idx]
                    forward_val = info['forward_value'][col_idx]
                    val_col.append(forward_val)  # Use forward value for display
                    forward_vals_col.append(forward_val)
                    if info['is_bidirectional']:
                        reverse_vals_col.append(info['reverse_value'][col_idx])
                    else:
                        reverse_vals_col.append(None)
                else:
                    val = connection_values[conn_idx, col_idx]
                    val_col.append(val)
                    forward_vals_col.append(val)
                    reverse_vals_col.append(None)

            conn_data[f'value_{col_idx}'] = val_col
            conn_data[f'forward_value_{col_idx}'] = forward_vals_col
            conn_data[f'reverse_value_{col_idx}'] = reverse_vals_col

            # Store centers for this column
            centers = all_centers[col_idx]
            x0_col = [centers[connections[i, 0], 0] for i in range(n_connections)]
            y0_col = [centers[connections[i, 0], 1] for i in range(n_connections)]
            x1_col = [centers[connections[i, 1], 0] for i in range(n_connections)]
            y1_col = [centers[connections[i, 1], 1] for i in range(n_connections)]
            conn_data[f'x0_{col_idx}'] = x0_col
            conn_data[f'y0_{col_idx}'] = y0_col
            conn_data[f'x1_{col_idx}'] = x1_col
            conn_data[f'y1_{col_idx}'] = y1_col

        source_connections = ColumnDataSource(data=conn_data)

        # Create separate color mapper for connections if parameters are provided
        if connection_palette is not None or connection_log_scale is not None or connection_color_limits is not None:
            # Determine connection palette
            if connection_palette is not None:
                if isinstance(connection_palette, str) and connection_palette in palette_map:
                    conn_color_palette = palette_map[connection_palette]
                elif isinstance(connection_palette, str):
                    conn_color_palette = connection_palette
                else:
                    conn_color_palette = connection_palette
            else:
                # Use same palette as polygons
                conn_color_palette = color_palette

            # Determine connection log scale
            conn_log_scale = connection_log_scale if connection_log_scale is not None else log_scale

            # Calculate connection color scale limits
            # Collect all values including both forward and reverse for bidirectional connections
            all_conn_values = []
            for conn_idx in range(n_connections):
                if conn_idx in bidirectional_info:
                    info = bidirectional_info[conn_idx]
                    all_conn_values.extend(info['forward_value'])
                    if info['is_bidirectional']:
                        all_conn_values.extend(info['reverse_value'])
                else:
                    all_conn_values.extend(connection_values[conn_idx, :])

            all_conn_values = np.array(all_conn_values)
            finite_conn_values = all_conn_values[np.isfinite(all_conn_values)]

            if len(finite_conn_values) == 0:
                conn_vmin = 0
                conn_vmax = 1
            else:
                conn_limit_min = None
                conn_limit_max = None
                if connection_color_limits is not None:
                    if not isinstance(connection_color_limits, (tuple, list)) or len(connection_color_limits) != 2:
                        raise ValueError("connection_color_limits must be a tuple of (min, max)")
                    conn_limit_min, conn_limit_max = connection_color_limits

                if conn_limit_min is None:
                    conn_vmin = np.min(finite_conn_values)
                else:
                    conn_vmin = conn_limit_min

                if conn_limit_max is None:
                    conn_vmax = np.max(finite_conn_values)
                else:
                    conn_vmax = conn_limit_max

            # Handle log scale requirements for connections
            if conn_log_scale:
                if conn_vmin <= 0:
                    positive_conn_values = finite_conn_values[finite_conn_values > 0]
                    if len(positive_conn_values) == 0:
                        raise ValueError("Cannot use connection log scale with all non-positive values")
                    conn_vmin = np.min(positive_conn_values)
                    print(f"Warning: Adjusting connection vmin to {conn_vmin} for log scale (was <= 0)")

            # Create connection color mapper
            if conn_log_scale:
                connection_mapper = LogColorMapper(palette=conn_color_palette, low=conn_vmin, high=conn_vmax)
            else:
                connection_mapper = LinearColorMapper(palette=conn_color_palette, low=conn_vmin, high=conn_vmax)
        else:
            # Use the same mapper as polygons
            connection_mapper = mapper

        # Determine if we're using log scale for connections
        conn_use_log_for_gradient = conn_log_scale if (connection_palette is not None or
                                                        connection_log_scale is not None or
                                                        connection_color_limits is not None) else log_scale

        # Create gradient lines for bidirectional connections
        # For bidirectional connections, create multiple segments with varying colors
        n_gradient_segments = 20  # Number of segments for smooth gradient

        # Determine which connections need gradients (must be consistent across all columns)
        # A connection needs gradient segments if it's bidirectional AND has different values
        # in ANY column
        connections_need_gradient = np.zeros(n_connections, dtype=bool)
        for conn_idx in range(n_connections):
            if conn_idx in bidirectional_info:
                info = bidirectional_info[conn_idx]
                if info['is_bidirectional']:
                    # Check if values differ significantly in any column
                    for col_idx in range(n_columns):
                        forward_val = info['forward_value'][col_idx]
                        reverse_val = info['reverse_value'][col_idx]
                        rel_diff = abs(forward_val - reverse_val) / max(abs(forward_val), abs(reverse_val), 1e-10)
                        if rel_diff > 0.01:  # More than 1% difference
                            connections_need_gradient[conn_idx] = True
                            break

        # Function to create gradient data for a given column
        # IMPORTANT: All columns must produce the same structure (same number of segments)
        def create_gradient_for_column(col_idx):
            grad_x0 = []
            grad_y0 = []
            grad_x1 = []
            grad_y1 = []
            grad_values = []
            grad_conn_id = []
            grad_from_label = []
            grad_to_label = []
            grad_names = []
            grad_is_bidirectional = []

            # Get centers for this column
            centers = all_centers[col_idx]

            for conn_idx in range(n_connections):
                i, j = connections[conn_idx]
                x0, y0 = centers[i, 0], centers[i, 1]
                x1, y1 = centers[j, 0], centers[j, 1]

                is_bidir = conn_is_bidirectional[conn_idx]
                conn_name = conn_names[conn_idx]

                # Use pre-computed mask to ensure all columns have same structure
                if connections_need_gradient[conn_idx]:
                    # Create gradient segments
                    info = bidirectional_info[conn_idx]
                    forward_val = info['forward_value'][col_idx]
                    reverse_val = info['reverse_value'][col_idx]

                    for seg_idx in range(n_gradient_segments):
                        t0 = seg_idx / n_gradient_segments
                        t1 = (seg_idx + 1) / n_gradient_segments

                        # Interpolate position
                        seg_x0 = x0 + t0 * (x1 - x0)
                        seg_y0 = y0 + t0 * (y1 - y0)
                        seg_x1 = x0 + t1 * (x1 - x0)
                        seg_y1 = y0 + t1 * (y1 - y0)

                        # Interpolate value using appropriate scale
                        if conn_use_log_for_gradient:
                            # Log-space interpolation (geometric)
                            if forward_val > 0 and reverse_val > 0:
                                log_forward = np.log(forward_val)
                                log_reverse = np.log(reverse_val)
                                log_val = log_forward + t0 * (log_reverse - log_forward)
                                seg_val = np.exp(log_val)
                            elif forward_val > 0:
                                seg_val = forward_val
                            elif reverse_val > 0:
                                seg_val = reverse_val
                            else:
                                seg_val = 0
                        else:
                            # Linear interpolation
                            seg_val = forward_val + t0 * (reverse_val - forward_val)

                        grad_x0.append(seg_x0)
                        grad_y0.append(seg_y0)
                        grad_x1.append(seg_x1)
                        grad_y1.append(seg_y1)
                        grad_values.append(seg_val)
                        grad_conn_id.append(conn_idx)
                        grad_from_label.append(conn_from_labels[conn_idx])
                        grad_to_label.append(conn_to_labels[conn_idx])
                        grad_names.append(conn_name)
                        grad_is_bidirectional.append(True)
                else:
                    # Single segment for unidirectional or similar bidirectional values
                    grad_x0.append(x0)
                    grad_y0.append(y0)
                    grad_x1.append(x1)
                    grad_y1.append(y1)
                    grad_values.append(connection_values[conn_idx, col_idx])
                    grad_conn_id.append(conn_idx)
                    grad_from_label.append(conn_from_labels[conn_idx])
                    grad_to_label.append(conn_to_labels[conn_idx])
                    grad_names.append(conn_name)
                    grad_is_bidirectional.append(is_bidir)

            return {
                'x0': grad_x0,
                'y0': grad_y0,
                'x1': grad_x1,
                'y1': grad_y1,
                'value': grad_values,
                'name': grad_names,
                'conn_id': grad_conn_id,
                'from_label': grad_from_label,
                'to_label': grad_to_label,
                'is_bidirectional': grad_is_bidirectional,
            }

        # Create gradient data for first column
        gradient_data = create_gradient_for_column(0)

        # Store gradient data for all columns (for column switching)
        for col_idx in range(n_columns):
            col_grad_data = create_gradient_for_column(col_idx)
            for key in col_grad_data:
                gradient_data[f'{key}_{col_idx}'] = col_grad_data[key]

        source_gradient = ColumnDataSource(data=gradient_data)

        # Draw border lines (white/light) first for visibility
        if connection_border_color is not None:
            border_width = connection_width + 2  # Border slightly wider
            conn_border = p.segment(
                x0='x0', y0='y0', x1='x1', y1='y1',
                source=source_connections,
                line_color=connection_border_color,
                line_width=border_width,
                line_cap='round'
            )
            connection_renderers.append(conn_border)

        # Draw colored gradient connection lines
        conn_lines = p.segment(
            x0='x0', y0='y0', x1='x1', y1='y1',
            source=source_gradient,
            line_color={'field': 'value', 'transform': connection_mapper},
            line_width=connection_width,
            line_cap='round'
        )
        connection_renderers.append(conn_lines)

        # Store connection color scale info for colorbar
        has_independent_connection_scale = (connection_palette is not None or
                                           connection_log_scale is not None or
                                           connection_color_limits is not None)
    else:
        source_connections = None
        has_independent_connection_scale = False
        connection_mapper = None
        conn_log_scale = False
        conn_lines = None

    # Add unified hover tool for both polygons and connections
    # Using HTML formatting to hide field labels and center align
    unified_tooltips = """
        <div style="text-align: center;">
            <div><b>@name</b></div>
            <div>@value{0.0000}</div>
        </div>
    """

    # Collect all renderers for hover
    hover_renderers = all_patches.copy()
    if has_connections and conn_lines is not None:
        hover_renderers.append(conn_lines)

    hover = HoverTool(
        renderers=hover_renderers,
        tooltips=unified_tooltips,
        attachment="vertical",
        point_policy="follow_mouse",
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

        # Add second colorbar for connections if they have independent color scale
        if has_connections and has_independent_connection_scale:
            # Create ticker for connection colorbar
            if conn_log_scale:
                conn_ticker = LogTicker()
            else:
                conn_ticker = BasicTicker()

            conn_color_bar = ColorBar(
                color_mapper=connection_mapper,
                ticker=conn_ticker,
                label_standoff=12,
                border_line_color=None,
                location=(0, 0),
                title=connection_colorbar_label if connection_colorbar_label else 'Connection Value'
            )
            p.add_layout(conn_color_bar, 'right')

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
                source_conn=source_connections if has_connections else None,
                source_grad=source_gradient if has_connections else None,
                select=select,
                value_names=value_names,
                n_columns=n_columns,
                vmin=vmin,
                vmax=vmax,
                nan_inf_color=nan_inf_color,
                has_connections=has_connections,
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
                    const src_name = [];

                    for (let i = 0; i < n_polygons; i++) {
                        if (mask[i]) {
                            src_xs.push(new_xs[i]);
                            src_ys.push(new_ys[i]);
                            src_face.push(data['face'][i]);
                            src_value.push(new_values[i]);
                            src_label.push(data['label'][i]);
                            src_name.push(data['name'][i]);
                        }
                    }

                    src_data['xs'] = src_xs;
                    src_data['ys'] = src_ys;
                    src_data['face'] = src_face;
                    src_data['value'] = src_value;
                    src_data['label'] = src_label;
                    src_data['name'] = src_name;
                    src.change.emit();
                }

                // Update all sources
                updateSource(source_in, in_range);
                updateSource(source_below, below_min);
                updateSource(source_above, above_max);
                if (nan_inf_color !== null) {
                    updateSource(source_nan, nan_inf);
                }

                // Update connections if present
                if (has_connections && source_conn !== null) {
                    const conn_data = source_conn.data;
                    conn_data['value'] = conn_data['value_' + col_idx];
                    conn_data['forward_value'] = conn_data['forward_value_' + col_idx];
                    conn_data['reverse_value'] = conn_data['reverse_value_' + col_idx];
                    conn_data['x0'] = conn_data['x0_' + col_idx];
                    conn_data['y0'] = conn_data['y0_' + col_idx];
                    conn_data['x1'] = conn_data['x1_' + col_idx];
                    conn_data['y1'] = conn_data['y1_' + col_idx];
                    source_conn.change.emit();
                }

                // Update gradient segments if present
                if (has_connections && source_grad !== null) {
                    const grad_data = source_grad.data;
                    grad_data['x0'] = grad_data['x0_' + col_idx];
                    grad_data['y0'] = grad_data['y0_' + col_idx];
                    grad_data['x1'] = grad_data['x1_' + col_idx];
                    grad_data['y1'] = grad_data['y1_' + col_idx];
                    grad_data['value'] = grad_data['value_' + col_idx];
                    grad_data['name'] = grad_data['name_' + col_idx];
                    grad_data['from_label'] = grad_data['from_label_' + col_idx];
                    grad_data['to_label'] = grad_data['to_label_' + col_idx];
                    grad_data['is_bidirectional'] = grad_data['is_bidirectional_' + col_idx];
                    source_grad.change.emit();
                }

                source.change.emit();
            """
        )

        select.js_on_change('value', callback)

        # Add connection width slider if connections are present
        if has_connections:
            conn_width_slider = Slider(
                start=0.5,
                end=10.0,
                value=connection_width,
                step=0.5,
                title="Connection Line Width:",
                width=200
            )

            # JavaScript callback to update connection line widths
            conn_width_callback = CustomJS(
                args=dict(
                    slider=conn_width_slider,
                    renderers=connection_renderers,
                    border_offset=2 if connection_border_color is not None else 0
                ),
                code="""
                    const width = slider.value;
                    // Update each renderer
                    for (let i = 0; i < renderers.length; i++) {
                        if (i === 0 && border_offset > 0) {
                            // First renderer is border (if present)
                            renderers[i].glyph.line_width = width + border_offset;
                        } else {
                            // Main line renderer
                            renderers[i].glyph.line_width = width;
                        }
                    }
                """
            )
            conn_width_slider.js_on_change('value', conn_width_callback)

            # Create layout with all selectors and plot
            controls = row(select, palette_select, conn_width_slider)
            panel = column(controls, p)
        else:
            # Create layout with selectors and plot
            controls = row(select, palette_select)
            panel = column(controls, p)
    else:
        # No matrix values
        if has_connections:
            # Add connection width slider
            conn_width_slider = Slider(
                start=0.5,
                end=10.0,
                value=connection_width,
                step=0.5,
                title="Connection Line Width:",
                width=200
            )

            conn_width_callback = CustomJS(
                args=dict(
                    slider=conn_width_slider,
                    renderers=connection_renderers,
                    border_offset=2 if connection_border_color is not None else 0
                ),
                code="""
                    const width = slider.value;
                    for (let i = 0; i < renderers.length; i++) {
                        if (i === 0 && border_offset > 0) {
                            renderers[i].glyph.line_width = width + border_offset;
                        } else {
                            renderers[i].glyph.line_width = width;
                        }
                    }
                """
            )
            conn_width_slider.js_on_change('value', conn_width_callback)

            controls = row(palette_select, conn_width_slider)
            panel = column(controls, p)
        else:
            # Return as a panel with palette selector only
            panel = column(palette_select, p)

    return panel

if __name__ == "__main__":
    from bokeh.plotting import show

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
    values_ = np.array([[5, 15, 25, np.nan, 45, 55],[15, 16, 27, 38, 49, 500]]).T
    labels_ = np.array(['V=5', 'V=15', 'V=25', 'NaN', 'V=45', 'V=55'])
    connections_ = np.array([[0, 1], [1, 2], [2, 3], [3, 4],
                             [4, 5], [1, 0], [1, 4], [4, 1]])
    connection_values_ = np.array([[1000, 20], [25, 15], [50, 60], [70, 80],
                                   [90, 100], [1000, 25], [40, 0.55], [0.55, 0.55]])

    panel_limits = plot_polygon_grid(
        vertices=[vertices1, vertices2],
        values=values_,
        labels=labels_,
        connections=connections_,
        connection_values=connection_values_,
        connection_width=6.0,
        # connection_border_color='black',
        palette='Turbo',
        connection_log_scale=True,
        color_limits=(None, 100),
        out_of_range_colors=('blue', 'red'),
        nan_inf_color=None,
        colorbar_label='Cells',
        connection_colorbar_label='Connection',
        title='Map Example'
    )
    show(panel_limits)
