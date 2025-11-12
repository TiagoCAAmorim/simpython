"""
Plotting utilities for rsimpy.
"""
import numpy as np
from bokeh.plotting import figure
from bokeh.models import (
    HoverTool, LinearColorMapper, LogColorMapper,
    ColorBar, BasicTicker, LogTicker, Select, ColumnDataSource, CustomJS
)
from bokeh.palettes import Viridis256, Turbo256, Plasma256, Inferno256, Magma256
from bokeh.layouts import column


def plot_polygon_grid(vertices, values, width=800, height=600,
                       palette='Viridis256', line_color='black', line_width=1,
                       colorbar=True, colorbar_label=None, log_scale=False,
                       title='Polygon Grid', labels=None,
                       color_limits=None, out_of_range_color=None,
                       show_nan_inf=True, value_names=None):
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
    out_of_range_color : str or tuple of (str, str), default=None
        Color(s) for polygons with values outside color_limits.
        - None (default): values outside limits get min/max colors from the palette
        - Single color (e.g., 'gray'): both below and above limits use this color
        - Tuple (e.g., ('blue', 'red')): (color_below_min, color_above_max)
        - Tuple with None: e.g., (None, 'red') means below-min uses palette min color,
          above-max uses red
        Note: NaN and Inf values follow show_nan_inf parameter.
    show_nan_inf : bool, default=True
        Whether to display polygons with NaN or Inf values.
        - True: display as gray
        - False: hide these polygons (not rendered)
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
    ...     out_of_range_color=('blue', 'red'),  # Below=blue, Above=red
    ...     colorbar_label='Value'
    ... )
    >>> show(panel)  # Value 5 is blue, 15 and 25 colored, 35 is red

    >>> # Hide NaN/Inf polygons
    >>> values = np.array([1, np.nan, 3, np.inf])
    >>> panel = plot_polygon_grid(
    ...     vertices, values,
    ...     show_nan_inf=False,  # Don't show NaN/Inf
    ...     colorbar_label='Value'
    ... )
    >>> show(panel)  # Only polygons 0 and 2 are shown

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
    # Convert to numpy arrays
    vertices = np.asarray(vertices)
    values = np.asarray(values)

    # Validate inputs
    if vertices.ndim != 3 or vertices.shape[1] != 4 or vertices.shape[2] != 2:
        raise ValueError(
            f"vertices must have shape (n_polygons, 4, 2), got {vertices.shape}"
        )

    n_polygons = vertices.shape[0]

    # Check if values is a matrix
    is_matrix = values.ndim == 2
    if is_matrix:
        n_values, n_columns = values.shape
        if n_values != n_polygons:
            raise ValueError(
                f"values must have shape ({n_polygons}, m), got {values.shape}"
            )
        # Validate or create value_names
        if value_names is not None:
            value_names = np.asarray(value_names, dtype=str)
            if len(value_names) != n_columns:
                raise ValueError(
                    f"value_names must have length {n_columns}, got {len(value_names)}"
                )
        else:
            value_names = [f'Column {i}' for i in range(n_columns)]
    else:
        # Make it a column vector for consistency
        if values.ndim == 1:
            values = values.reshape(-1, 1)
            n_columns = 1
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

    # Normalize out_of_range_color to tuple format
    if out_of_range_color is None:
        color_below_min = None
        color_above_max = None
    elif isinstance(out_of_range_color, (tuple, list)):
        if len(out_of_range_color) != 2:
            raise ValueError("out_of_range_color tuple must have exactly 2 elements")
        color_below_min, color_above_max = out_of_range_color
    else:
        # Single value - use for both
        color_below_min = out_of_range_color
        color_above_max = out_of_range_color

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

    # Prepare data for patches glyph - handle matrix case
    xs = []  # List of lists of x coordinates for each polygon
    ys = []  # List of lists of y coordinates for each polygon
    face_ids = []  # Face numbers
    label_list = []  # Labels for each polygon

    for i in range(n_polygons):
        # Extract x and y coordinates for this polygon
        poly_x = vertices[i, :, 0].tolist()
        poly_y = vertices[i, :, 1].tolist()

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

    # 4. NaN/Inf polygons (show as gray or hide)
    if show_nan_inf:
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
                fill_color='gray',
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
                show_nan_inf=show_nan_inf,
            ),
            code="""
                // Find which column was selected
                const col_name = select.value;
                const col_idx = value_names.indexOf(col_name);

                // Get the data from the source
                const data = source.data;
                const n_polygons = data['xs'].length;

                // Update the active value column
                const new_values = data['value_' + col_idx];
                data['value'] = new_values;

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
                            src_xs.push(data['xs'][i]);
                            src_ys.push(data['ys'][i]);
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
                if (show_nan_inf) {
                    updateSource(source_nan, nan_inf);
                }

                source.change.emit();
            """
        )

        select.js_on_change('value', callback)

        # Create layout with selector and plot
        panel = column(select, p)
    else:
        # Return as a panel (layout) without selector
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
    values_limits = np.array([[5, 15, 25, 35, 45, 55],[15, 115, 125, 135, 145, 155]]).T
    labels_limits = np.array(['V=5', 'V=15', 'V=25', 'V=35', 'V=45', 'V=55'])

    panel_limits = plot_polygon_grid(
        vertices_limits, values_limits,
        labels=labels_limits,
        color_limits=(20, 40),
        colorbar_label='Value',
        title='Color Limits Example (20-40, others gray)'
    )
    show(panel_limits)
