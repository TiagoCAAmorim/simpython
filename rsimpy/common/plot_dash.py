# pylint: disable=too-many-lines
"""
Dash/Plotly plotting utilities for rsimpy.

This module is the foundation for a Dash-based plotting stack that mirrors
the architecture currently used by the Bokeh-based plot utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.colors import sample_colorscale
except ImportError as exc:
    raise ImportError(
        "plotly is required for Dash plotting. Install plotly>=5.24.0"
    ) from exc


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
    """Validate connection data tensor shape.

    Expected shape: (n_conn_properties, n_days, n_connections).
    """
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
            f"connection_data n_days ({arr.shape[1]}) "
            f"must match grid n_days ({n_days})."
        )
    if arr.shape[2] != int(n_connections):
        raise ValueError(
            "connection_data n_connections must match connection_indices n_connections."
        )
    return arr


def validate_wells(wells, n_cells):
    """Validate wells dict mapping "name,type" -> 0-indexed cell indices."""
    if wells is None:
        return {}
    if not isinstance(wells, dict):
        raise ValueError("wells must be a dict mapping 'name,type' to cell indices.")

    validated = {}
    for key, values in wells.items():
        if not isinstance(key, str) or len(key.strip()) == 0:
            raise ValueError("well keys must be non-empty strings.")
        arr = np.asarray(values, dtype=int).ravel()
        if arr.size == 0:
            continue
        if np.any(arr < 0) or np.any(arr >= int(n_cells)):
            raise ValueError("well cell indices must be within [0, n_cells-1].")
        validated[str(key)] = arr
    return validated


def _sample_line_points(p0, p1, n_points=20):
    """Sample intermediate points for a line segment to improve hover hit area."""
    t = np.linspace(0.0, 1.0, int(n_points))
    xs = p0[0] + t * (p1[0] - p0[0])
    ys = p0[1] + t * (p1[1] - p0[1])
    return xs, ys


def _sample_quad_interior_points(poly_xy, n_per_side=3, inset=0.2):
    """Sample interior points of a quadrilateral for robust hover hit testing."""
    arr = np.asarray(poly_xy, dtype=float)
    if arr.shape[0] != 4 or arr.shape[1] != 2:
        raise ValueError("poly_xy must have shape (4, 2).")

    # Bilinear interpolation using vertex order [0, 1, 2, 3].
    p00 = arr[0]
    p10 = arr[1]
    p11 = arr[2]
    p01 = arr[3]

    n_per_side = max(int(n_per_side), 1)
    inset = float(min(max(inset, 0.0), 0.49))
    us = np.linspace(inset, 1.0 - inset, n_per_side)
    vs = np.linspace(inset, 1.0 - inset, n_per_side)

    points = []
    for u in us:
        for v in vs:
            p = (
                (1.0 - u) * (1.0 - v) * p00
                + u * (1.0 - v) * p10
                + u * v * p11
                + (1.0 - u) * v * p01
            )
            points.append(p)

    points = np.asarray(points, dtype=float)
    return points[:, 0], points[:, 1]


def _compute_polygon_bounds(vertices):
    """Compute x/y bounds from all polygon vertices."""
    arr = np.asarray(vertices, dtype=float)
    x_min = float(np.nanmin(arr[:, :, 0]))
    x_max = float(np.nanmax(arr[:, :, 0]))
    y_min = float(np.nanmin(arr[:, :, 1]))
    y_max = float(np.nanmax(arr[:, :, 1]))
    return x_min, x_max, y_min, y_max


def _polygon_area_xy(poly_xy):
    """Compute polygon area on XY plane using the shoelace formula."""
    arr = np.asarray(poly_xy, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError("poly_xy must have shape (n_vertices, 2).")
    if arr.shape[0] < 3:
        return 0.0
    x = arr[:, 0]
    y = arr[:, 1]
    area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    return float(area)


def _circle_polygon(center_x, center_y, radius, n_points=48):
    """Build a closed polygon approximating a circle in data coordinates."""
    theta = np.linspace(0.0, 2.0 * np.pi, int(max(n_points, 12)), endpoint=True)
    xs = float(center_x) + float(radius) * np.cos(theta)
    ys = float(center_y) + float(radius) * np.sin(theta)
    return xs, ys


def _interpolate_edge_contour(p1, p2, z1, z2, contour_value):
    """Find where a contour level crosses an edge between two points."""
    if z1 == z2:
        mid_x = 0.5 * (p1[0] + p2[0])
        mid_y = 0.5 * (p1[1] + p2[1])
        return np.asarray([mid_x, mid_y], dtype=float)

    if (z1 <= contour_value <= z2) or (z2 <= contour_value <= z1):
        t = (contour_value - z1) / (z2 - z1)
        x = p1[0] + t * (p2[0] - p1[0])
        y = p1[1] + t * (p2[1] - p1[1])
        return np.array([x, y])

    return None


def _get_contour_segments_triangle(triangle, z_vals, contour_value):
    """Compute contour segments for one triangle and one contour level."""
    triangle_z_min = float(np.min(z_vals))
    triangle_z_max = float(np.max(z_vals))
    if contour_value < triangle_z_min or contour_value > triangle_z_max:
        return []

    crossings = []
    for i in range(3):
        j = (i + 1) % 3
        point = _interpolate_edge_contour(
            triangle[i], triangle[j], z_vals[i], z_vals[j], contour_value
        )
        if point is not None:
            if not any(np.allclose(point, existing) for existing in crossings):
                crossings.append(point)

    if len(crossings) == 2:
        return [(crossings[0], crossings[1])]

    if len(crossings) > 2:
        return [(crossings[0], crossings[1])]

    return []


def _nice_contour_step(raw_step):
    """Round a contour step to a visually meaningful 1/2/5 * 10^n value."""
    raw_step = float(raw_step)
    if raw_step <= 0.0:
        return 1.0

    exponent = float(np.floor(np.log10(raw_step)))
    fraction = raw_step / (10.0 ** exponent)
    if fraction < 1.5:
        nice_fraction = 1.0
    elif fraction < 3.5:
        nice_fraction = 2.0
    elif fraction < 7.5:
        nice_fraction = 5.0
    else:
        nice_fraction = 10.0
    return nice_fraction * (10.0 ** exponent)


def _triangulate_polygon(polygon):
    """Triangulate a polygon by fan triangulation from its center."""
    n_vertices = polygon.shape[0]
    if n_vertices == 3:
        return [polygon[:, :2]]

    center_xy = np.mean(polygon[:, :2], axis=0)
    triangles = []
    for i in range(n_vertices):
        j = (i + 1) % n_vertices
        triangles.append(np.array([polygon[i, :2], polygon[j, :2], center_xy]))
    return triangles


def _get_z_values_for_triangle(polygon_z, triangle_idx, n_vertices):
    """Get z-values for triangle vertices in fan triangulation."""
    if n_vertices == 3:
        return polygon_z

    i = triangle_idx
    j = (i + 1) % n_vertices
    center_z = float(np.mean(polygon_z))
    return np.array([polygon_z[i], polygon_z[j], center_z])


def _compute_contour_lines_for_polygon(polygon, contour_values):
    """Compute contour segments for a polygon with (x, y, z) vertices."""
    if polygon.shape[1] != 3:
        return {}

    z_vals = polygon[:, 2]
    n_vertices = polygon.shape[0]
    triangles = _triangulate_polygon(polygon)

    contour_segments = {float(cv): [] for cv in contour_values}
    for tri_idx, triangle in enumerate(triangles):
        tri_z_vals = _get_z_values_for_triangle(z_vals, tri_idx, n_vertices)
        for contour_value in contour_values:
            segments = _get_contour_segments_triangle(
                triangle, tri_z_vals, contour_value
            )
            contour_segments[float(contour_value)].extend(segments)

    return contour_segments


def _determine_contour_levels(vertices, contour_count):
    """Determine contour levels from the global z-value range."""
    contour_count = int(contour_count)
    if contour_count <= 0:
        raise ValueError("contour_count must be > 0.")

    z_vals = np.asarray(vertices[:, :, 2], dtype=float).ravel()
    z_vals = z_vals[np.isfinite(z_vals)]
    if z_vals.size == 0:
        return None

    if float(np.std(z_vals)) < 1.0e-2:
        return None

    z_min = float(np.min(z_vals))
    z_max = float(np.max(z_vals))
    if contour_count == 1 or np.isclose(z_min, z_max):
        return np.asarray([0.5 * (z_min + z_max)], dtype=float)

    raw_step = (z_max - z_min) / float(contour_count - 1)
    step = _nice_contour_step(raw_step)
    first_level = np.ceil(z_min / step) * step
    last_level = np.floor(z_max / step) * step
    if last_level < first_level:
        return np.asarray([0.5 * (z_min + z_max)], dtype=float)

    n_levels = int(np.floor((last_level - first_level) / step)) + 1
    return first_level + step * np.arange(n_levels, dtype=float)


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

    h2 = height / 2.0
    if direction == "up":
        xs = [center_x, center_x - half_w, center_x + half_w, center_x]
        ys = [center_y + h2, center_y - h2, center_y - h2, center_y + h2]
    else:
        xs = [center_x, center_x - half_w, center_x + half_w, center_x]
        ys = [center_y - h2, center_y + h2, center_y + h2, center_y - h2]

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
):
    """Add a filled triangle as a Scatter trace to a Plotly figure."""
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
            hoverinfo="skip",
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
        wells=None,
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
            self.grid_data = np.arange(
                n_cells_from_vertices, dtype=float
            ).reshape(1, 1, -1)
            self.property_names = ["Cell Index"]
        else:
            self.grid_data = validate_grid_data(grid_data)
            if self.grid_data.shape[2] != n_cells_from_vertices:
                raise ValueError(
                    "grid_data n_cells does not match vertices n_cells. "
                    f"Got {self.grid_data.shape[2]} vs {n_cells_from_vertices}."
                )
            if property_names is None:
                self.property_names = [
                    f"Property {i+1}" for i in range(self.grid_data.shape[0])
                ]
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
        self.wells = validate_wells(wells, n_cells=n_cells_from_vertices)

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

    def has_contours(self):
        """Return True when z-variance supports contour rendering."""
        z_vals = np.asarray(self.vertices[:, :, 2], dtype=float).ravel()
        z_vals = z_vals[np.isfinite(z_vals)]
        if z_vals.size == 0:
            return False
        return float(np.std(z_vals)) >= 1.0e-2

    def has_wells(self):
        """Return True when well definitions are available."""
        return len(self.wells) > 0

    def create_figure(self):
        """Backward-compatible wrapper that returns the default map view."""
        return self.create_map_figure()

    def create_map_figure(
        self,
        property_index=0,
        day_index=0,
        layer=1,
        palette="Turbo",
        grid_log_scale=False,
        color_limits=None,
        line_color="black",
        line_width=0.8,
        nan_inf_color="#bdbdbd",
        add_grid=True,
        add_connections=False,
        connection_property_index=0,
        connection_width=5.0,
        connection_line_color="#1f1f1f",
        connection_triangle_color=None,
        connection_palette="Plasma",
        connection_log_scale=False,
        connection_color_limits=None,
        connection_nan_inf_color="#bdbdbd",
        connection_line_segments=10,
        connection_triangle_size=0.225,
        add_contours=False,
        contour_count=7,
        contour_line_width=3.0,
        add_wells=False,
        well_size_percent=20.0,
        well_line_width=2.0,
    ):
        """Create a basic polygon map for one property/day/layer selection."""
        n_properties, n_days, _ = self.grid_data.shape
        if property_index < 0 or property_index >= n_properties:
            raise ValueError(
                f"property_index {property_index} is out of range "
                f"[0, {n_properties-1}]."
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
            raise ValueError(
                "add_connections=True but no connection data provided."
            )
        if add_wells and not self.has_wells():
            raise ValueError("add_wells=True but no wells data was provided.")
        if self.has_connections():
            n_conn_props = self.connection_data.shape[0]
            if (
                connection_property_index < 0
                or connection_property_index >= n_conn_props
            ):
                raise ValueError(
                    "connection_property_index is out of range "
                    f"[0, {n_conn_props-1}]."
                )

        values_all = self.grid_data[property_index, day_index, :]
        layer_mask = self.layer_per_cell == int(layer)
        layer_indices = np.where(layer_mask)[0]
        layer_values = values_all[layer_indices]

        def _build_log_tick_labels(log_min, log_max, n_ticks=7):
            """Build readable log-scale ticks using 1-2-5 steps in original units."""
            log_min = float(log_min)
            log_max = float(log_max)
            if (
                not np.isfinite(log_min)
                or not np.isfinite(log_max)
                or log_max <= log_min
            ):
                vals = np.array([log_min, log_max], dtype=float)
                text = [f"{10.0 ** v:.6g}" for v in vals]
                return vals, text

            lower = 10.0 ** log_min
            upper = 10.0 ** log_max
            target_n = int(max(n_ticks, 2))

            exp_lo = int(np.floor(np.log10(lower)))
            exp_hi = int(np.ceil(np.log10(upper)))
            bases = (1.0, 2.0, 5.0)

            candidates = []
            for exp in range(exp_lo - 1, exp_hi + 2):
                scale = 10.0 ** exp
                for base in bases:
                    value = base * scale
                    if lower <= value <= upper:
                        candidates.append(value)

            unique_vals = np.array(
                sorted(set(float(v) for v in candidates)), dtype=float
            )

            if unique_vals.size > target_n:
                idx = np.linspace(0, unique_vals.size - 1, target_n)
                idx = np.unique(np.round(idx).astype(int))
                unique_vals = unique_vals[idx]

            def _format_original_value(v):
                av = abs(v)
                if av >= 1000:
                    return f"{v:.0f}"
                if av >= 1:
                    return f"{v:.3f}".rstrip("0").rstrip(".")
                if av >= 0.1:
                    return f"{v:.4f}".rstrip("0").rstrip(".")
                return f"{v:.6f}".rstrip("0").rstrip(".")

            tick_vals = np.log10(unique_vals)
            tick_text = [_format_original_value(v) for v in unique_vals]
            return tick_vals, tick_text

        property_all_days = self.grid_data[property_index, :, :]
        finite_values_global = property_all_days[np.isfinite(property_all_days)]
        positive_values_global = finite_values_global[finite_values_global > 0.0]

        if grid_log_scale:
            if color_limits is None:
                if positive_values_global.size == 0:
                    vmin, vmax = 0.0, 1.0
                else:
                    vmin = float(np.log10(np.nanmin(positive_values_global)))
                    vmax = float(np.log10(np.nanmax(positive_values_global)))
                    if np.isclose(vmin, vmax):
                        vmax = vmin + 1.0
            else:
                if len(color_limits) != 2:
                    raise ValueError(
                        "color_limits must be a tuple/list with two values."
                    )
                vmin, vmax = float(color_limits[0]), float(color_limits[1])
                if vmax <= vmin:
                    raise ValueError("color_limits must satisfy max > min.")

            def _value_to_color(value):
                if not np.isfinite(value) or float(value) <= 0.0:
                    return "#4d4d4d"
                t = (float(np.log10(value)) - vmin) / (vmax - vmin)
                t = min(max(t, 0.0), 1.0)
                return sample_colorscale(palette, [t])[0]

            prop_name = self.property_names[property_index]
        else:
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
                    raise ValueError(
                        "color_limits must be a tuple/list with two values."
                    )
                vmin, vmax = float(color_limits[0]), float(color_limits[1])
                if vmax <= vmin:
                    raise ValueError("color_limits must satisfy max > min.")

            def _value_to_color(value):
                if not np.isfinite(value):
                    return nan_inf_color
                t = (float(value) - vmin) / (vmax - vmin)
                t = min(max(t, 0.0), 1.0)
                return sample_colorscale(palette, [t])[0]

            prop_name = self.property_names[property_index]

        fig = go.Figure()

        if add_grid:
            for idx in layer_indices:
                poly = self.vertices[idx]
                x_poly = poly[:, 0]
                y_poly = poly[:, 1]
                value = values_all[idx]
                fill_color = _value_to_color(value)

                x_closed = np.append(x_poly, x_poly[0])
                y_closed = np.append(y_poly, y_poly[0])

                hover_text = (
                    f"#{idx}: "
                    f"{self.cell_names[idx]}<br>"
                    f"{prop_name}={value:.6g}"
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

                # Add sparse interior hit points (3x3 = 9) for robust polygon hover.
                hover_x, hover_y = _sample_quad_interior_points(
                    poly[:, :2], n_per_side=3, inset=0.2
                )
                fig.add_trace(
                    go.Scatter(
                        x=hover_x,
                        y=hover_y,
                        mode="markers",
                        marker={"size": 9, "color": "rgba(0,0,0,0.001)"},
                        text=[hover_text] * len(hover_x),
                        name="cell-polygon-hover",
                        hovertemplate="%{text}<extra></extra>",
                        showlegend=False,
                    )
                )

            if grid_log_scale:
                finite_values_current_layer = layer_values[
                    np.isfinite(layer_values) & (layer_values > 0.0)
                ]
                colorbar_values = (
                    np.log10(finite_values_current_layer)
                    if finite_values_current_layer.size > 0
                    else np.array([vmin, vmax], dtype=float)
                )
            else:
                finite_values_current_layer = layer_values[np.isfinite(layer_values)]
                colorbar_values = (
                    finite_values_current_layer
                    if finite_values_current_layer.size > 0
                    else np.array([vmin, vmax], dtype=float)
                )

            grid_colorbar = {"title": prop_name, "x": 1.02, "y": 0.5, "len": 0.9}
            if grid_log_scale:
                tick_vals, tick_text = _build_log_tick_labels(vmin, vmax)
                grid_colorbar["tickmode"] = "array"
                grid_colorbar["tickvals"] = tick_vals
                grid_colorbar["ticktext"] = tick_text

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
                        "colorbar": grid_colorbar,
                    },
                    hoverinfo="skip",
                    showlegend=False,
                    name="colorbar",
                )
            )

        x_min, x_max, y_min, y_max = _compute_polygon_bounds(self.vertices)
        x_pad = 0.05 * max(x_max - x_min, 1.0)
        y_pad = 0.05 * max(y_max - y_min, 1.0)

        fig.update_layout(
            title=self.title,
            width=self.width,
            height=self.height,
            dragmode="pan",
            xaxis_title="X",
            yaxis_title="Y",
            xaxis={
                "tickformat": ".2f",
                "range": [x_min - x_pad, x_max + x_pad],
                "autorange": False,
            },
            yaxis={
                "tickformat": ".2f",
                "range": [y_min - y_pad, y_max + y_pad],
                "autorange": False,
            },
            template="plotly_white",
            margin={"l": 40, "r": 190, "t": 60, "b": 40},
            uirevision="dash-map-view",
        )
        fig.update_yaxes(scaleanchor="x", scaleratio=1)

        if add_contours:
            contour_levels = _determine_contour_levels(self.vertices, contour_count)
            if contour_levels is not None and len(contour_levels) > 0:
                contour_levels = np.asarray(contour_levels, dtype=float)
                cmin = float(np.min(contour_levels))
                cmax = float(np.max(contour_levels))
                if np.isclose(cmin, cmax):
                    cmax = cmin + 1.0

                def _contour_level_to_color(level):
                    t = (float(level) - cmin) / (cmax - cmin)
                    t = min(max(t, 0.0), 1.0)
                    return sample_colorscale("Greys", [t])[0]

                segments_by_level = {float(level): [] for level in contour_levels}
                for idx in layer_indices:
                    polygon = self.vertices[idx]
                    poly_segments = _compute_contour_lines_for_polygon(
                        polygon, contour_levels
                    )
                    for level, segments in poly_segments.items():
                        segments_by_level[float(level)].extend(segments)

                for level in contour_levels:
                    segments = segments_by_level[float(level)]
                    if len(segments) == 0:
                        continue

                    line_x = []
                    line_y = []
                    hover_x = []
                    hover_y = []
                    hover_t = []
                    for p0, p1 in segments:
                        line_x.extend([float(p0[0]), float(p1[0]), None])
                        line_y.extend([float(p0[1]), float(p1[1]), None])
                        hover_x.append(float(0.5 * (p0[0] + p1[0])))
                        hover_y.append(float(0.5 * (p0[1] + p1[1])))
                        hover_t.append(f"Z={float(level):.6g}")

                    fig.add_trace(
                        go.Scatter(
                            x=line_x,
                            y=line_y,
                            mode="lines",
                            line={
                                "color": _contour_level_to_color(level),
                                "width": float(contour_line_width),
                            },
                            name="contour-line",
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=hover_x,
                            y=hover_y,
                            mode="markers",
                            marker={"size": 8, "color": "rgba(0,0,0,0.001)"},
                            text=hover_t,
                            hovertemplate="%{text}<extra></extra>",
                            name="contour-line-hover",
                            showlegend=False,
                        )
                    )

        if add_connections and self.has_connections():
            conn_values = self.connection_data[connection_property_index, day_index, :]
            layer_id = int(layer)

            conn_all_days = self.connection_data[connection_property_index, :, :]
            conn_finite_global = conn_all_days[np.isfinite(conn_all_days)]
            conn_positive_global = conn_finite_global[conn_finite_global > 0.0]
            if connection_log_scale:
                if connection_color_limits is None:
                    if conn_positive_global.size == 0:
                        conn_vmin, conn_vmax = 0.0, 1.0
                    else:
                        conn_vmin = float(np.log10(np.nanmin(conn_positive_global)))
                        conn_vmax = float(np.log10(np.nanmax(conn_positive_global)))
                        if np.isclose(conn_vmin, conn_vmax):
                            conn_vmax = conn_vmin + 1.0
                else:
                    if len(connection_color_limits) != 2:
                        raise ValueError(
                            "connection_color_limits must be a tuple/list "
                            "with two values."
                        )
                    conn_vmin = float(connection_color_limits[0])
                    conn_vmax = float(connection_color_limits[1])
                    if conn_vmax <= conn_vmin:
                        raise ValueError(
                            "connection_color_limits must satisfy max > min."
                        )

                def _connection_value_to_color(value):
                    if not np.isfinite(value) or float(value) <= 0.0:
                        return "#4d4d4d"
                    t = (float(np.log10(value)) - conn_vmin) / (conn_vmax - conn_vmin)
                    t = min(max(t, 0.0), 1.0)
                    return sample_colorscale(connection_palette, [t])[0]

                connection_colorbar_title = "Connection"
            else:
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
                            "connection_color_limits must be a tuple/list "
                            "with two values."
                        )
                    conn_vmin = float(connection_color_limits[0])
                    conn_vmax = float(connection_color_limits[1])
                    if conn_vmax <= conn_vmin:
                        raise ValueError(
                            "connection_color_limits must satisfy max > min."
                        )

                def _connection_value_to_color(value):
                    if not np.isfinite(value):
                        return connection_nan_inf_color
                    t = (float(value) - conn_vmin) / (conn_vmax - conn_vmin)
                    t = min(max(t, 0.0), 1.0)
                    return sample_colorscale(connection_palette, [t])[0]

                connection_colorbar_title = "Connection"

            directional_values = {}
            for conn_idx in range(self.connection_indices.shape[1]):
                c0 = int(self.connection_indices[0, conn_idx])
                c1 = int(self.connection_indices[1, conn_idx])
                directional_values[(c0, c1)] = float(conn_values[conn_idx])

            pair_set = set()
            for (c0, c1) in directional_values:
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
                hover_text = []
                if has_ab:
                    hover_text.append(f"{a}->{b}={v_ab:.6g}")
                if has_ba:
                    hover_text.append(f"{b}->{a}={v_ba:.6g}")
                hover_text = "<br>".join(hover_text)
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
                    arrow = "↑"
                else:
                    triangle_center_x = float(cx + offset)
                    triangle_center_y = float(cy - offset)
                    arrow = "↓"
                triangle_hover_text = (
                    f"{selected_cell}{arrow}={agg_value:.6g}"
                )
                tri_fill_color = (
                    triangle_color
                    if connection_triangle_color is None
                    else connection_triangle_color
                )
                add_triangle_trace(
                    fig=fig,
                    center_x=triangle_center_x,
                    center_y=triangle_center_y,
                    size=float(connection_triangle_size),
                    direction=direction,
                    line_color=connection_line_color,
                    fill_color=tri_fill_color,
                    name=f"connection-triangle-{direction}",
                )
                # Single center hit point improves triangle hover reliability.
                fig.add_trace(
                    go.Scatter(
                        x=[triangle_center_x],
                        y=[triangle_center_y],
                        mode="markers",
                        marker={"size": 12, "color": "rgba(0,0,0,0.001)"},
                        text=[triangle_hover_text],
                        hovertemplate="%{text}<extra></extra>",
                        name="connection-triangle-hover",
                        showlegend=False,
                    )
                )

            if connection_log_scale:
                conn_finite_current_day = conn_values[
                    np.isfinite(conn_values) & (conn_values > 0.0)
                ]
                if conn_finite_current_day.size == 0:
                    conn_colorbar_values = np.array([conn_vmin, conn_vmax], dtype=float)
                else:
                    conn_colorbar_values = np.log10(conn_finite_current_day)
            else:
                conn_finite_current_day = conn_values[np.isfinite(conn_values)]
                if conn_finite_current_day.size == 0:
                    conn_colorbar_values = np.array([conn_vmin, conn_vmax], dtype=float)
                else:
                    conn_colorbar_values = conn_finite_current_day

            connection_colorbar = {
                "title": connection_colorbar_title,
                "x": 1.14,
                "y": 0.5,
                "len": 0.9,
            }
            if connection_log_scale:
                tick_vals, tick_text = _build_log_tick_labels(conn_vmin, conn_vmax)
                connection_colorbar["tickmode"] = "array"
                connection_colorbar["tickvals"] = tick_vals
                connection_colorbar["ticktext"] = tick_text

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
                        "colorbar": connection_colorbar,
                    },
                    hoverinfo="skip",
                    showlegend=False,
                    name="connection-colorbar",
                )
            )

        if add_wells and self.has_wells():
            well_size_percent = float(well_size_percent)
            well_size_percent = min(max(well_size_percent, 5.0), 200.0)

            # Size well circles by area in data units so zoom preserves physical scale.
            layer_areas = []
            for idx in layer_indices:
                layer_areas.append(_polygon_area_xy(self.vertices[int(idx), :, :2]))
            finite_areas = np.asarray(layer_areas, dtype=float)
            finite_areas = finite_areas[np.isfinite(finite_areas)]
            if finite_areas.size == 0 or float(np.mean(finite_areas)) <= 0.0:
                mean_cell_area = 1.0
            else:
                mean_cell_area = float(np.mean(finite_areas))
            target_circle_area = mean_cell_area * (well_size_percent / 100.0)
            circle_radius = float(np.sqrt(max(target_circle_area, 1.0e-12) / np.pi))

            type_colors = {
                "prod": "green",
                "injw": "blue",
                "injg": "red",
                "inj": "#F17720",
                "closed": "gray",
            }
            active_layer = int(layer)

            for well_key, well_cells in self.wells.items():
                if "," in well_key:
                    well_name, well_type = well_key.rsplit(",", 1)
                else:
                    well_name, well_type = well_key, "unknown"
                well_name = well_name.strip()
                well_type = well_type.strip().lower()
                well_color = type_colors.get(well_type, "black")

                cells_in_well = [
                    int(c) for c in np.asarray(well_cells, dtype=int).ravel()
                ]
                if len(cells_in_well) == 0:
                    continue

                if len(cells_in_well) >= 2:
                    for c0, c1 in zip(cells_in_well[:-1], cells_in_well[1:]):
                        p0 = self.centers_xy[int(c0)]
                        p1 = self.centers_xy[int(c1)]
                        k0 = int(self.layer_per_cell[int(c0)])
                        k1 = int(self.layer_per_cell[int(c1)])
                        same_layer = k0 == active_layer and k1 == active_layer
                        line_dash = "solid" if same_layer else "dash"
                        fig.add_trace(
                            go.Scatter(
                                x=[float(p0[0]), float(p1[0])],
                                y=[float(p0[1]), float(p1[1])],
                                mode="lines",
                                line={
                                    "color": "black",
                                    "width": float(well_line_width),
                                    "dash": line_dash,
                                },
                                name="well-line",
                                hoverinfo="skip",
                                showlegend=False,
                            )
                        )

                hover_x = []
                hover_y = []
                hover_t = []
                for c in cells_in_well:
                    cx = float(self.centers_xy[int(c)][0])
                    cy = float(self.centers_xy[int(c)][1])
                    hover_x.append(cx)
                    hover_y.append(cy)
                    layer_idx = int(self.layer_per_cell[int(c)])
                    hover_text = (
                        f"{well_name} ({well_type})<br>"
                        f"#{int(c)} (k={layer_idx})"
                    )
                    hover_t.append(hover_text)

                # Draw non-active circles first, then active circles on top.
                circle_order = sorted(
                    cells_in_well,
                    key=lambda c: int(self.layer_per_cell[int(c)]) == active_layer,
                )
                for c in circle_order:
                    cx = float(self.centers_xy[int(c)][0])
                    cy = float(self.centers_xy[int(c)][1])
                    circle_layer = int(self.layer_per_cell[int(c)])
                    is_active_layer = circle_layer == active_layer
                    if is_active_layer:
                        local_radius = circle_radius
                    else:
                        local_radius = 0.5 * circle_radius
                    circle_x, circle_y = _circle_polygon(
                        cx, cy, local_radius, n_points=48
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=circle_x,
                            y=circle_y,
                            mode="lines",
                            fill="toself",
                            line={"color": "black", "width": 0.8},
                            fillcolor=(
                                well_color
                                if is_active_layer
                                else "rgba(0,0,0,0)"
                            ),
                            name="well-circle",
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )

                fig.add_trace(
                    go.Scatter(
                        x=hover_x,
                        y=hover_y,
                        mode="markers",
                        marker={"size": 10, "color": "rgba(0,0,0,0.001)"},
                        text=hover_t,
                        hovertemplate="%{text}<extra></extra>",
                        name="well-hover",
                        showlegend=False,
                    )
                )

        return fig
