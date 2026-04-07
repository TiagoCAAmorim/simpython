"""Minimal Dash app template for map workflows.

This module provides a small, testable Dash application skeleton that will be
expanded in later steps to host map, line, scatter, and table components.
"""

from __future__ import annotations

import numpy as np
from dash import Dash, Input, Output, ctx, dcc, html, no_update
import plotly.graph_objects as go

from rsimpy.common.plot_dash import DashMapPlot, add_triangle_trace


PALETTE_OPTIONS = [
    {"label": "Turbo", "value": "Turbo"},
    {"label": "Viridis", "value": "Viridis"},
    {"label": "Plasma", "value": "Plasma"},
    {"label": "Inferno", "value": "Inferno"},
    {"label": "Magma", "value": "Magma"},
    {"label": "Cividis", "value": "Cividis"},
    {"label": "Greys", "value": "Greys"},
]


def build_triangle_demo_figure(direction="up", size=0.3, show_triangle=True):
    """Build a small figure used to validate controls + callback wiring."""
    fig = go.Figure()
    fig.update_layout(
        title="Dash Map Template - Triangle Demo",
        xaxis_title="X",
        yaxis_title="Y",
        xaxis={"range": [0.0, 1.0]},
        yaxis={"range": [0.0, 1.0], "scaleanchor": "x", "scaleratio": 1},
        template="plotly_white",
        margin={"l": 30, "r": 20, "t": 40, "b": 30},
    )

    if show_triangle:
        add_triangle_trace(
            fig=fig,
            center_x=0.5,
            center_y=0.5,
            size=float(size),
            direction=direction,
            line_color="black",
            fill_color="#cc2f2f",
            name="triangle",
            hover_text=f"direction={direction}",
        )

    return fig


def _make_regular_grid_vertices(n_rows, n_cols, dx=1.0, dy=1.0):
    """Create [n_cells, 4, 3] vertices for an axis-aligned regular grid."""
    vertices = []
    for row in range(n_rows):
        y0 = row * dy
        y1 = (row + 1) * dy
        for col in range(n_cols):
            x0 = col * dx
            x1 = (col + 1) * dx
            vertices.append(
                [
                    [x0, y0, 0.0],
                    [x1, y0, 0.0],
                    [x1, y1, 0.0],
                    [x0, y1, 0.0],
                ]
            )
    return np.asarray(vertices, dtype=float)


def build_step_2_2_demo_map_plot(n_rows=5, n_cols=6, n_days=5):
    """Build the working example with two layers and cross-layer triangles."""
    layer1_rows, layer1_cols = n_rows, n_cols
    layer2_rows, layer2_cols = 3, 4
    layer3_rows, layer3_cols = 3, 4

    # Create grid vertices and shift origin to (1000, 10000) for demo
    origin_x, origin_y = 1000.0, 10000.0
    layer1_vertices = _make_regular_grid_vertices(layer1_rows, layer1_cols) + np.array([origin_x, origin_y, 0.0])
    layer2_vertices = _make_regular_grid_vertices(layer2_rows, layer2_cols) + np.array([origin_x, origin_y, 0.0])
    layer3_vertices = _make_regular_grid_vertices(layer3_rows, layer3_cols) + np.array([origin_x, origin_y, 0.0])

    # Add synthetic z variation for contour rendering in Step 2.4.
    for layer_idx, layer_vertices in enumerate([layer1_vertices, layer2_vertices, layer3_vertices], start=1):
        local_x = layer_vertices[:, :, 0] - origin_x
        local_y = layer_vertices[:, :, 1] - origin_y
        layer_vertices[:, :, 2] = (2.0 * local_x + 3.0 * local_y) + 10.0 * float(layer_idx)

    vertices = np.concatenate([layer1_vertices, layer2_vertices, layer3_vertices], axis=0)
    layer_sizes = [
        layer1_rows * layer1_cols,
        layer2_rows * layer2_cols,
        layer3_rows * layer3_cols,
    ]
    n_cells = vertices.shape[0]

    base_index = np.arange(n_cells, dtype=float)
    row_values = np.concatenate([
        np.array([row + 1 for row in range(layer1_rows) for _ in range(layer1_cols)], dtype=float),
        np.array([row + 1 for row in range(layer2_rows) for _ in range(layer2_cols)], dtype=float),
        np.array([row + 1 for row in range(layer3_rows) for _ in range(layer3_cols)], dtype=float),
    ])
    col_values = np.concatenate([
        np.array([col + 1 for _ in range(layer1_rows) for col in range(layer1_cols)], dtype=float),
        np.array([col + 1 for _ in range(layer2_rows) for col in range(layer2_cols)], dtype=float),
        np.array([col + 1 for _ in range(layer3_rows) for col in range(layer3_cols)], dtype=float),
    ])

    grid_data = np.zeros((4, n_days, n_cells), dtype=float)
    for day in range(n_days):
        grid_data[0, day, :] = base_index
        grid_data[1, day, :] = col_values
        grid_data[2, day, :] = row_values
        grid_data[3, day, :] = base_index + 30.0 * float(day)

    mean_z_values = np.mean(vertices[:, :, 2], axis=1)
    grid_data = np.concatenate([grid_data, np.zeros((1, n_days, n_cells), dtype=float)], axis=0)
    for day in range(n_days):
        grid_data[4, day, :] = mean_z_values

    property_names = ["Cell Index", "Column", "Row", "Index + 30*Day", "Mean Z"]
    cell_names = [
        f"({row+1},{col+1},1)"
        for row in range(layer1_rows)
        for col in range(layer1_cols)
    ] + [
        f"({row+1},{col+1},2)"
        for row in range(layer2_rows)
        for col in range(layer2_cols)
    ] + [
        f"({row+1},{col+1},3)"
        for row in range(layer3_rows)
        for col in range(layer3_cols)
    ]

    conn_pairs = []
    # Same-layer neighbor connections inside layer 1.
    for row in range(layer1_rows):
        for col in range(layer1_cols):
            idx = row * layer1_cols + col
            if col < layer1_cols - 1:
                conn_pairs.append((idx, idx + 1))
            if row < layer1_rows - 1:
                conn_pairs.append((idx, idx + layer1_cols))
    # Same-layer neighbor connections inside layer 2.
    layer2_offset = layer_sizes[0]
    for row in range(layer2_rows):
        for col in range(layer2_cols):
            idx = layer2_offset + row * layer2_cols + col
            if col < layer2_cols - 1:
                conn_pairs.append((idx, idx + 1))
            if row < layer2_rows - 1:
                conn_pairs.append((idx, idx + layer2_cols))
    # Same-layer neighbor connections inside layer 3.
    layer3_offset = layer_sizes[0] + layer_sizes[1]
    for row in range(layer3_rows):
        for col in range(layer3_cols):
            idx = layer3_offset + row * layer3_cols + col
            if col < layer3_cols - 1:
                conn_pairs.append((idx, idx + 1))
            if row < layer3_rows - 1:
                conn_pairs.append((idx, idx + layer3_cols))

    # Cross-layer connections so that the middle layer shows both up and down triangles.
    for idx in range(min(layer_sizes[1], layer_sizes[2])):
        conn_pairs.append((layer2_offset + idx, idx))
        conn_pairs.append((layer2_offset + idx, layer3_offset + idx))

    connection_indices = np.asarray(conn_pairs, dtype=int).T
    n_connections = connection_indices.shape[1]
    connection_data = np.zeros((1, n_days, n_connections), dtype=float)
    for day in range(n_days):
        connection_data[0, day, :] = float(day + 1)

    wells = {
        "WELL-A,prod": np.asarray([0, layer2_offset + 0, layer3_offset + 0], dtype=int),
        "WELL-B,injw": np.asarray([5, layer2_offset + 5, layer3_offset + 5], dtype=int),
        "WELL-C,inj": np.asarray([10, layer2_offset + 10, layer3_offset + 10], dtype=int),
        "WELL-E,injg": np.asarray([2, layer2_offset + 2, layer3_offset + 2], dtype=int),
        "WELL-D,closed": np.asarray([14], dtype=int),
    }

    return DashMapPlot(
        vertices=vertices,
        layer_sizes=layer_sizes,
        grid_data=grid_data,
        property_names=property_names,
        cell_names=cell_names,
        connection_indices=connection_indices,
        connection_data=connection_data,
        connection_property_names=["Connectivity"],
        wells=wells,
        title="Step 2.2 - Interactive Map Controls",
        width=1000,
        height=700,
    )


def create_dash_template_app(map_plot=None):
    """Create Dash app with property/day/layer controls wired to DashMapPlot."""
    if map_plot is None:
        map_plot = build_step_2_2_demo_map_plot()

    n_properties, n_days, _ = map_plot.grid_data.shape
    n_layers = len(map_plot.layer_sizes)
    has_connections = map_plot.has_connections()
    has_contours = map_plot.has_contours()
    has_wells = map_plot.has_wells()

    day_marks = {idx: str(idx) for idx in range(n_days)}
    layer_marks = {idx + 1: str(idx + 1) for idx in range(n_layers)}

    app = Dash(__name__)

    app.layout = html.Div(
        [
            html.H3("rsimpy Dash Map - Step 2.3"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Layer"),
                            dcc.Slider(
                                id="map-layer-slider",
                                min=1,
                                max=max(1, n_layers),
                                step=1,
                                marks=layer_marks,
                                value=1,
                                disabled=n_layers == 1,
                            ),
                            html.Br(),
                            html.Label("Day"),
                            dcc.Slider(
                                id="map-day-slider",
                                min=0,
                                max=max(0, n_days - 1),
                                step=1,
                                marks=day_marks,
                                value=0,
                            ),
                            html.Hr(style={"margin": "12px 0"}),
                            html.Div(
                                [
                                    dcc.Checklist(
                                        id="map-show-grid",
                                        options=[
                                            {
                                                "label": "Show grid",
                                                "value": "show",
                                            }
                                        ],
                                        value=["show"],
                                        style={"marginRight": "12px"},
                                    ),
                                    dcc.Checklist(
                                        id="map-grid-options-toggle",
                                        options=[
                                            {
                                                "label": "Options",
                                                "value": "show",
                                                "disabled": False,
                                            }
                                        ],
                                        value=[],
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "columnGap": "12px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Label("Property"),
                                    dcc.Dropdown(
                                        id="map-property-dropdown",
                                        options=[
                                            {"label": map_plot.property_names[i], "value": i}
                                            for i in range(n_properties)
                                        ],
                                        value=0,
                                        clearable=False,
                                    ),
                                ],
                                id="map-property-controls-group",
                                style={"display": "block"},
                            ),
                            html.Div(
                                [
                                    html.Label("Grid palette"),
                                    dcc.Dropdown(
                                        id="map-grid-palette",
                                        options=PALETTE_OPTIONS,
                                        value="Turbo",
                                        clearable=False,
                                    ),
                                ],
                                id="map-grid-controls-group",
                                style={"display": "block"},
                            ),
                            html.Hr(style={"margin": "12px 0"}),
                            html.Div(
                                [
                                    dcc.Checklist(
                                        id="map-show-connections",
                                        options=[
                                            {
                                                "label": "Show connections",
                                                "value": "show",
                                                "disabled": not has_connections,
                                            }
                                        ],
                                        value=[],
                                        style={"marginRight": "12px"},
                                    ),
                                    dcc.Checklist(
                                        id="map-connection-options-toggle",
                                        options=[
                                            {
                                                "label": "Options",
                                                "value": "show",
                                                "disabled": not has_connections,
                                            }
                                        ],
                                        value=[],
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "columnGap": "12px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Div("Connections", style={"fontWeight": "bold"}),
                                    html.Label("Connection palette"),
                                    dcc.Dropdown(
                                        id="map-connection-palette",
                                        options=PALETTE_OPTIONS,
                                        value="Plasma",
                                        clearable=False,
                                    ),
                                    html.Br(),
                                    html.Label("Connection line width"),
                                    dcc.Slider(
                                        id="map-connection-width",
                                        min=1.0,
                                        max=10.0,
                                        step=0.5,
                                        value=5.0,
                                        disabled=not has_connections,
                                    ),
                                    html.Br(),
                                    html.Label("Gradient segments"),
                                    dcc.Slider(
                                        id="map-connection-segments",
                                        min=3,
                                        max=20,
                                        step=1,
                                        value=10,
                                        disabled=not has_connections,
                                    ),
                                ],
                                id="map-connection-controls-group",
                                style={"display": "none"},
                            ),
                            html.Hr(style={"margin": "12px 0"}),
                            html.Div(
                                [
                                    dcc.Checklist(
                                        id="map-show-wells",
                                        options=[
                                            {
                                                "label": "Show wells",
                                                "value": "show",
                                                "disabled": not has_wells,
                                            }
                                        ],
                                        value=[],
                                        style={"marginRight": "12px"},
                                    ),
                                    dcc.Checklist(
                                        id="map-well-options-toggle",
                                        options=[
                                            {
                                                "label": "Options",
                                                "value": "show",
                                                "disabled": not has_wells,
                                            }
                                        ],
                                        value=[],
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "columnGap": "12px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Div("Wells", style={"fontWeight": "bold"}),
                                    html.Label("Well size (%)"),
                                    dcc.Slider(
                                        id="map-well-size",
                                        min=5,
                                        max=200,
                                        step=5,
                                        value=20,
                                        disabled=not has_wells,
                                    ),
                                ],
                                id="map-well-controls-group",
                                style={"display": "none"},
                            ),
                            html.Hr(style={"margin": "12px 0"}),
                            html.Div(
                                [
                                    dcc.Checklist(
                                        id="map-show-contours",
                                        options=[
                                            {
                                                "label": "Show contours",
                                                "value": "show",
                                                "disabled": not has_contours,
                                            }
                                        ],
                                        value=[],
                                        style={"marginRight": "12px"},
                                    ),
                                    dcc.Checklist(
                                        id="map-contour-options-toggle",
                                        options=[
                                            {
                                                "label": "Options",
                                                "value": "show",
                                                "disabled": not has_contours,
                                            }
                                        ],
                                        value=[],
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "columnGap": "12px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Div("Contours", style={"fontWeight": "bold"}),
                                    html.Label("Contour count"),
                                    dcc.Slider(
                                        id="map-contour-count",
                                        min=2,
                                        max=15,
                                        step=1,
                                        value=7,
                                        disabled=not has_contours,
                                    ),
                                ],
                                id="map-contour-controls-group",
                                style={"display": "none"},
                            ),
                        ],
                        style={"width": "24%", "display": "inline-block", "verticalAlign": "top"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="map-graph",
                                figure=map_plot.create_map_figure(
                                    property_index=0,
                                    day_index=0,
                                    layer=1,
                                    add_connections=False,
                                    add_contours=False,
                                    add_wells=False,
                                    contour_count=7,
                                ),
                                config={
                                    "displaylogo": False,
                                    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                                    "scrollZoom": True,
                                },
                            )
                        ],
                        style={"width": "75%", "display": "inline-block"},
                    ),
                ]
            ),
        ],
        style={"padding": "12px"},
    )

    @app.callback(
        Output("map-grid-options-toggle", "value"),
        Output("map-connection-options-toggle", "value"),
        Output("map-contour-options-toggle", "value"),
        Output("map-well-options-toggle", "value"),
        Input("map-show-grid", "value"),
        Input("map-show-connections", "value"),
        Input("map-show-contours", "value"),
        Input("map-show-wells", "value"),
        prevent_initial_call=True,
    )
    def _sync_options_toggles(_show_grid_values, _show_connections_values, _show_contours_values, _show_wells_values):
        # Reset only the options toggle that corresponds to the changed show toggle.
        trigger = ctx.triggered_id
        grid_value = [] if trigger == "map-show-grid" else no_update
        connection_value = [] if trigger == "map-show-connections" else no_update
        contour_value = [] if trigger == "map-show-contours" else no_update
        well_value = [] if trigger == "map-show-wells" else no_update
        return grid_value, connection_value, contour_value, well_value

    @app.callback(
        Output("map-graph", "figure"),
        Output("map-property-controls-group", "style"),
        Output("map-grid-controls-group", "style"),
        Output("map-connection-controls-group", "style"),
        Output("map-contour-controls-group", "style"),
        Output("map-well-controls-group", "style"),
        Output("map-grid-options-toggle", "options"),
        Output("map-connection-options-toggle", "options"),
        Output("map-contour-options-toggle", "options"),
        Output("map-well-options-toggle", "options"),
        Input("map-show-grid", "value"),
        Input("map-property-dropdown", "value"),
        Input("map-day-slider", "value"),
        Input("map-grid-palette", "value"),
        Input("map-layer-slider", "value"),
        Input("map-show-connections", "value"),
        Input("map-connection-options-toggle", "value"),
        Input("map-show-contours", "value"),
        Input("map-contour-options-toggle", "value"),
        Input("map-grid-options-toggle", "value"),
        Input("map-show-wells", "value"),
        Input("map-well-options-toggle", "value"),
        Input("map-contour-count", "value"),
        Input("map-connection-palette", "value"),
        Input("map-connection-width", "value"),
        Input("map-connection-segments", "value"),
        Input("map-well-size", "value"),
    )
    def _update_map_figure(
        show_grid_values,
        property_index,
        day_index,
        grid_palette,
        layer,
        show_connections_values,
        connection_options_values,
        show_contours_values,
        contour_options_values,
        grid_options_values,
        show_wells_values,
        well_options_values,
        contour_count,
        connection_palette,
        connection_width,
        connection_segments,
        well_size,
    ):
        show_connections = (
            map_plot.has_connections() and "show" in (show_connections_values or [])
        )
        show_grid = "show" in (show_grid_values or [])
        show_contours = (
            map_plot.has_contours() and "show" in (show_contours_values or [])
        )
        show_wells = map_plot.has_wells() and "show" in (show_wells_values or [])
        show_grid_options = show_grid and "show" in (grid_options_values or [])
        show_connection_options = show_connections and "show" in (connection_options_values or [])
        show_contour_options = show_contours and "show" in (contour_options_values or [])
        show_well_options = show_wells and "show" in (well_options_values or [])
        property_style = {"display": "block" if show_grid else "none"}
        grid_style = {"display": "block" if show_grid_options else "none"}
        connection_style = {"display": "block" if show_connection_options else "none"}
        contour_style = {"display": "block" if show_contour_options else "none"}
        well_style = {"display": "block" if show_well_options else "none"}
        grid_options = [{"label": "Options", "value": "show", "disabled": not show_grid}]
        connection_options = [{
            "label": "Options",
            "value": "show",
            "disabled": (not has_connections) or (not show_connections),
        }]
        contour_options = [{
            "label": "Options",
            "value": "show",
            "disabled": (not has_contours) or (not show_contours),
        }]
        well_options = [{
            "label": "Options",
            "value": "show",
            "disabled": (not has_wells) or (not show_wells),
        }]
        return (
            map_plot.create_map_figure(
                property_index=int(property_index),
                day_index=int(day_index),
                layer=int(layer),
                palette=str(grid_palette),
                add_grid=show_grid,
                add_connections=show_connections,
                add_contours=show_contours,
                add_wells=show_wells,
                contour_count=int(contour_count),
                connection_palette=str(connection_palette),
                connection_width=float(connection_width),
                connection_line_segments=int(connection_segments),
                well_size_percent=float(well_size),
            ),
            property_style,
            grid_style,
            connection_style,
            contour_style,
            well_style,
            grid_options,
            connection_options,
            contour_options,
            well_options,
        )

    return app


def create_step_2_2_working_example_app():
    """Create the ready-to-run Step 2.2 example app."""
    return create_dash_template_app(map_plot=build_step_2_2_demo_map_plot())


if __name__ == "__main__":
    demo_app = create_step_2_2_working_example_app()
    demo_app.run(debug=True)
