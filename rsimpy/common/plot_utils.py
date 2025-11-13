# pylint: disable=too-many-lines
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


def _get_palette_map():
    """Get the mapping of palette names to Bokeh palettes."""
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

    return palette_map


def _infer_polygon_count(vertices):
    """Infer the number of polygons from vertices structure."""
    if isinstance(vertices, np.ndarray):
        if vertices.ndim == 3:
            return vertices.shape[0]
        else:
            raise ValueError(
                "When values=None, vertices must be array with shape (n_polygons, n_vertices, 2) "
                "or a list of polygon arrays"
            )
    elif isinstance(vertices, (list, tuple)) and len(vertices) > 0:
        first_elem = vertices[0]
        if isinstance(first_elem, (list, tuple)):
            if len(first_elem) > 0:
                second_elem = first_elem[0]
                if isinstance(second_elem, (list, tuple, np.ndarray)):
                    second_elem_arr = np.asarray(second_elem)
                    if second_elem_arr.ndim == 2 and second_elem_arr.shape[1] == 2:
                        return len(first_elem)
                    else:
                        return len(vertices)
                else:
                    return len(vertices)
            else:
                return len(vertices)
        elif isinstance(first_elem, np.ndarray):
            if first_elem.ndim == 2 and first_elem.shape[1] == 2:
                return len(vertices)
            elif first_elem.ndim == 3:
                return first_elem.shape[0]
            else:
                return len(vertices)
        else:
            return len(vertices)
    else:
        raise ValueError("vertices must be an array or list")


def _count_polygon_sets(vertices):
    """Count the number of polygon sets in vertices structure."""
    if isinstance(vertices, (list, tuple)) and len(vertices) > 0:
        first_elem = vertices[0]
        if isinstance(first_elem, (list, tuple)):
            if len(first_elem) > 0:
                second_elem = first_elem[0]
                if isinstance(second_elem, (list, tuple, np.ndarray)):
                    second_elem_arr = np.asarray(second_elem)
                    if second_elem_arr.ndim == 2 and second_elem_arr.shape[1] == 2:
                        # Multi-set: vertices is a list of polygon sets
                        return len(vertices)
        elif isinstance(first_elem, np.ndarray):
            if first_elem.ndim == 3:
                # Multi-set: vertices is a list of arrays of polygons
                return len(vertices)
    # Single set
    return 1


def _normalize_values(values, n_polygons_inferred=None, n_sets_inferred=None):
    """
    Normalize values to 2D array format.

    Returns
    -------
    values : np.ndarray
        2D array of shape (n_polygons, n_columns)
    n_polygons : int
        Number of polygons
    n_columns : int
        Number of value columns
    """
    if values is None:
        if n_polygons_inferred is None:
            raise ValueError("n_polygons_inferred required when values is None")
        # Create a matrix with zeros, one column per polygon set
        n_columns = n_sets_inferred if n_sets_inferred is not None else 1
        values = np.zeros((n_polygons_inferred, n_columns))

    values = np.asarray(values)

    if values.ndim == 2:
        n_polygons, n_columns = values.shape
    elif values.ndim == 1:
        values = values.reshape(-1, 1)
        n_columns = 1
        n_polygons = values.shape[0]
    else:
        raise ValueError("values must be 1D or 2D array")

    return values, n_polygons, n_columns


def _is_multi_set_vertices(vertices):
    """Determine if vertices contains multiple polygon sets."""
    if not isinstance(vertices, (list, tuple)) or len(vertices) == 0:
        return False

    first_elem = vertices[0]
    if isinstance(first_elem, (list, tuple)):
        if len(first_elem) > 0:
            second_elem = first_elem[0]
            if isinstance(second_elem, (list, tuple, np.ndarray)):
                second_elem_arr = np.asarray(second_elem)
                if second_elem_arr.ndim == 2 and second_elem_arr.shape[1] == 2:
                    return True
    elif isinstance(first_elem, np.ndarray):
        if first_elem.ndim == 3:
            return True

    return False


def _validate_polygon(poly_arr, index, set_index=None):
    """Validate a single polygon array."""
    prefix = f"vertices[{set_index}][{index}]" if set_index is not None else f"vertices[{index}]"

    if poly_arr.ndim != 2 or poly_arr.shape[1] != 2:
        raise ValueError(f"{prefix} must have shape (n_vertices, 2), got {poly_arr.shape}")
    if poly_arr.shape[0] < 3:
        raise ValueError(f"{prefix} must have at least 3 vertices, got {poly_arr.shape[0]}")


def _parse_single_polygon_set(vert_set, n_polygons, set_index=None):
    """Parse a single set of polygons into a list of arrays."""
    vert_list = []

    if isinstance(vert_set, np.ndarray):
        if vert_set.ndim == 3:
            if vert_set.shape[0] != n_polygons:
                prefix = f"vertices[{set_index}]" if set_index is not None else "vertices"
                raise ValueError(
                    f"{prefix} must have {n_polygons} polygons, got {vert_set.shape[0]}"
                )
            for i in range(n_polygons):
                vert_list.append(vert_set[i])
        else:
            prefix = f"vertices[{set_index}]" if set_index is not None else "vertices"
            raise ValueError(f"{prefix} array must have 3 dimensions, got {vert_set.ndim}")
    elif isinstance(vert_set, (list, tuple)):
        if len(vert_set) != n_polygons:
            prefix = f"vertices[{set_index}]" if set_index is not None else "vertices"
            raise ValueError(f"{prefix} must have {n_polygons} polygons, got {len(vert_set)}")
        for i, poly in enumerate(vert_set):
            poly_arr = np.asarray(poly)
            _validate_polygon(poly_arr, i, set_index)
            vert_list.append(poly_arr)
    else:
        prefix = f"vertices[{set_index}]" if set_index is not None else "vertices"
        raise ValueError(f"{prefix} must be array or list")

    return vert_list


def _parse_vertices(vertices, n_polygons, n_columns):
    """
    Parse vertices structure into list of polygon sets.

    Returns
    -------
    all_vertices_lists : list of lists
        List of n_columns polygon sets, each containing n_polygons polygon arrays
    """
    vertices_are_multi_set = _is_multi_set_vertices(vertices)

    if vertices_are_multi_set:
        # Multiple polygon sets (one per column)
        if len(vertices) != n_columns:
            raise ValueError(
                f"When providing multiple polygon sets, must have {n_columns} sets "
                f"(one per data column), got {len(vertices)}"
            )

        all_vertices_lists = []
        for col_idx, vert_set in enumerate(vertices):
            vert_list = _parse_single_polygon_set(vert_set, n_polygons, col_idx)
            all_vertices_lists.append(vert_list)
    else:
        # Single polygon set (used for all columns)
        vertices_list = _parse_single_polygon_set(vertices, n_polygons)
        all_vertices_lists = [vertices_list for _ in range(n_columns)]

    return all_vertices_lists


def _normalize_color_limits(color_limits, values, log_scale):
    """
    Calculate and validate color scale limits.

    Returns
    -------
    vmin : float
        Minimum value for color scale
    vmax : float
        Maximum value for color scale
    """
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
            positive_values = finite_values[finite_values > 0]
            if len(positive_values) == 0:
                # raise ValueError("Cannot use log scale with all non-positive values")
                vmin = 0.0  # Default to 1.0 if no positive values
                vmax = 1.0
            else:
                vmin = np.min(positive_values)
            print(f"Warning: Adjusting vmin to {vmin} for log scale (was <= 0)")

    return vmin, vmax


def _normalize_out_of_range_colors(out_of_range_colors):
    """
    Normalize out_of_range_colors parameter to tuple format.

    Returns
    -------
    color_below_min : str or None
    color_above_max : str or None
    """
    if out_of_range_colors is None:
        return None, None
    elif isinstance(out_of_range_colors, (tuple, list)):
        if len(out_of_range_colors) != 2:
            raise ValueError("out_of_range_colors tuple must have exactly 2 elements")
        return out_of_range_colors[0], out_of_range_colors[1]
    else:
        # Single value - use for both
        return out_of_range_colors, out_of_range_colors


def _create_color_mapper(palette, log_scale, vmin, vmax):
    """
    Create a color mapper for the given palette and scale.

    Returns
    -------
    mapper : ColorMapper
    ticker : Ticker
    color_palette : palette object
    """
    palette_map = _get_palette_map()

    if isinstance(palette, str) and palette in palette_map:
        color_palette = palette_map[palette]
    elif isinstance(palette, str):
        color_palette = palette
    else:
        color_palette = palette

    if log_scale:
        mapper = LogColorMapper(palette=color_palette, low=vmin, high=vmax)
        ticker = LogTicker()
    else:
        mapper = LinearColorMapper(palette=color_palette, low=vmin, high=vmax)
        ticker = BasicTicker()

    return mapper, ticker, color_palette


def _categorize_polygons(values, vmin, vmax):
    """
    Categorize polygons based on their values.

    Returns
    -------
    finite_mask : np.ndarray (bool)
    nan_inf_mask : np.ndarray (bool)
    below_min_mask : np.ndarray (bool)
    above_max_mask : np.ndarray (bool)
    in_range_mask : np.ndarray (bool)
    """
    n_polygons = len(values)
    finite_mask = np.isfinite(values)
    nan_inf_mask = ~finite_mask

    below_min_mask = np.zeros(n_polygons, dtype=bool)
    above_max_mask = np.zeros(n_polygons, dtype=bool)
    in_range_mask = np.zeros(n_polygons, dtype=bool)

    finite_indices = np.where(finite_mask)[0]
    for idx in finite_indices:
        val = values[idx]
        if val < vmin:
            below_min_mask[idx] = True
        elif val > vmax:
            above_max_mask[idx] = True
        else:
            in_range_mask[idx] = True

    return finite_mask, nan_inf_mask, below_min_mask, above_max_mask, in_range_mask


def _calculate_plot_range(all_vertices_lists, values, nan_inf_color):
    """
    Calculate plot range with margins.

    Returns
    -------
    x_range : tuple of (min, max)
    y_range : tuple of (min, max)
    """
    n_columns = len(all_vertices_lists)
    all_x_coords = []
    all_y_coords = []

    for col_idx in range(n_columns):
        col_vertices = all_vertices_lists[col_idx]
        col_values = values[:, col_idx]

        for poly_idx, poly_verts in enumerate(col_vertices):
            # Include polygon if finite or will be rendered
            if np.isfinite(col_values[poly_idx]) or nan_inf_color is not None:
                all_x_coords.append(poly_verts[:, 0])
                all_y_coords.append(poly_verts[:, 1])

    if len(all_x_coords) == 0:
        return (0, 1), (0, 1)

    all_x = np.concatenate(all_x_coords)
    all_y = np.concatenate(all_y_coords)

    x_range_val = all_x.max() - all_x.min()
    y_range_val = all_y.max() - all_y.min()
    x_margin = x_range_val * 0.02 if x_range_val > 0 else 1
    y_margin = y_range_val * 0.02 if y_range_val > 0 else 1

    return (all_x.min() - x_margin, all_x.max() + x_margin), \
           (all_y.min() - y_margin, all_y.max() + y_margin)


def _create_polygon_names(n_polygons, labels):
    """Create unified name field for polygons."""
    polygon_names = []
    for i in range(n_polygons):
        if labels is not None and labels[i]:
            polygon_names.append(labels[i])
        else:
            polygon_names.append(str(i))
    return polygon_names


def _prepare_base_data(
        xs, ys, face_ids, label_list, polygon_names,
        values, all_vertices_lists, current_values, in_range_mask
    ):
    """Prepare base data dictionary for ColumnDataSource."""
    n_columns = values.shape[1]

    base_data = {
        'xs': xs,
        'ys': ys,
        'face': face_ids,
        'label': label_list,
        'name': polygon_names,
    }

    # Add all value columns
    for col_idx in range(n_columns):
        base_data[f'value_{col_idx}'] = values[:, col_idx].tolist()

    # Add all vertices columns
    for col_idx in range(n_columns):
        col_vertices = all_vertices_lists[col_idx]
        xs_col = [v[:, 0].tolist() for v in col_vertices]
        ys_col = [v[:, 1].tolist() for v in col_vertices]
        base_data[f'xs_{col_idx}'] = xs_col
        base_data[f'ys_{col_idx}'] = ys_col

    # Set active value column
    base_data['value'] = current_values.tolist()
    base_data['in_range'] = in_range_mask.tolist()

    return base_data


def _create_patch_source(xs, ys, face_ids, values, label_list, polygon_names, indices):
    """Create a ColumnDataSource for a specific category of patches."""
    if len(indices) == 0:
        return None

    data = {
        'xs': [xs[i] for i in indices],
        'ys': [ys[i] for i in indices],
        'face': [face_ids[i] for i in indices],
        'value': [values[i] for i in indices],
        'label': [label_list[i] for i in indices],
        'name': [polygon_names[i] for i in indices],
    }
    return ColumnDataSource(data=data)


def _add_patches_to_plot(p, source, mapper, line_color, line_width, fill_color=None):
    """Add patches to plot with specified styling."""
    if fill_color is None:
        # Use mapper
        return p.patches(
            'xs', 'ys',
            source=source,
            fill_color={'field': 'value', 'transform': mapper},
            line_color=line_color,
            line_width=line_width,
        )
    else:
        # Use fixed color
        return p.patches(
            'xs', 'ys',
            source=source,
            fill_color=fill_color,
            line_color=line_color,
            line_width=line_width,
        )


def _calculate_polygon_centers(vertices_list):
    """Calculate centroids for a list of polygons."""
    centers = []
    for poly_verts in vertices_list:
        center_x = np.mean(poly_verts[:, 0])
        center_y = np.mean(poly_verts[:, 1])
        centers.append([center_x, center_y])
    return np.array(centers)


def _process_connections(connections, n_polygons):
    """
    Validate and normalize connection array format.

    Returns
    -------
    connections : np.ndarray
        Array of shape (n_connections, 2)
    """
    connections = np.asarray(connections)

    if connections.ndim != 2:
        raise ValueError(f"connections must be 2D array, got shape {connections.shape}")

    if connections.shape[0] == 2:
        connections = connections.T
    elif connections.shape[1] != 2:
        raise ValueError(
            f"connections must have shape (2, n_connections) or (n_connections, 2), "
            f"got {connections.shape}"
        )

    if np.any(connections < 0) or np.any(connections >= n_polygons):
        raise ValueError(
            f"connection indices must be in range [0, {n_polygons}), "
            f"got min={connections.min()}, max={connections.max()}"
        )

    return connections


def _normalize_connection_values(connection_values, n_connections, n_columns):
    """Normalize connection values to 2D array format."""
    if connection_values is None:
        return np.zeros((n_connections, n_columns))

    connection_values = np.asarray(connection_values)

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
        connection_values = connection_values.reshape(-1, 1)
        if n_columns > 1:
            connection_values = np.tile(connection_values, (1, n_columns))
    else:
        raise ValueError("connection_values must be 1D or 2D array")

    return connection_values


def _detect_bidirectional_connections(connections, connection_values, n_connections):
    """
    Detect and process bidirectional connections.

    Returns
    -------
    connections : np.ndarray
        Filtered connections array
    connection_values : np.ndarray
        Filtered connection values array
    bidirectional_info : dict
        Information about bidirectional connections
    """
    connection_map = {}
    bidirectional_info = {}

    for conn_idx in range(n_connections):
        i, j = connections[conn_idx]
        key = (min(i, j), max(i, j))
        if key not in connection_map:
            connection_map[key] = []
        connection_map[key].append((conn_idx, i, j))

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
            conn_idx_1, _, _ = conn_list[1]

            kept_idx = conn_idx_0
            removed_idx = conn_idx_1

            val_0 = connection_values[conn_idx_0, :].copy()
            val_1 = connection_values[conn_idx_1, :].copy()

            if i0 == conn_list[0][1] and j0 == conn_list[0][2]:
                value_i_to_j = val_0
                value_j_to_i = val_1
            else:
                value_i_to_j = val_1
                value_j_to_i = val_0

            keep_connection[removed_idx] = False

            bidirectional_info[kept_idx] = {
                'is_bidirectional': True,
                'from': i0,
                'to': j0,
                'forward_value': value_i_to_j,
                'reverse_value': value_j_to_i,
            }
        else:
            # More than 2 connections - keep first only
            for idx, (conn_idx, i, j) in enumerate(conn_list):
                if idx > 0:
                    keep_connection[conn_idx] = False

    # Filter connections and rebuild bidirectional_info
    connections = connections[keep_connection]
    connection_values = connection_values[keep_connection]

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

    return connections, connection_values, new_bidirectional_info


def _determine_gradient_needs(bidirectional_info, n_connections, n_columns):
    """Determine which connections need gradient segments."""
    connections_need_gradient = np.zeros(n_connections, dtype=bool)

    for conn_idx in range(n_connections):
        if conn_idx in bidirectional_info:
            info = bidirectional_info[conn_idx]
            if info['is_bidirectional']:
                for col_idx in range(n_columns):
                    forward_val = info['forward_value'][col_idx]
                    reverse_val = info['reverse_value'][col_idx]
                    num = abs(forward_val - reverse_val)
                    denom = max(abs(forward_val), abs(reverse_val), 1e-10)
                    rel_diff = num / denom
                    if rel_diff > 0.01:
                        connections_need_gradient[conn_idx] = True
                        break

    return connections_need_gradient


def _create_gradient_segments(
        conn_idx, connections, all_centers, col_idx, bidirectional_info,
        connection_values, connections_need_gradient, conn_use_log_for_gradient,
        n_gradient_segments=10
    ):
    """Create gradient segments for a single connection."""
    i, j = connections[conn_idx]
    x0, y0 = all_centers[col_idx][i, 0], all_centers[col_idx][i, 1]
    x1, y1 = all_centers[col_idx][j, 0], all_centers[col_idx][j, 1]

    if connections_need_gradient[conn_idx]:
        info = bidirectional_info[conn_idx]
        forward_val = info['forward_value'][col_idx]
        reverse_val = info['reverse_value'][col_idx]

        segments = []
        for seg_idx in range(n_gradient_segments):
            t0 = seg_idx / n_gradient_segments
            t1 = (seg_idx + 1) / n_gradient_segments
            t_val = seg_idx / (n_gradient_segments - 1)

            seg_x0 = x0 + t0 * (x1 - x0)
            seg_y0 = y0 + t0 * (y1 - y0)
            seg_x1 = x0 + t1 * (x1 - x0)
            seg_y1 = y0 + t1 * (y1 - y0)

            # Interpolate value
            if conn_use_log_for_gradient:
                if forward_val > 0 and reverse_val > 0:
                    log_forward = np.log(forward_val)
                    log_reverse = np.log(reverse_val)
                    log_val = log_forward + t_val * (log_reverse - log_forward)
                    seg_val = np.exp(log_val)
                elif forward_val > 0:
                    seg_val = forward_val
                elif reverse_val > 0:
                    seg_val = reverse_val
                else:
                    seg_val = 0
            else:
                seg_val = forward_val + t_val * (reverse_val - forward_val)

            segments.append((seg_x0, seg_y0, seg_x1, seg_y1, seg_val))

        return segments
    else:
        # Single segment
        seg_val = connection_values[conn_idx, col_idx]
        return [(x0, y0, x1, y1, seg_val)]


def _prepare_connection_data(connections, connection_values, all_centers, labels,
                              bidirectional_info, connections_need_gradient,
                              conn_use_log_for_gradient, n_columns):
    """Prepare connection line and gradient data."""
    n_connections = connections.shape[0]

    # Prepare main connection data
    current_centers = all_centers[0]
    conn_x0 = []
    conn_y0 = []
    conn_x1 = []
    conn_y1 = []
    conn_vals = []
    conn_from_labels = []
    conn_to_labels = []
    conn_names = []
    conn_is_bidirectional = []
    conn_forward_vals = []
    conn_reverse_vals = []

    for conn_idx in range(n_connections):
        i, j = connections[conn_idx]
        conn_x0.append(current_centers[i, 0])
        conn_y0.append(current_centers[i, 1])
        conn_x1.append(current_centers[j, 0])
        conn_y1.append(current_centers[j, 1])

        # Prepare labels
        if labels is not None and labels[i] and labels[j]:
            from_label = labels[i]
            to_label = labels[j]
        else:
            from_label = str(i)
            to_label = str(j)

        # Check if bidirectional for arrow selection
        is_bidir = (conn_idx in bidirectional_info and \
                    bidirectional_info[conn_idx]['is_bidirectional'])
        arrow = "↔" if is_bidir else "→"

        if labels is not None and labels[i] and labels[j]:
            conn_name = f"{from_label}{arrow}{to_label}"
        else:
            conn_name = f"{i}{arrow}{j}"

        conn_from_labels.append(from_label)
        conn_to_labels.append(to_label)
        conn_names.append(conn_name)

        # Add bidirectional information
        if conn_idx in bidirectional_info:
            info = bidirectional_info[conn_idx]
            conn_is_bidirectional.append(info['is_bidirectional'])
            conn_forward_vals.append(info['forward_value'][0])
            if info['is_bidirectional']:
                conn_vals.append(info['forward_value'][0])
                conn_reverse_vals.append(info['reverse_value'][0])
            else:
                conn_vals.append(info['forward_value'][0])
                conn_reverse_vals.append(None)
        else:
            conn_is_bidirectional.append(False)
            conn_vals.append(connection_values[conn_idx, 0])
            conn_forward_vals.append(connection_values[conn_idx, 0])
            conn_reverse_vals.append(None)

    # Create connection data dictionary
    conn_data = {
        'x0': conn_x0,
        'y0': conn_y0,
        'x1': conn_x1,
        'y1': conn_y1,
        'value': conn_vals,
        'name': conn_names,
        'conn_id': list(range(n_connections)),
        'from_label': conn_from_labels,
        'to_label': conn_to_labels,
        'is_bidirectional': conn_is_bidirectional,
        'forward_value': conn_forward_vals,
        'reverse_value': conn_reverse_vals,
    }

    # Store all columns
    for col_idx in range(n_columns):
        val_col = []
        forward_vals_col = []
        reverse_vals_col = []

        for conn_idx in range(n_connections):
            if conn_idx in bidirectional_info:
                info = bidirectional_info[conn_idx]
                forward_val = info['forward_value'][col_idx]
                val_col.append(forward_val)
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

        centers = all_centers[col_idx]
        x0_col = [centers[connections[i, 0], 0] for i in range(n_connections)]
        y0_col = [centers[connections[i, 0], 1] for i in range(n_connections)]
        x1_col = [centers[connections[i, 1], 0] for i in range(n_connections)]
        y1_col = [centers[connections[i, 1], 1] for i in range(n_connections)]
        conn_data[f'x0_{col_idx}'] = x0_col
        conn_data[f'y0_{col_idx}'] = y0_col
        conn_data[f'x1_{col_idx}'] = x1_col
        conn_data[f'y1_{col_idx}'] = y1_col

    # Create gradient data
    gradient_data = {}
    for col_idx in range(n_columns):
        grad_x0, grad_y0, grad_x1, grad_y1 = [], [], [], []
        grad_values, grad_conn_id = [], []
        grad_from_label, grad_to_label, grad_names = [], [], []
        grad_is_bidirectional = []

        for conn_idx in range(n_connections):
            segments = _create_gradient_segments(
                conn_idx, connections, all_centers, col_idx, bidirectional_info,
                connection_values, connections_need_gradient, conn_use_log_for_gradient
            )

            for seg_x0, seg_y0, seg_x1, seg_y1, seg_val in segments:
                grad_x0.append(seg_x0)
                grad_y0.append(seg_y0)
                grad_x1.append(seg_x1)
                grad_y1.append(seg_y1)
                grad_values.append(seg_val)
                grad_conn_id.append(conn_idx)
                grad_from_label.append(conn_from_labels[conn_idx])
                grad_to_label.append(conn_to_labels[conn_idx])
                grad_names.append(conn_names[conn_idx])
                grad_is_bidirectional.append(conn_is_bidirectional[conn_idx])

        # Store gradient data
        if col_idx == 0:
            gradient_data['x0'] = grad_x0
            gradient_data['y0'] = grad_y0
            gradient_data['x1'] = grad_x1
            gradient_data['y1'] = grad_y1
            gradient_data['value'] = grad_values
            gradient_data['name'] = grad_names
            gradient_data['conn_id'] = grad_conn_id
            gradient_data['from_label'] = grad_from_label
            gradient_data['to_label'] = grad_to_label
            gradient_data['is_bidirectional'] = grad_is_bidirectional

        gradient_data[f'x0_{col_idx}'] = grad_x0
        gradient_data[f'y0_{col_idx}'] = grad_y0
        gradient_data[f'x1_{col_idx}'] = grad_x1
        gradient_data[f'y1_{col_idx}'] = grad_y1
        gradient_data[f'value_{col_idx}'] = grad_values
        gradient_data[f'name_{col_idx}'] = grad_names
        gradient_data[f'from_label_{col_idx}'] = grad_from_label
        gradient_data[f'to_label_{col_idx}'] = grad_to_label
        gradient_data[f'is_bidirectional_{col_idx}'] = grad_is_bidirectional

    return conn_data, gradient_data


def _create_connection_color_mapper(
        connection_palette, connection_log_scale, connection_color_limits,
        connection_values, bidirectional_info, n_connections,
        color_palette, log_scale
    ):
    """Create color mapper for connections if independent scale requested."""
    if connection_palette is None and \
        connection_log_scale is None and \
            connection_color_limits is None:
        return None, None

    palette_map = _get_palette_map()

    # Determine connection palette
    if connection_palette is not None:
        if isinstance(connection_palette, str) and connection_palette in palette_map:
            conn_color_palette = palette_map[connection_palette]
        elif isinstance(connection_palette, str):
            conn_color_palette = connection_palette
        else:
            conn_color_palette = connection_palette
    else:
        conn_color_palette = color_palette

    # Determine connection log scale
    conn_log_scale = connection_log_scale if connection_log_scale is not None else log_scale

    # Calculate connection color scale limits
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
        conn_vmin, conn_vmax = 0, 1
    else:
        conn_limit_min, conn_limit_max = None, None
        if connection_color_limits is not None:
            if not isinstance(connection_color_limits, (tuple, list)) or \
                len(connection_color_limits) != 2:
                raise ValueError("connection_color_limits must be a tuple of (min, max)")
            conn_limit_min, conn_limit_max = connection_color_limits

        conn_vmin = np.min(finite_conn_values) if conn_limit_min is None else conn_limit_min
        conn_vmax = np.max(finite_conn_values) if conn_limit_max is None else conn_limit_max

    # Handle log scale requirements
    if conn_log_scale and conn_vmin <= 0:
        positive_conn_values = finite_conn_values[finite_conn_values > 0]
        if len(positive_conn_values) == 0:
            raise ValueError("Cannot use connection log scale with all non-positive values")
        conn_vmin = np.min(positive_conn_values)
        print(f"Warning: Adjusting connection vmin to {conn_vmin} for log scale (was <= 0)")

    # Create mapper
    if conn_log_scale:
        connection_mapper = LogColorMapper(
            palette=conn_color_palette, low=conn_vmin, high=conn_vmax
        )
    else:
        connection_mapper = LinearColorMapper(
            palette=conn_color_palette, low=conn_vmin, high=conn_vmax
        )

    return connection_mapper, conn_log_scale


def _create_palette_selector(initial_palette, mapper):
    """Create palette selector widget with callback."""
    palette_options = [
        'Viridis', 'Turbo', 'Plasma', 'Inferno', 'Magma', 'Cividis',
        'Greys', 'Blues', 'Greens', 'Reds', 'Oranges', 'Purples'
    ]
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

    palette_map = _get_palette_map()
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
    return palette_select


def _create_column_selector(
        value_names, source, source_in_range, source_below_min, source_above_max,
        source_nan_inf, source_connections, source_gradient, vmin, vmax,
        nan_inf_color, has_connections
    ):
    """Create column selector widget with callback for matrix data."""
    select = Select(
        title="Select Data Column:",
        value=value_names[0],
        options=list(value_names),
        width=200
    )

    callback = CustomJS(
        args=dict(
            source=source,
            source_in=source_in_range,
            source_below=source_below_min,
            source_above=source_above_max,
            source_nan=source_nan_inf,
            source_conn=source_connections,
            source_grad=source_gradient,
            select=select,
            value_names=value_names,
            n_columns=len(value_names),
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
    return select


def _create_connection_width_slider(
        connection_width, connection_renderers, connection_border_color
    ):
    """Create connection width slider widget with callback."""
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
    return conn_width_slider


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
    # Handle values=None case by inferring polygon count and number of sets from vertices
    if values is None:
        n_polygons_inferred = _infer_polygon_count(vertices)
        n_sets_inferred = _count_polygon_sets(vertices)
    else:
        n_polygons_inferred = None
        n_sets_inferred = None

    # Normalize values to 2D array
    values, n_polygons, n_columns = _normalize_values(values, n_polygons_inferred, n_sets_inferred)
    is_matrix = n_columns > 1

    # Parse vertices into list of polygon sets
    all_vertices_lists = _parse_vertices(vertices, n_polygons, n_columns)

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
        connections = _process_connections(connections, n_polygons)
        n_connections = connections.shape[0]
        has_connections = True

        connection_values = _normalize_connection_values(
            connection_values, n_connections, n_columns
        )
        connections, connection_values, bidirectional_info = _detect_bidirectional_connections(
            connections, connection_values, n_connections
        )
        n_connections = connections.shape[0]
    else:
        n_connections = 0
        connection_values = np.zeros((0, n_columns))
        bidirectional_info = {}

    # Normalize out_of_range_colors to tuple format
    color_below_min, color_above_max = _normalize_out_of_range_colors(out_of_range_colors)

    # Calculate color scale limits
    vmin, vmax = _normalize_color_limits(color_limits, values, log_scale)

    # Create color mapper
    mapper, ticker, color_palette = _create_color_mapper(palette, log_scale, vmin, vmax)

    # Store initial palette name for selector
    if isinstance(palette, str):
        if palette.endswith('256'):
            initial_palette = palette[:-3]
        else:
            palette_map = _get_palette_map()
            initial_palette = palette if palette in palette_map else 'Viridis'
    else:
        initial_palette = 'Viridis'

    # Prepare data for patches glyph - handle matrix case
    xs = []  # List of lists of x coordinates for each polygon
    ys = []  # List of lists of y coordinates for each polygon
    face_ids = []  # Face numbers
    label_list = []  # Labels for each polygon

    # Use first column's vertices for initial display
    vertices_list = all_vertices_lists[0]

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
        all_centers = []
        for col_idx in range(n_columns):
            col_vertices = all_vertices_lists[col_idx]
            all_centers.append(_calculate_polygon_centers(col_vertices))

    # Start with the first column (or only column)
    current_values = values[:, 0]

    # Categorize polygons based on their values
    _, nan_inf_mask, below_min_mask, above_max_mask, in_range_mask = \
        _categorize_polygons(current_values, vmin, vmax)

    # Calculate plot range
    x_range_tuple, y_range_tuple = _calculate_plot_range(all_vertices_lists, values, nan_inf_color)

    # Create figure with equal axis scaling for map visualization
    p = figure(
        width=width,
        height=height,
        title=title,
        x_axis_label='X',
        y_axis_label='Y',
        match_aspect=True,
        aspect_scale=1,
        x_range=x_range_tuple,
        y_range=y_range_tuple,
        tools='pan,wheel_zoom,box_zoom,reset,save'
    )

    # Create polygon names
    polygon_names = _create_polygon_names(n_polygons, labels)

    # Prepare base data dictionary
    base_data = _prepare_base_data(
        xs, ys, face_ids, label_list, polygon_names, values,
        all_vertices_lists, current_values, in_range_mask
    )

    # Create ColumnDataSource for dynamic updates
    source = ColumnDataSource(data=base_data)

    # Create data sources and patches for each category
    all_patches = []

    # 1. In-range polygons (with color mapping)
    in_range_indices = np.where(in_range_mask)[0]
    source_in_range = _create_patch_source(
        xs, ys, face_ids, current_values, label_list, polygon_names, in_range_indices
    )
    if source_in_range is not None:
        patches_in_range = _add_patches_to_plot(p, source_in_range, mapper, line_color, line_width)
        all_patches.append(patches_in_range)

    # 2. Below minimum (use color_below_min or palette min color)
    below_min_indices = np.where(below_min_mask)[0]
    source_below_min = _create_patch_source(
        xs, ys, face_ids, current_values, label_list, polygon_names, below_min_indices
    )
    if source_below_min is not None:
        if color_below_min is None:
            patches_below_min = _add_patches_to_plot(
                p, source_below_min, mapper, line_color, line_width
            )
        else:
            patches_below_min = _add_patches_to_plot(
                p, source_below_min, mapper, line_color, line_width, fill_color=color_below_min
            )
        all_patches.append(patches_below_min)

    # 3. Above maximum (use color_above_max or palette max color)
    above_max_indices = np.where(above_max_mask)[0]
    source_above_max = _create_patch_source(
        xs, ys, face_ids, current_values, label_list, polygon_names, above_max_indices
    )
    if source_above_max is not None:
        if color_above_max is None:
            patches_above_max = _add_patches_to_plot(
                p, source_above_max, mapper, line_color, line_width
            )
        else:
            patches_above_max = _add_patches_to_plot(
                p, source_above_max, mapper, line_color, line_width, fill_color=color_above_max
            )
        all_patches.append(patches_above_max)

    # 4. NaN/Inf polygons (show with specified color or hide)
    source_nan_inf = None
    if nan_inf_color is not None:
        nan_inf_indices = np.where(nan_inf_mask)[0]
        source_nan_inf = _create_patch_source(
            xs, ys, face_ids, current_values, label_list, polygon_names, nan_inf_indices
        )
        if source_nan_inf is not None:
            patches_nan_inf = _add_patches_to_plot(
                p, source_nan_inf, mapper, line_color, line_width, fill_color=nan_inf_color
            )
            all_patches.append(patches_nan_inf)

    # Add connection lines if provided
    connection_renderers = []
    if has_connections:
        # Create connection color mapper if independent scale requested
        connection_mapper, conn_log_scale = _create_connection_color_mapper(
            connection_palette, connection_log_scale, connection_color_limits,
            connection_values, bidirectional_info, n_connections,
            color_palette, log_scale
        )

        if connection_mapper is None:
            connection_mapper = mapper
            conn_log_scale = log_scale

        conn_use_log_for_gradient = conn_log_scale

        # Determine which connections need gradients
        connections_need_gradient = _determine_gradient_needs(
            bidirectional_info,
            n_connections,
            n_columns
        )

        # Prepare connection and gradient data
        conn_data, gradient_data = _prepare_connection_data(
            connections, connection_values, all_centers, labels,
            bidirectional_info, connections_need_gradient,
            conn_use_log_for_gradient, n_columns
        )

        source_connections = ColumnDataSource(data=conn_data)
        source_gradient = ColumnDataSource(data=gradient_data)

        # Draw border lines (white/light) first for visibility
        if connection_border_color is not None:
            border_width = connection_width + 2
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
    palette_select = _create_palette_selector(initial_palette, mapper)

    # If matrix values, add selector control
    if is_matrix and n_columns > 1:
        # Create column selector
        select = _create_column_selector(
            value_names, source, source_in_range, source_below_min, source_above_max,
            source_nan_inf, source_connections if has_connections else None,
            source_gradient if has_connections else None,
            vmin, vmax, nan_inf_color, has_connections
        )

        # Add connection width slider if connections are present
        if has_connections:
            conn_width_slider = _create_connection_width_slider(
                connection_width, connection_renderers, connection_border_color
            )
            controls = row(select, palette_select, conn_width_slider)
            panel = column(controls, p)
        else:
            controls = row(select, palette_select)
            panel = column(controls, p)
    else:
        # No matrix values
        if has_connections:
            conn_width_slider = _create_connection_width_slider(
                connection_width, connection_renderers, connection_border_color
            )
            controls = row(palette_select, conn_width_slider)
            panel = column(controls, p)
        else:
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
                                   [90, 100], [1000, 20], [40, 0.55], [0.55, 0.55]])

    panel_limits = plot_polygon_grid(
        vertices=[vertices1, vertices2],
        values=values_,
        labels=labels_,
        connections=connections_,
        connection_values=connection_values_,
        connection_width=6.0,
        palette='Turbo',
        connection_log_scale=True,
        log_scale=True,
        # color_limits=(0.1, 1000),
        out_of_range_colors=('blue', 'red'),
        nan_inf_color=None,
        colorbar_label='Cells',
        # connection_colorbar_label='Connection',
        title='Map Example'
    )
    show(panel_limits)
