"""
Dash/Plotly plotting utilities for rsimpy.

This module is the foundation for a Dash-based plotting stack that mirrors
the architecture currently used by the Bokeh-based plot utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


def validate_grid_data(grid_data):
    """Validate and normalize grid data to shape (n_properties, n_days, n_cells)."""
    arr = np.asarray(grid_data)
    if arr.ndim != 3:
        raise ValueError(
            "grid_data must be a 3D array with shape "
            "(n_properties, n_days, n_cells)."
        )
    if arr.shape[0] <= 0 or arr.shape[1] <= 0 or arr.shape[2] <= 0:
        raise ValueError("grid_data dimensions must all be greater than zero.")
    return arr


def validate_vertices(vertices, n_cells):
    """Validate and normalize vertices to shape (n_cells, 4, 3)."""
    arr = np.asarray(vertices, dtype=float)
    if arr.ndim != 3 or arr.shape[1:] != (4, 3):
        raise ValueError("vertices must have shape (n_cells, 4, 3).")
    if arr.shape[0] != n_cells:
        raise ValueError(
            f"vertices has {arr.shape[0]} cells, but n_cells from data is {n_cells}."
        )
    return arr


def validate_layer_sizes(layer_sizes, n_cells):
    """Validate layer sizes and ensure their sum matches n_cells."""
    arr = np.asarray(layer_sizes, dtype=int)
    if arr.ndim != 1:
        raise ValueError("layer_sizes must be a 1D array.")
    if arr.size == 0:
        raise ValueError("layer_sizes cannot be empty.")
    if np.any(arr <= 0):
        raise ValueError("layer_sizes must contain only positive integers.")
    if int(arr.sum()) != int(n_cells):
        raise ValueError(
            f"sum(layer_sizes) = {arr.sum()} must equal number of cells ({n_cells})."
        )
    return arr


def build_layer_per_cell(layer_sizes):
    """Return 1-indexed layer id for each cell from layer sizes."""
    layer_sizes = np.asarray(layer_sizes, dtype=int)
    layer_ids = []
    for layer_idx, size in enumerate(layer_sizes, start=1):
        layer_ids.extend([layer_idx] * int(size))
    return np.asarray(layer_ids, dtype=int)


def validate_connection_indices(connection_indices, n_cells):
    """Validate connection indices array shape (2, n_connections)."""
    arr = np.asarray(connection_indices, dtype=int)
    if arr.ndim != 2 or arr.shape[0] != 2:
        raise ValueError("connection_indices must have shape (2, n_connections).")
    if arr.shape[1] == 0:
        raise ValueError("connection_indices cannot be empty when provided.")
    if np.any(arr < 0):
        raise ValueError("connection_indices must be 0-indexed and non-negative.")
    if np.any(arr >= int(n_cells)):
        raise ValueError("connection_indices contains cell index >= n_cells.")
    return arr


def validate_connection_data(connection_data, n_days, n_connections):
    """Validate connection data tensor shape (n_conn_properties, n_days, n_connections)."""
    arr = np.asarray(connection_data)
    if arr.ndim != 3:
        raise ValueError(
            "connection_data must have shape "
            "(n_conn_properties, n_days, n_connections)."
        )
    if arr.shape[0] <= 0:
        raise ValueError("connection_data must have at least one property.")
    if arr.shape[1] != int(n_days):
        raise ValueError(
            f"connection_data n_days ({arr.shape[1]}) must match grid n_days ({n_days})."
        )
    if arr.shape[2] != int(n_connections):
        raise ValueError(
            "connection_data n_connections must match connection_indices n_connections."
        )
    return arr


def _sample_line_points(p0, p1, n_points=20):
    """Sample intermediate points for a line segment to improve hover hit area."""
    t = np.linspace(0.0, 1.0, int(n_points))
    xs = p0[0] + t * (p1[0] - p0[0])
    ys = p0[1] + t * (p1[1] - p0[1])
    return xs, ys


def _compute_polygon_bounds(vertices):
    """Compute x/y bounds from all polygon vertices."""
    arr = np.asarray(vertices, dtype=float)
    x_min = float(np.nanmin(arr[:, :, 0]))
    x_max = float(np.nanmax(arr[:, :, 0]))
    y_min = float(np.nanmin(arr[:, :, 1]))
    y_max = float(np.nanmax(arr[:, :, 1]))
    return x_min, x_max, y_min, y_max


def _color_with_alpha(color, alpha):
    """Convert a color string to rgba(...) with the requested alpha."""
    alpha = float(min(max(alpha, 0.0), 1.0))
    color = str(color).strip()

    if color.startswith("rgba("):
        body = color[5:-1]
        parts = [p.strip() for p in body.split(",")]
        if len(parts) >= 3:
            return f"rgba({parts[0]}, {parts[1]}, {parts[2]}, {alpha:.3f})"

    if color.startswith("rgb("):
        body = color[4:-1]
        parts = [p.strip() for p in body.split(",")]
        if len(parts) == 3:
            return f"rgba({parts[0]}, {parts[1]}, {parts[2]}, {alpha:.3f})"

    if color.startswith("#") and len(color) == 7:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        return f"rgba({r}, {g}, {b}, {alpha:.3f})"

    # Fallback for named colors.
    return color


def _add_gradient_connection_line(
    fig,
    p0,
    p1,
    value_start,
    value_end,
    value_to_color,
    width,
    hover_text,
    n_segments=20,
    alpha_start=1.0,
    alpha_end=1.0,
):
    """Draw a directional line with linear color gradient from p0 to p1."""
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise ImportError(
            "plotly is required for gradient connection rendering."
        ) from exc

    n_segments = max(int(n_segments), 2)
    xs = np.linspace(p0[0], p1[0], n_segments + 1)
    ys = np.linspace(p0[1], p1[1], n_segments + 1)
    vals = np.linspace(float(value_start), float(value_end), n_segments)
    alphas = np.linspace(float(alpha_start), float(alpha_end), n_segments)

    for i in range(n_segments):
        seg_color = _color_with_alpha(value_to_color(vals[i]), alphas[i])
        fig.add_trace(
            go.Scatter(
                x=[xs[i], xs[i + 1]],
                y=[ys[i], ys[i + 1]],
                mode="lines",
                line={"color": seg_color, "width": float(width)},
                name="connection-line",
                hoverinfo="skip",
                showlegend=False,
            )
        )

    hover_x, hover_y = _sample_line_points(p0, p1, n_points=25)
    fig.add_trace(
        go.Scatter(
            x=hover_x,
            y=hover_y,
            mode="markers",
            marker={"size": 10, "opacity": 0.0, "color": "rgba(0,0,0,0)"},
            text=[hover_text] * len(hover_x),
            hovertemplate="%{text}<extra></extra>",
            name="connection-line-hover",
            showlegend=False,
        )
    )


def create_triangle_vertices(center_x, center_y, size, direction="up"):
    """
    Create vertices for an equilateral-looking triangle centered near (x, y).

    Returns
    -------
    tuple(list[float], list[float])
        Closed polygon coordinates suitable for Plotly fill='toself'.
    """
    if size <= 0:
        raise ValueError("size must be positive.")
    if direction not in ("up", "down"):
        raise ValueError("direction must be either 'up' or 'down'.")

    half_w = size / 2.0
    height = size * 0.8660254037844386  # sqrt(3)/2

    if direction == "up":
        xs = [center_x, center_x - half_w, center_x + half_w, center_x]
        ys = [center_y + height / 2.0, center_y - height / 2.0, center_y - height / 2.0, center_y + height / 2.0]
    else:
        xs = [center_x, center_x - half_w, center_x + half_w, center_x]
        ys = [center_y - height / 2.0, center_y + height / 2.0, center_y + height / 2.0, center_y - height / 2.0]

    return xs, ys


def add_triangle_trace(
    fig,
    center_x,
    center_y,
    size,
    direction="up",
    line_color="black",
    fill_color="black",
    name="connection",
    hover_text=None,
):
    """Add a filled triangle as a Scatter trace to a Plotly figure."""
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise ImportError(
            "plotly is required for triangle rendering. Install plotly>=5.24.0"
        ) from exc

    if fig is None:
        fig = go.Figure()

    xs, ys = create_triangle_vertices(center_x, center_y, size, direction)

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            fill="toself",
            line={"color": line_color, "width": 1.0},
            fillcolor=fill_color,
            name=name,
            hovertemplate=(hover_text + "<extra></extra>") if hover_text else None,
            showlegend=False,
        )
    )
    return fig


class BaseDashPlot(ABC):
    """Base class for Dash plot components."""

    def __init__(self, width=900, height=600, title=""):
        self.width = int(width)
        self.height = int(height)
        self.title = title

        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be greater than zero.")

    @abstractmethod
    def create_figure(self):
        """Return a Plotly figure for the component."""


class DashMapPlot(BaseDashPlot):
    """Minimal foundation for map plotting based on 3D grid tensors."""

    def __init__(
        self,
        vertices,
        layer_sizes,
        grid_data=None,
        property_names=None,
        cell_names=None,
        connection_indices=None,
        connection_data=None,
        connection_property_names=None,
        width=900,
        height=600,
        title="Map",
    ):
        super().__init__(width=width, height=height, title=title)

        n_cells_from_vertices = np.asarray(vertices).shape[0]
        self.layer_sizes = validate_layer_sizes(layer_sizes, n_cells_from_vertices)
        self.layer_per_cell = build_layer_per_cell(self.layer_sizes)

        self.vertices = validate_vertices(vertices, n_cells=n_cells_from_vertices)

        if grid_data is None:
            self.grid_data = np.arange(n_cells_from_vertices, dtype=float).reshape(1, 1, -1)
            self.property_names = ["Cell Index"]
        else:
            self.grid_data = validate_grid_data(grid_data)
            if self.grid_data.shape[2] != n_cells_from_vertices:
                raise ValueError(
                    "grid_data n_cells does not match vertices n_cells. "
                    f"Got {self.grid_data.shape[2]} vs {n_cells_from_vertices}."
                )
            if property_names is None:
                self.property_names = [f"Property {i+1}" for i in range(self.grid_data.shape[0])]
            else:
                if len(property_names) != self.grid_data.shape[0]:
                    raise ValueError(
                        "property_names length must match grid_data n_properties."
                    )
                self.property_names = list(property_names)

        if cell_names is None:
            self.cell_names = [f"Cell {i}" for i in range(n_cells_from_vertices)]
        else:
            if len(cell_names) != n_cells_from_vertices:
                raise ValueError("cell_names length must match n_cells.")
            self.cell_names = list(cell_names)

        self.centers_xy = np.mean(self.vertices[:, :, :2], axis=1)

        self.connection_indices = None
        self.connection_data = None
        self.connection_property_names = []
        if connection_indices is not None or connection_data is not None:
            if connection_indices is None or connection_data is None:
                raise ValueError(
                    "connection_indices and connection_data must be provided together."
                )
            self.connection_indices = validate_connection_indices(
                connection_indices,
                n_cells=n_cells_from_vertices,
            )
            self.connection_data = validate_connection_data(
                connection_data,
                n_days=self.grid_data.shape[1],
                n_connections=self.connection_indices.shape[1],
            )
            if connection_property_names is None:
                self.connection_property_names = [
                    f"Connection Property {i+1}"
                    for i in range(self.connection_data.shape[0])
                ]
            else:
                if len(connection_property_names) != self.connection_data.shape[0]:
                    raise ValueError(
                        "connection_property_names length must match "
                        "connection_data n_conn_properties."
                    )
                self.connection_property_names = list(connection_property_names)

    def has_connections(self):
        """Return True when connection tensors are available."""
        return self.connection_indices is not None and self.connection_data is not None

    def create_figure(self):
        """Backward-compatible wrapper that returns the default map view."""
        return self.create_map_figure()

    def create_map_figure(
        self,
        property_index=0,
        day_index=0,
        layer=1,
        palette="Turbo",
        color_limits=None,
        line_color="black",
        line_width=0.8,
        nan_inf_color="#bdbdbd",
        add_connections=False,
        connection_property_index=0,
        connection_width=5.0,
        connection_line_color="#1f1f1f",
        connection_triangle_color=None,
        connection_palette="Plasma",
        connection_color_limits=None,
        connection_nan_inf_color="#bdbdbd",
        connection_line_segments=10,
        connection_triangle_size=0.225,
    ):
        """Create a basic polygon map for one property/day/layer selection."""
        try:
            import plotly.graph_objects as go
            from plotly.colors import sample_colorscale
        except ImportError as exc:
            raise ImportError(
                "plotly is required for Dash map plotting. Install plotly>=5.24.0"
            ) from exc

        n_properties, n_days, _ = self.grid_data.shape
        if property_index < 0 or property_index >= n_properties:
            raise ValueError(
                f"property_index {property_index} is out of range [0, {n_properties-1}]."
            )
        if day_index < 0 or day_index >= n_days:
            raise ValueError(
                f"day_index {day_index} is out of range [0, {n_days-1}]."
            )
        if layer < 1 or layer > len(self.layer_sizes):
            raise ValueError(
                f"layer {layer} is out of range [1, {len(self.layer_sizes)}]."
            )
        if add_connections and not self.has_connections():
            raise ValueError("add_connections=True but no connection data was provided.")
        if self.has_connections():
            n_conn_props = self.connection_data.shape[0]
            if connection_property_index < 0 or connection_property_index >= n_conn_props:
                raise ValueError(
                    "connection_property_index is out of range "
                    f"[0, {n_conn_props-1}]."
                )

        values_all = self.grid_data[property_index, day_index, :]
        layer_mask = self.layer_per_cell == int(layer)
        layer_indices = np.where(layer_mask)[0]
        layer_values = values_all[layer_indices]

        property_all_days = self.grid_data[property_index, :, :]
        finite_values_global = property_all_days[np.isfinite(property_all_days)]

        if color_limits is None:
            if finite_values_global.size == 0:
                vmin, vmax = 0.0, 1.0
            else:
                vmin = float(np.nanmin(finite_values_global))
                vmax = float(np.nanmax(finite_values_global))
                if np.isclose(vmin, vmax):
                    vmax = vmin + 1.0
        else:
            if len(color_limits) != 2:
                raise ValueError("color_limits must be a tuple/list with two values.")
            vmin, vmax = float(color_limits[0]), float(color_limits[1])
            if vmax <= vmin:
                raise ValueError("color_limits must satisfy max > min.")

        def _value_to_color(value):
            if not np.isfinite(value):
                return nan_inf_color
            t = (float(value) - vmin) / (vmax - vmin)
            t = min(max(t, 0.0), 1.0)
            return sample_colorscale(palette, [t])[0]

        fig = go.Figure()

        prop_name = self.property_names[property_index]
        for idx in layer_indices:
            poly = self.vertices[idx]
            x_poly = poly[:, 0]
            y_poly = poly[:, 1]
            value = values_all[idx]
            fill_color = _value_to_color(value)

            x_closed = np.append(x_poly, x_poly[0])
            y_closed = np.append(y_poly, y_poly[0])

            hover_text = (
                f"Cell Index: {idx}<br>"
                f"Cell Name: {self.cell_names[idx]}<br>"
                f"{prop_name}: {value:.6g}"
            )

            fig.add_trace(
                go.Scatter(
                    x=x_closed,
                    y=y_closed,
                    mode="lines",
                    fill="toself",
                    fillcolor=fill_color,
                    line={"color": line_color, "width": float(line_width)},
                    name="cell-polygon",
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            # Invisible fill trace dedicated to hover on polygon area.
            fig.add_trace(
                go.Scatter(
                    x=x_closed,
                    y=y_closed,
                    mode="lines",
                    hoveron="fills",
                    fill="toself",
                    fillcolor="rgba(0,0,0,0)",
                    line={"color": "rgba(0,0,0,0)", "width": 0.0},
                    name="cell-polygon-hover",
                    hovertemplate=hover_text + "<extra></extra>",
                    showlegend=False,
                )
            )

        finite_values_current_layer = layer_values[np.isfinite(layer_values)]
        if finite_values_current_layer.size > 0:
            colorbar_values = finite_values_current_layer
        else:
            colorbar_values = np.array([vmin, vmax], dtype=float)

        fig.add_trace(
            go.Scatter(
                x=[None] * len(colorbar_values),
                y=[None] * len(colorbar_values),
                mode="markers",
                marker={
                    "size": 0.1,
                    "color": colorbar_values,
                    "colorscale": palette,
                    "cmin": vmin,
                    "cmax": vmax,
                    "showscale": True,
                    "colorbar": {"title": prop_name, "x": 1.02, "y": 0.5, "len": 0.9},
                },
                hoverinfo="skip",
                showlegend=False,
                name="colorbar",
            )
        )

        fig.update_layout(
            title=self.title,
            width=self.width,
            height=self.height,
            xaxis_title="X",
            yaxis_title="Y",
            template="plotly_white",
            margin={"l": 40, "r": 190, "t": 60, "b": 40},
            uirevision="dash-map-view",
        )
        x_min, x_max, y_min, y_max = _compute_polygon_bounds(self.vertices)
        x_pad = 0.05 * max(x_max - x_min, 1.0)
        y_pad = 0.05 * max(y_max - y_min, 1.0)
        fig.update_xaxes(range=[x_min - x_pad, x_max + x_pad])
        fig.update_yaxes(range=[y_min - y_pad, y_max + y_pad], scaleanchor="x", scaleratio=1)

        if add_connections and self.has_connections():
            conn_values = self.connection_data[connection_property_index, day_index, :]
            layer_id = int(layer)

            conn_all_days = self.connection_data[connection_property_index, :, :]
            conn_finite_global = conn_all_days[np.isfinite(conn_all_days)]
            if connection_color_limits is None:
                if conn_finite_global.size == 0:
                    conn_vmin, conn_vmax = 0.0, 1.0
                else:
                    conn_vmin = float(np.nanmin(conn_finite_global))
                    conn_vmax = float(np.nanmax(conn_finite_global))
                    if np.isclose(conn_vmin, conn_vmax):
                        conn_vmax = conn_vmin + 1.0
            else:
                if len(connection_color_limits) != 2:
                    raise ValueError(
                        "connection_color_limits must be a tuple/list with two values."
                    )
                conn_vmin = float(connection_color_limits[0])
                conn_vmax = float(connection_color_limits[1])
                if conn_vmax <= conn_vmin:
                    raise ValueError("connection_color_limits must satisfy max > min.")

            def _connection_value_to_color(value):
                if not np.isfinite(value):
                    return connection_nan_inf_color
                t = (float(value) - conn_vmin) / (conn_vmax - conn_vmin)
                t = min(max(t, 0.0), 1.0)
                return sample_colorscale(connection_palette, [t])[0]

            directional_values = {}
            for conn_idx in range(self.connection_indices.shape[1]):
                c0 = int(self.connection_indices[0, conn_idx])
                c1 = int(self.connection_indices[1, conn_idx])
                directional_values[(c0, c1)] = float(conn_values[conn_idx])

            pair_set = set()
            for (c0, c1) in directional_values.keys():
                if c0 == c1:
                    continue
                pair_set.add(tuple(sorted((c0, c1))))

            # Same-layer connections as thick lines with directional gradient colors.
            for a, b in sorted(pair_set):
                k0 = int(self.layer_per_cell[a])
                k1 = int(self.layer_per_cell[b])
                if not (k0 == layer_id and k1 == layer_id):
                    continue

                has_ab = (a, b) in directional_values
                has_ba = (b, a) in directional_values
                v_ab = directional_values.get((a, b), 0.0)
                v_ba = directional_values.get((b, a), 0.0)

                if has_ab and has_ba:
                    value_start = v_ab
                    value_end = v_ba
                    alpha_start = 1.0
                    alpha_end = 1.0
                elif has_ab:
                    value_start = v_ab
                    value_end = v_ab
                    alpha_start = 1.0
                    alpha_end = 0.12
                elif has_ba:
                    value_start = v_ba
                    value_end = v_ba
                    alpha_start = 0.12
                    alpha_end = 1.0
                else:
                    continue

                p0 = self.centers_xy[a]
                p1 = self.centers_xy[b]
                text_ab = f"{v_ab:.6g}" if has_ab else "missing"
                text_ba = f"{v_ba:.6g}" if has_ba else "missing"
                hover_text = (
                    f"{a}->{b}: {text_ab}<br>"
                    f"{b}->{a}: {text_ba}"
                )
                _add_gradient_connection_line(
                    fig=fig,
                    p0=p0,
                    p1=p1,
                    value_start=value_start,
                    value_end=value_end,
                    value_to_color=_connection_value_to_color,
                    width=connection_width,
                    hover_text=hover_text,
                    n_segments=connection_line_segments,
                    alpha_start=alpha_start,
                    alpha_end=alpha_end,
                )

            # Cross-layer connections summarized as triangles at selected layer cells.
            agg = {}
            for conn_idx in range(self.connection_indices.shape[1]):
                c0 = int(self.connection_indices[0, conn_idx])
                c1 = int(self.connection_indices[1, conn_idx])
                k0 = int(self.layer_per_cell[c0])
                k1 = int(self.layer_per_cell[c1])
                value = float(conn_values[conn_idx])

                if k0 == layer_id and k1 != layer_id:
                    selected_cell = c0
                    other_layer = k1
                elif k1 == layer_id and k0 != layer_id:
                    selected_cell = c1
                    other_layer = k0
                else:
                    continue

                direction = "up" if other_layer < layer_id else "down"
                key = (selected_cell, direction)
                if key not in agg:
                    agg[key] = 0.0
                agg[key] += value

            for (selected_cell, direction), agg_value in agg.items():
                cx, cy = self.centers_xy[selected_cell]
                triangle_color = _connection_value_to_color(agg_value)
                offset = connection_triangle_size * 0.275
                if direction == "up":
                    triangle_center_x = float(cx - offset)
                    triangle_center_y = float(cy + offset)
                else:
                    triangle_center_x = float(cx + offset)
                    triangle_center_y = float(cy - offset)
                add_triangle_trace(
                    fig=fig,
                    center_x=triangle_center_x,
                    center_y=triangle_center_y,
                    size=float(connection_triangle_size),
                    direction=direction,
                    line_color=connection_line_color,
                    fill_color=triangle_color if connection_triangle_color is None else connection_triangle_color,
                    name=f"connection-triangle-{direction}",
                    hover_text=(
                        f"Connection: Cell {selected_cell}<br>"
                        f"Direction: {direction}<br>"
                        f"Aggregated Value: {agg_value:.6g}"
                    ),
                )

            conn_finite_current_day = conn_values[np.isfinite(conn_values)]
            if conn_finite_current_day.size == 0:
                conn_colorbar_values = np.array([conn_vmin, conn_vmax], dtype=float)
            else:
                conn_colorbar_values = conn_finite_current_day

            fig.add_trace(
                go.Scatter(
                    x=[None] * len(conn_colorbar_values),
                    y=[None] * len(conn_colorbar_values),
                    mode="markers",
                    marker={
                        "size": 0.1,
                        "color": conn_colorbar_values,
                        "colorscale": connection_palette,
                        "cmin": conn_vmin,
                        "cmax": conn_vmax,
                        "showscale": True,
                        "colorbar": {"title": "Connection", "x": 1.14, "y": 0.5, "len": 0.9},
                    },
                    hoverinfo="skip",
                    showlegend=False,
                    name="connection-colorbar",
                )
            )
        return fig
