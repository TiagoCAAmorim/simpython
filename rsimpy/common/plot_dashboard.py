# pylint: disable=too-many-lines
"""Dashboard composition utilities for Dash-based plot components."""

from __future__ import annotations

import numpy as np
from dash import Dash, Input, Output, Patch, ctx, dash_table, dcc, html, no_update

from rsimpy.common.plot_dash import (
    DashLinePlot,
    DashMapPlot,
    DashScatterPlot,
    DashTable,
)


PALETTE_OPTIONS = [
    {"label": "Turbo", "value": "Turbo"},
    {"label": "Viridis", "value": "Viridis"},
    {"label": "Plasma", "value": "Plasma"},
    {"label": "Inferno", "value": "Inferno"},
    {"label": "Magma", "value": "Magma"},
    {"label": "Cividis", "value": "Cividis"},
    {"label": "Greys", "value": "Greys"},
]


_TAB_STYLE = {"padding": "6px 12px"}
_TAB_SELECTED_STYLE = {"padding": "6px 12px", "fontWeight": "600"}

_SLIDER_TOOLTIP = {"placement": "bottom", "always_visible": True}

_COLOR_LIMITS_STYLE = {"display": "flex", "alignItems": "center", "gap": "4px", "marginTop": "6px"}
_COLOR_ERROR_STYLE = {"color": "red", "fontSize": "11px", "marginTop": "2px"}
_INPUT_SMALL = {"width": "88px", "fontSize": "12px"}


def _parse_color_limits(vmin_input, vmax_input, scale_mode, auto_vmin=None, auto_vmax=None):
    """Parse and validate vmin/vmax inputs. Returns (color_limits, error_msg).

    When only one bound is provided the missing bound is filled from the
    auto_vmin / auto_vmax fallbacks (data-derived range). If the auto
    fallback still violates max > min, a 10 % padding is applied instead.
    """
    if vmin_input is None and vmax_input is None:
        return None, ""

    only_min = vmin_input is not None and vmax_input is None
    only_max = vmin_input is None and vmax_input is not None

    if only_min:
        if auto_vmax is None:
            return None, "Provide both Min and Max."
        vmin_val = float(vmin_input)
        vmax_val = float(auto_vmax)
        if vmax_val <= vmin_val:
            delta = 0.1 * abs(vmin_val)
            vmax_val = vmin_val + (delta if delta > 1e-12 else 1.0)
    elif only_max:
        if auto_vmin is None:
            return None, "Provide both Min and Max."
        vmax_val = float(vmax_input)
        vmin_val = float(auto_vmin)
        if vmin_val >= vmax_val:
            delta = 0.1 * abs(vmax_val)
            vmin_val = vmax_val - (delta if delta > 1e-12 else 1.0)
    else:
        vmin_val = float(vmin_input)
        vmax_val = float(vmax_input)
        if vmax_val <= vmin_val:
            return None, "Max must be greater than Min."

    if scale_mode == "log" and vmin_val <= 0.0:
        return None, "Min must be > 0 for log scale."
    return [vmin_val, vmax_val], ""


class DashDashboard:
    """Compose map/line/scatter/table components into one Dash layout."""

    def __init__(
        self,
        map_plot=None,
        line_plot=None,
        scatter_plot=None,
        table_plot=None,
        title="Dash Dashboard",
    ):
        self.map_plot = map_plot
        self.line_plot = line_plot
        self.scatter_plot = scatter_plot
        self.table_plot = table_plot
        self.title = str(title)

        if all(
            component is None
            for component in (
                self.map_plot,
                self.line_plot,
                self.scatter_plot,
                self.table_plot,
            )
        ):
            raise ValueError(
                "DashDashboard requires at least one component "
                "(map_plot, line_plot, scatter_plot, or table_plot)."
            )

    def create_layout(
        self,
        map_kwargs=None,
        line_kwargs=None,
        scatter_kwargs=None,
        table_page_size=None,
    ):
        """Create a responsive grid layout with available components."""
        map_kwargs = {} if map_kwargs is None else dict(map_kwargs)
        line_kwargs = {} if line_kwargs is None else dict(line_kwargs)
        scatter_kwargs = {} if scatter_kwargs is None else dict(scatter_kwargs)

        panels = []

        if self.map_plot is not None:
            map_fig = self.map_plot.create_map_figure(**map_kwargs)
            map_fig.update_layout(autosize=True, width=None, height=None)
            panels.append(
                html.Div(
                    [
                        html.H4("Map", style={"margin": "0 0 8px 0"}),
                        dcc.Graph(
                            id="dashboard-map-graph",
                            figure=map_fig,
                            responsive=True,
                            style={"height": "100%", "width": "100%"},
                            config={
                                "displaylogo": False,
                                "scrollZoom": True,
                                "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "300px",
                        "height": "100%",
                    },
                )
            )

        if self.line_plot is not None:
            line_fig = self.line_plot.create_line_figure(**line_kwargs)
            line_fig.update_layout(autosize=True, width=None, height=None)
            panels.append(
                html.Div(
                    [
                        html.H4("Line", style={"margin": "0 0 8px 0"}),
                        dcc.Graph(
                            id="dashboard-line-graph",
                            figure=line_fig,
                            responsive=True,
                            style={"height": "100%", "width": "100%"},
                            config={
                                "displaylogo": False,
                                "scrollZoom": True,
                                "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "300px",
                        "height": "100%",
                    },
                )
            )

        if self.scatter_plot is not None:
            scatter_fig = self.scatter_plot.create_scatter_figure(**scatter_kwargs)
            scatter_fig.update_layout(autosize=True, width=None, height=None)
            panels.append(
                html.Div(
                    [
                        html.H4("Scatter", style={"margin": "0 0 8px 0"}),
                        dcc.Graph(
                            id="dashboard-scatter-graph",
                            figure=scatter_fig,
                            responsive=True,
                            style={"height": "100%", "width": "100%"},
                            config={
                                "displaylogo": False,
                                "scrollZoom": True,
                                "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": "300px",
                        "height": "100%",
                    },
                )
            )

        if self.table_plot is not None:
            page_size = table_page_size
            if page_size is None:
                page_size = self.table_plot.page_size
            table_props = self.table_plot.create_dash_table_props(page_size=page_size)
            panels.append(
                html.Div(
                    [
                        html.H4("Table", style={"margin": "0 0 8px 0"}),
                        dash_table.DataTable(
                            id="dashboard-table",
                            **table_props,
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "left", "padding": "6px"},
                            style_header={"fontWeight": "bold"},
                        ),
                    ],
                    style={"minHeight": "300px", "height": "100%"},
                )
            )

        return html.Div(
            [
                html.H3(self.title, style={"margin": "0 0 10px 0"}),
                html.Div(
                    panels,
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(420px, 1fr))",
                        "gap": "12px",
                        "width": "100%",
                        "height": "calc(100vh - 70px)",
                    },
                ),
            ],
            style={"padding": "12px", "boxSizing": "border-box", "height": "100vh"},
        )

    def create_app(
        self,
        map_kwargs=None,
        line_kwargs=None,
        scatter_kwargs=None,
        table_page_size=None,
    ):
        """Create a Dash app instance with composed dashboard layout."""
        app = Dash(__name__)
        app.layout = self.create_layout(
            map_kwargs=map_kwargs,
            line_kwargs=line_kwargs,
            scatter_kwargs=scatter_kwargs,
            table_page_size=table_page_size,
        )
        return app


class DashMultiPanelDashboard:
    """Build a multi-panel dashboard from dicts of plot objects.

    The user provides dictionaries where keys become tab labels and values are
    plot objects. The dashboard groups tabs by type (Maps, Line Plots,
    Scatter Plots, Tables) and adds a second tab level for each object.
    """

    def __init__(
        self,
        map_plots=None,
        line_plots=None,
        scatter_plots=None,
        table_plots=None,
        title="Dash Multi-Panel Dashboard",
    ):
        self.map_plots = self._normalize_map_panel_dict(map_plots)
        self.line_plots = self._normalize_panel_dict(
            line_plots,
            expected_type=DashLinePlot,
            name="line_plots",
        )
        self.scatter_plots = self._normalize_panel_dict(
            scatter_plots,
            expected_type=DashScatterPlot,
            name="scatter_plots",
        )
        self.table_plots = self._normalize_panel_dict(
            table_plots,
            expected_type=DashTable,
            name="table_plots",
        )
        self.title = str(title)

        if (
            len(self.map_plots) == 0
            and len(self.line_plots) == 0
            and len(self.scatter_plots) == 0
            and len(self.table_plots) == 0
        ):
            raise ValueError(
                "DashMultiPanelDashboard requires at least one panel object."
            )

    @staticmethod
    def _normalize_panel_dict(values, expected_type, name):
        if values is None:
            return {}
        if not isinstance(values, dict):
            raise ValueError(f"{name} must be a dict mapping tab names to objects.")

        normalized = {}
        for key, value in values.items():
            if not isinstance(key, str) or len(key.strip()) == 0:
                raise ValueError(f"{name} keys must be non-empty strings.")
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"{name}['{key}'] must be an instance of "
                    f"{expected_type.__name__}."
                )
            normalized[str(key)] = value
        return normalized

    def _normalize_map_panel_dict(self, values):
        """Normalize map_plots dict accepting both DashMapPlot and DashMapCompare."""
        if values is None:
            return {}
        if not isinstance(values, dict):
            raise ValueError("map_plots must be a dict mapping tab names to objects.")

        normalized = {}
        for key, value in values.items():
            if not isinstance(key, str) or len(key.strip()) == 0:
                raise ValueError("map_plots keys must be non-empty strings.")
            if not isinstance(value, (DashMapPlot, DashMapCompare)):
                raise ValueError(
                    f"map_plots['{key}'] must be an instance of DashMapPlot or DashMapCompare."
                )
            normalized[str(key)] = value
        return normalized

    def _build_map_panel_tab(self, panel_name, map_plot, prefix):
        # Handle DashMapCompare specially by creating a side-by-side view with controls
        if isinstance(map_plot, DashMapCompare):
            map_a = map_plot.map_plot_a
            map_b = map_plot.map_plot_b
            n_properties = map_a.grid_data.shape[0]
            n_days = map_a.grid_data.shape[1]
            n_layers = len(map_a.layer_sizes)
            has_contours = map_a.has_contours() or map_b.has_contours()
            has_wells = map_a.has_wells() or map_b.has_wells()

            init_limits = map_plot._compute_synced_limits(0, log_scale=False)

            fig_a = map_a.create_map_figure(
                property_index=0, day_index=0, layer=1,
                add_grid=True, add_connections=False,
                add_contours=False, add_wells=False,
                color_limits=init_limits,
            )
            fig_b = map_b.create_map_figure(
                property_index=0, day_index=0, layer=1,
                add_grid=True, add_connections=False,
                add_contours=False, add_wells=False,
                color_limits=init_limits,
            )

            for fig in (fig_a, fig_b):
                fig.update_layout(autosize=True, width=None, height=None)

            return dcc.Tab(
                label=panel_name,
                style=_TAB_STYLE,
                selected_style=_TAB_SELECTED_STYLE,
                children=[
                    html.Div(
                        [
                            html.Div(
                                [
                                    # ── Controls panel ──────────────────────────────
                                    html.Div(
                                        [
                                            html.Label("Property"),
                                            dcc.Dropdown(
                                                id=f"{prefix}-property",
                                                options=[
                                                    {"label": map_a.property_names[i], "value": i}
                                                    for i in range(n_properties)
                                                ],
                                                value=0,
                                                clearable=False,
                                            ),
                                            html.Br(),
                                            html.Label("Layer"),
                                            dcc.Slider(
                                                id=f"{prefix}-layer",
                                                min=1,
                                                max=max(1, n_layers),
                                                step=1,
                                                value=1,
                                                marks={1: "1", n_layers: str(n_layers)},
                                                tooltip=_SLIDER_TOOLTIP,
                                                disabled=n_layers == 1,
                                            ),
                                            html.Br(),
                                            html.Label("Day"),
                                            dcc.Slider(
                                                id=f"{prefix}-day",
                                                min=0,
                                                max=max(0, n_days - 1),
                                                step=1,
                                                value=0,
                                                marks={0: "0", max(0, n_days - 1): str(max(0, n_days - 1))},
                                                tooltip=_SLIDER_TOOLTIP,
                                            ),
                                            html.Hr(style={"margin": "12px 0"}),
                                            html.Div(
                                                [
                                                    dcc.Checklist(
                                                        id=f"{prefix}-show-grid",
                                                        options=[{"label": "Grid", "value": "show"}],
                                                        value=["show"],
                                                        style={"marginRight": "12px"},
                                                    ),
                                                    dcc.Checklist(
                                                        id=f"{prefix}-grid-log",
                                                        options=[{"label": "Log", "value": "on"}],
                                                        value=[],
                                                        style={"marginRight": "12px"},
                                                    ),
                                                    dcc.Checklist(
                                                        id=f"{prefix}-grid-asinh",
                                                        options=[{"label": "Asinh", "value": "on"}],
                                                        value=[],
                                                        style={"marginRight": "12px"},
                                                    ),
                                                    dcc.Checklist(
                                                        id=f"{prefix}-grid-options",
                                                        options=[{"label": "Options", "value": "show"}],
                                                        value=[],
                                                    ),
                                                ],
                                                style={
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "columnGap": "8px",
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    html.Label("Grid palette"),
                                                    dcc.Dropdown(
                                                        id=f"{prefix}-palette",
                                                        options=PALETTE_OPTIONS,
                                                        value="Turbo",
                                                        clearable=False,
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Label(
                                                                "Color limits",
                                                                style={"fontSize": "12px"},
                                                            ),
                                                            html.Div(
                                                                [
                                                                    dcc.Input(
                                                                        id=f"{prefix}-vmin",
                                                                        type="number",
                                                                        placeholder="Min (auto)",
                                                                        debounce=True,
                                                                        style=_INPUT_SMALL,
                                                                    ),
                                                                    html.Span(
                                                                        "–",
                                                                        style={"margin": "0 4px"},
                                                                    ),
                                                                    dcc.Input(
                                                                        id=f"{prefix}-vmax",
                                                                        type="number",
                                                                        placeholder="Max (auto)",
                                                                        debounce=True,
                                                                        style=_INPUT_SMALL,
                                                                    ),
                                                                ],
                                                                style=_COLOR_LIMITS_STYLE,
                                                            ),
                                                            html.Div(
                                                                id=f"{prefix}-color-error",
                                                                style=_COLOR_ERROR_STYLE,
                                                            ),
                                                        ],
                                                        style={"marginTop": "8px"},
                                                    ),
                                                ],
                                                id=f"{prefix}-grid-controls-group",
                                                style={"display": "none"},
                                            ),
                                            html.Hr(style={"margin": "12px 0"}),
                                            html.Div(
                                                [
                                                    dcc.Checklist(
                                                        id=f"{prefix}-show-wells",
                                                        options=[
                                                            {
                                                                "label": "Wells",
                                                                "value": "show",
                                                                "disabled": not has_wells,
                                                            }
                                                        ],
                                                        value=[],
                                                        style={"marginRight": "12px"},
                                                    ),
                                                    dcc.Checklist(
                                                        id=f"{prefix}-well-options-toggle",
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
                                                style={"display": "flex", "alignItems": "center"},
                                            ),
                                            html.Div(
                                                [
                                                    html.Label("Well size (%)"),
                                                    dcc.Slider(
                                                        id=f"{prefix}-well-size",
                                                        min=5,
                                                        max=200,
                                                        step=5,
                                                        value=20,
                                                        disabled=not has_wells,
                                                        tooltip=_SLIDER_TOOLTIP,
                                                    ),
                                                ],
                                                id=f"{prefix}-well-controls-group",
                                                style={"display": "none"},
                                            ),
                                            html.Hr(style={"margin": "12px 0"}),
                                            html.Div(
                                                [
                                                    dcc.Checklist(
                                                        id=f"{prefix}-show-contours",
                                                        options=[
                                                            {
                                                                "label": "Contours",
                                                                "value": "show",
                                                                "disabled": not has_contours,
                                                            }
                                                        ],
                                                        value=[],
                                                        style={"marginRight": "12px"},
                                                    ),
                                                    dcc.Checklist(
                                                        id=f"{prefix}-contour-options",
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
                                                style={"display": "flex", "alignItems": "center"},
                                            ),
                                            html.Div(
                                                [
                                                    html.Label("Contour count"),
                                                    dcc.Slider(
                                                        id=f"{prefix}-contour-count",
                                                        min=2,
                                                        max=15,
                                                        step=1,
                                                        value=7,
                                                        disabled=not has_contours,
                                                        tooltip=_SLIDER_TOOLTIP,
                                                    ),
                                                ],
                                                id=f"{prefix}-contour-controls-group",
                                                style={"display": "none"},
                                            ),
                                        ],
                                        style={
                                            "flex": "0 0 220px",
                                            "paddingRight": "12px",
                                            "overflowY": "auto",
                                        },
                                    ),
                                    # ── Two map graphs ───────────────────────────────
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Label(
                                                        map_plot.label_a,
                                                        style={"fontWeight": "600", "marginBottom": "4px"},
                                                    ),
                                                    dcc.Graph(
                                                        id=f"{prefix}-graph-a",
                                                        figure=fig_a,
                                                        responsive=True,
                                                        style={"flex": "1 1 auto"},
                                                        config={
                                                            "displaylogo": False,
                                                            "scrollZoom": True,
                                                            "modeBarButtonsToRemove": [
                                                                "select2d",
                                                                "lasso2d",
                                                            ],
                                                        },
                                                    ),
                                                ],
                                                style={
                                                    "display": "flex",
                                                    "flexDirection": "column",
                                                    "flex": "1 1 auto",
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    html.Label(
                                                        map_plot.label_b,
                                                        style={"fontWeight": "600", "marginBottom": "4px"},
                                                    ),
                                                    dcc.Graph(
                                                        id=f"{prefix}-graph-b",
                                                        figure=fig_b,
                                                        responsive=True,
                                                        style={"flex": "1 1 auto"},
                                                        config={
                                                            "displaylogo": False,
                                                            "scrollZoom": True,
                                                            "modeBarButtonsToRemove": [
                                                                "select2d",
                                                                "lasso2d",
                                                            ],
                                                        },
                                                    ),
                                                ],
                                                style={
                                                    "display": "flex",
                                                    "flexDirection": "column",
                                                    "flex": "1 1 auto",
                                                },
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "flex": "1 1 auto",
                                            "gap": "8px",
                                        },
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "height": "100%",
                                    "minHeight": "0",
                                },
                            ),
                        ],
                        style={
                            "padding": "12px",
                            "boxSizing": "border-box",
                            "height": "100%",
                            "overflow": "hidden",
                        }
                    )
                ],
            )

        # Handle regular DashMapPlot
        n_properties, n_days, _ = map_plot.grid_data.shape
        n_layers = len(map_plot.layer_sizes)
        has_connections = map_plot.has_connections()
        has_contours = map_plot.has_contours()
        has_wells = map_plot.has_wells()

        initial = map_plot.create_map_figure(
            property_index=0,
            day_index=0,
            layer=1,
            add_grid=True,
            add_connections=False,
            add_contours=False,
            add_wells=False,
        )
        initial.update_layout(autosize=True, width=None, height=None)

        return dcc.Tab(
            label=panel_name,
            style=_TAB_STYLE,
            selected_style=_TAB_SELECTED_STYLE,
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Property"),
                                dcc.Dropdown(
                                    id=f"{prefix}-property",
                                    options=[
                                        {"label": map_plot.property_names[i], "value": i}
                                        for i in range(n_properties)
                                    ],
                                    value=0,
                                    clearable=False,
                                ),
                                html.Br(),
                                html.Label("Layer"),
                                dcc.Slider(
                                    id=f"{prefix}-layer",
                                    min=1,
                                    max=max(1, n_layers),
                                    step=1,
                                    value=1,
                                    marks={1: "1", n_layers: str(n_layers)},
                                    tooltip=_SLIDER_TOOLTIP,
                                    disabled=n_layers == 1,
                                ),
                                html.Br(),
                                html.Label("Day"),
                                dcc.Slider(
                                    id=f"{prefix}-day",
                                    min=0,
                                    max=max(0, n_days - 1),
                                    step=1,
                                    value=0,
                                    marks={0: "0", max(0, n_days - 1): str(max(0, n_days - 1))},
                                    tooltip=_SLIDER_TOOLTIP,
                                ),
                                html.Br(),
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id=f"{prefix}-show-grid",
                                            options=[{"label": "Grid", "value": "show"}],
                                            value=["show"],
                                            style={"marginRight": "10px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-grid-log-scale",
                                            options=[
                                                {
                                                    "label": "Log",
                                                    "value": "on",
                                                    "disabled": False,
                                                }
                                            ],
                                            value=[],
                                            style={"marginRight": "10px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-grid-asinh-scale",
                                            options=[
                                                {
                                                    "label": "Asinh",
                                                    "value": "on",
                                                    "disabled": False,
                                                }
                                            ],
                                            value=[],
                                            style={"marginRight": "10px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-grid-options-toggle",
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
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Grid palette"),
                                        dcc.Dropdown(
                                            id=f"{prefix}-grid-palette",
                                            options=PALETTE_OPTIONS,
                                            value="Turbo",
                                            clearable=False,
                                        ),
                                        html.Div(
                                            [
                                                html.Label(
                                                    "Color limits",
                                                    style={"fontSize": "12px"},
                                                ),
                                                html.Div(
                                                    [
                                                        dcc.Input(
                                                            id=f"{prefix}-vmin",
                                                            type="number",
                                                            placeholder="Min (auto)",
                                                            debounce=True,
                                                            style=_INPUT_SMALL,
                                                        ),
                                                        html.Span(
                                                            "–",
                                                            style={"margin": "0 4px"},
                                                        ),
                                                        dcc.Input(
                                                            id=f"{prefix}-vmax",
                                                            type="number",
                                                            placeholder="Max (auto)",
                                                            debounce=True,
                                                            style=_INPUT_SMALL,
                                                        ),
                                                    ],
                                                    style=_COLOR_LIMITS_STYLE,
                                                ),
                                                html.Div(
                                                    id=f"{prefix}-color-error",
                                                    style=_COLOR_ERROR_STYLE,
                                                ),
                                            ],
                                            style={"marginTop": "8px"},
                                        ),
                                    ],
                                    id=f"{prefix}-grid-controls-group",
                                    style={"display": "none"},
                                ),
                                html.Hr(style={"margin": "10px 0"}),
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id=f"{prefix}-show-connections",
                                            options=[
                                                {
                                                    "label": "Connections",
                                                    "value": "show",
                                                    "disabled": not has_connections,
                                                }
                                            ],
                                            value=[],
                                            style={"marginRight": "10px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-connection-log-scale",
                                            options=[
                                                {
                                                    "label": "Log",
                                                    "value": "on",
                                                    "disabled": True,
                                                }
                                            ],
                                            value=[],
                                            style={"marginRight": "10px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-connection-asinh-scale",
                                            options=[
                                                {
                                                    "label": "Asinh",
                                                    "value": "on",
                                                    "disabled": True,
                                                }
                                            ],
                                            value=[],
                                            style={"marginRight": "10px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-connection-options-toggle",
                                            options=[
                                                {
                                                    "label": "Options",
                                                    "value": "show",
                                                    "disabled": True,
                                                }
                                            ],
                                            value=[],
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Connection palette"),
                                        dcc.Dropdown(
                                            id=f"{prefix}-connection-palette",
                                            options=PALETTE_OPTIONS,
                                            value="Plasma",
                                            clearable=False,
                                        ),
                                        html.Br(),
                                        html.Label("Connection line width"),
                                        dcc.Slider(
                                            id=f"{prefix}-connection-width",
                                            min=1.0,
                                            max=10.0,
                                            step=0.5,
                                            value=5.0,
                                            disabled=not has_connections,
                                            tooltip=_SLIDER_TOOLTIP,
                                        ),
                                        html.Br(),
                                        html.Label("Gradient segments"),
                                        dcc.Slider(
                                            id=f"{prefix}-connection-segments",
                                            min=3,
                                            max=20,
                                            step=1,
                                            value=10,
                                            disabled=not has_connections,
                                            tooltip=_SLIDER_TOOLTIP,
                                        ),
                                    ],
                                    id=f"{prefix}-connection-controls-group",
                                    style={"display": "none"},
                                ),
                                html.Hr(style={"margin": "10px 0"}),
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id=f"{prefix}-show-wells",
                                            options=[
                                                {
                                                    "label": "Wells",
                                                    "value": "show",
                                                    "disabled": not has_wells,
                                                }
                                            ],
                                            value=[],
                                            style={"marginRight": "10px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-well-options-toggle",
                                            options=[
                                                {
                                                    "label": "Options",
                                                    "value": "show",
                                                    "disabled": True,
                                                }
                                            ],
                                            value=[],
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Well size (%)"),
                                        dcc.Slider(
                                            id=f"{prefix}-well-size",
                                            min=5,
                                            max=200,
                                            step=5,
                                            value=20,
                                            disabled=not has_wells,
                                            tooltip=_SLIDER_TOOLTIP,
                                        ),
                                    ],
                                    id=f"{prefix}-well-controls-group",
                                    style={"display": "none"},
                                ),
                                html.Hr(style={"margin": "10px 0"}),
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id=f"{prefix}-show-contours",
                                            options=[
                                                {
                                                    "label": "Contours",
                                                    "value": "show",
                                                    "disabled": not has_contours,
                                                }
                                            ],
                                            value=[],
                                            style={"marginRight": "10px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-contour-options-toggle",
                                            options=[
                                                {
                                                    "label": "Options",
                                                    "value": "show",
                                                    "disabled": True,
                                                }
                                            ],
                                            value=[],
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Contour count"),
                                        dcc.Slider(
                                            id=f"{prefix}-contour-count",
                                            min=2,
                                            max=15,
                                            step=1,
                                            value=7,
                                            disabled=not has_contours,
                                            tooltip=_SLIDER_TOOLTIP,
                                        ),
                                    ],
                                    id=f"{prefix}-contour-controls-group",
                                    style={"display": "none"},
                                ),
                            ],
                            style={"flex": "0 0 280px", "paddingRight": "12px"},
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id=f"{prefix}-graph",
                                    figure=initial,
                                    responsive=True,
                                    style={"height": "100%", "width": "100%"},
                                    config={
                                        "displaylogo": False,
                                        "scrollZoom": True,
                                        "modeBarButtonsToRemove": [
                                            "select2d",
                                            "lasso2d",
                                        ],
                                    },
                                )
                            ],
                            style={"flex": "1 1 auto", "height": "100%"},
                        ),
                    ],
                    style={"display": "flex", "height": "100%", "minHeight": "0"},
                )
            ],
        )

    def _build_line_panel_tab(self, panel_name, line_plot, prefix):
        has_secondary = len(line_plot.secondary_y) > 0
        initial = line_plot.create_line_figure(
            log_scale=False,
            log_scale_secondary=False,
            marker_mode=True,
        )
        initial.update_layout(autosize=True, width=None, height=None)

        return dcc.Tab(
            label=panel_name,
            style=_TAB_STYLE,
            selected_style=_TAB_SELECTED_STYLE,
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Checklist(
                                    id=f"{prefix}-log-y",
                                    options=[{"label": "Log-Y", "value": "on"}],
                                    value=[],
                                ),
                                dcc.Checklist(
                                    id=f"{prefix}-log-y2",
                                    options=[{"label": "Log-Y2", "value": "on"}],
                                    value=[],
                                    style={
                                        "display": "block" if has_secondary else "none"
                                    },
                                ),
                            ],
                            style={"flex": "0 0 220px", "paddingRight": "12px"},
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id=f"{prefix}-graph",
                                    figure=initial,
                                    responsive=True,
                                    style={"height": "100%", "width": "100%"},
                                    config={
                                        "displaylogo": False,
                                        "scrollZoom": True,
                                        "modeBarButtonsToRemove": [
                                            "select2d",
                                            "lasso2d",
                                        ],
                                    },
                                )
                            ],
                            style={"flex": "1 1 auto", "height": "100%"},
                        ),
                    ],
                    style={"display": "flex", "height": "100%", "minHeight": "0"},
                )
            ],
        )

    def _build_scatter_panel_tab(self, panel_name, scatter_plot, prefix):
        options = [{"label": key, "value": key} for key in scatter_plot.scatter_data.keys()]
        initial = scatter_plot.create_scatter_figure(property_name=[])
        initial.update_layout(autosize=True, width=None, height=None)

        return dcc.Tab(
            label=panel_name,
            style=_TAB_STYLE,
            selected_style=_TAB_SELECTED_STYLE,
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Property"),
                                dcc.Dropdown(
                                    id=f"{prefix}-property",
                                    options=options,
                                    value=[],
                                    multi=True,
                                    clearable=True,
                                    placeholder="Select one or more…",
                                ),
                                html.Br(),
                                dcc.Checklist(
                                    id=f"{prefix}-log-x",
                                    options=[{"label": "Log-X", "value": "on"}],
                                    value=[],
                                ),
                                dcc.Checklist(
                                    id=f"{prefix}-log-y",
                                    options=[{"label": "Log-Y", "value": "on"}],
                                    value=[],
                                ),
                                html.Hr(style={"margin": "8px 0"}),
                                dcc.Checklist(
                                    id=f"{prefix}-xy-line",
                                    options=[{"label": "X = Y line", "value": "on"}],
                                    value=[],
                                ),
                                dcc.Checklist(
                                    id=f"{prefix}-equal-axes",
                                    options=[{"label": "Equal axes", "value": "on"}],
                                    value=[],
                                ),
                            ],
                            style={"flex": "0 0 220px", "paddingRight": "12px"},
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id=f"{prefix}-graph",
                                    figure=initial,
                                    responsive=True,
                                    style={"height": "100%", "width": "100%"},
                                    config={
                                        "displaylogo": False,
                                        "scrollZoom": True,
                                        "modeBarButtonsToRemove": [
                                            "select2d",
                                            "lasso2d",
                                        ],
                                    },
                                )
                            ],
                            style={"flex": "1 1 auto", "height": "100%"},
                        ),
                    ],
                    style={"display": "flex", "height": "100%", "minHeight": "0"},
                )
            ],
        )

    def _build_table_panel_tab(self, panel_name, table_plot, prefix):
        props = table_plot.create_dash_table_props(page_size=int(table_plot.page_size))
        return dcc.Tab(
            label=panel_name,
            style=_TAB_STYLE,
            selected_style=_TAB_SELECTED_STYLE,
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Visible lines"),
                                dcc.Dropdown(
                                    id=f"{prefix}-page-size",
                                    options=[
                                        {"label": "10", "value": 10},
                                        {"label": "20", "value": 20},
                                        {"label": "50", "value": 50},
                                        {"label": "100", "value": 100},
                                    ],
                                    value=min(100, max(10, int(table_plot.page_size))),
                                    clearable=False,
                                ),
                                html.Br(),
                                html.Button(
                                    "Download CSV",
                                    id=f"{prefix}-download-btn",
                                    n_clicks=0,
                                ),
                                dcc.Download(id=f"{prefix}-download"),
                            ],
                            style={"flex": "0 0 220px", "paddingRight": "12px"},
                        ),
                        html.Div(
                            [
                                dash_table.DataTable(
                                    id=f"{prefix}-table",
                                    **props,
                                    style_table={"overflowX": "auto"},
                                    style_cell={"textAlign": "left", "padding": "6px"},
                                    style_header={"fontWeight": "bold"},
                                )
                            ],
                            style={"flex": "1 1 auto", "height": "100%"},
                        ),
                    ],
                    style={"display": "flex", "height": "100%", "minHeight": "0"},
                )
            ],
        )

    def create_layout(self):
        """Create nested tabs layout grouped by panel type."""
        top_level_tabs = []

        if len(self.map_plots) > 0:
            map_tabs = []
            for idx, (name, plot_obj) in enumerate(self.map_plots.items()):
                map_tabs.append(
                    self._build_map_panel_tab(name, plot_obj, prefix=f"mp-map-{idx}")
                )
            top_level_tabs.append(
                dcc.Tab(
                    label="Maps",
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED_STYLE,
                    children=[
                        dcc.Tabs(
                            map_tabs,
                            style={"flex": "1 1 auto", "minHeight": "0", "width": "100%"},
                            content_style={
                                "height": "calc(100vh - 180px)",
                                "width": "100%",
                                "padding": "6px 0 0 0",
                            },
                        )
                    ],
                )
            )

        if len(self.line_plots) > 0:
            line_tabs = []
            for idx, (name, plot_obj) in enumerate(self.line_plots.items()):
                line_tabs.append(
                    self._build_line_panel_tab(name, plot_obj, prefix=f"mp-line-{idx}")
                )
            top_level_tabs.append(
                dcc.Tab(
                    label="Line Plots",
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED_STYLE,
                    children=[
                        dcc.Tabs(
                            line_tabs,
                            style={"flex": "1 1 auto", "minHeight": "0", "width": "100%"},
                            content_style={
                                "height": "calc(100vh - 180px)",
                                "width": "100%",
                                "padding": "6px 0 0 0",
                            },
                        )
                    ],
                )
            )

        if len(self.scatter_plots) > 0:
            scatter_tabs = []
            for idx, (name, plot_obj) in enumerate(self.scatter_plots.items()):
                scatter_tabs.append(
                    self._build_scatter_panel_tab(
                        name,
                        plot_obj,
                        prefix=f"mp-scatter-{idx}",
                    )
                )
            top_level_tabs.append(
                dcc.Tab(
                    label="Scatter Plots",
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED_STYLE,
                    children=[
                        dcc.Tabs(
                            scatter_tabs,
                            style={"flex": "1 1 auto", "minHeight": "0", "width": "100%"},
                            content_style={
                                "height": "calc(100vh - 180px)",
                                "width": "100%",
                                "padding": "6px 0 0 0",
                            },
                        )
                    ],
                )
            )

        if len(self.table_plots) > 0:
            table_tabs = []
            for idx, (name, plot_obj) in enumerate(self.table_plots.items()):
                table_tabs.append(
                    self._build_table_panel_tab(name, plot_obj, prefix=f"mp-table-{idx}")
                )
            top_level_tabs.append(
                dcc.Tab(
                    label="Tables",
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED_STYLE,
                    children=[
                        dcc.Tabs(
                            table_tabs,
                            style={"flex": "1 1 auto", "minHeight": "0", "width": "100%"},
                            content_style={
                                "height": "calc(100vh - 180px)",
                                "width": "100%",
                                "padding": "6px 0 0 0",
                            },
                        )
                    ],
                )
            )

        return html.Div(
            [
                html.H3(self.title, style={"margin": "0 0 8px 0"}),
                dcc.Tabs(
                    top_level_tabs,
                    style={"flex": "1 1 auto", "minHeight": "0", "width": "100%"},
                    content_style={
                        "height": "calc(100vh - 120px)",
                        "width": "100%",
                        "padding": "6px 0 0 0",
                    },
                ),
            ],
            style={
                "height": "calc(100vh - 36px)",
                "width": "calc(100vw - 36px)",
                "padding": "12px",
                "boxSizing": "border-box",
                "overflow": "hidden",
                "display": "flex",
                "flexDirection": "column",
            },
        )

    def _register_map_callbacks(self, app):
        for idx, map_plot in enumerate(self.map_plots.values()):
            prefix = f"mp-map-{idx}"

            if isinstance(map_plot, DashMapCompare):
                # Register callbacks for DashMapCompare
                self._register_map_compare_callbacks(
                    app=app,
                    prefix=prefix,
                    map_compare=map_plot,
                )
            else:
                # Register callbacks for regular DashMapPlot
                has_connections = map_plot.has_connections()
                has_contours = map_plot.has_contours()
                has_wells = map_plot.has_wells()

                self._register_map_callback_factory(
                    app=app,
                    prefix=prefix,
                    map_plot=map_plot,
                    has_connections=has_connections,
                    has_contours=has_contours,
                    has_wells=has_wells,
                )

    def _register_map_callback_factory(
        self,
        app,
        prefix,
        map_plot,
        has_connections,
        has_contours,
        has_wells,
    ):
        @app.callback(
            Output(f"{prefix}-grid-options-toggle", "value"),
            Output(f"{prefix}-connection-options-toggle", "value"),
            Output(f"{prefix}-contour-options-toggle", "value"),
            Output(f"{prefix}-well-options-toggle", "value"),
            Input(f"{prefix}-show-grid", "value"),
            Input(f"{prefix}-show-connections", "value"),
            Input(f"{prefix}-show-contours", "value"),
            Input(f"{prefix}-show-wells", "value"),
            prevent_initial_call=True,
        )
        def _sync_options_toggles(
            _show_grid_values,
            _show_connections_values,
            _show_contours_values,
            _show_wells_values,
        ):
            trigger = ctx.triggered_id
            grid_value = [] if trigger == f"{prefix}-show-grid" else no_update
            connection_value = (
                [] if trigger == f"{prefix}-show-connections" else no_update
            )
            contour_value = [] if trigger == f"{prefix}-show-contours" else no_update
            well_value = [] if trigger == f"{prefix}-show-wells" else no_update
            return grid_value, connection_value, contour_value, well_value

        @app.callback(
            Output(f"{prefix}-graph", "figure"),
            Output(f"{prefix}-grid-controls-group", "style"),
            Output(f"{prefix}-connection-controls-group", "style"),
            Output(f"{prefix}-contour-controls-group", "style"),
            Output(f"{prefix}-well-controls-group", "style"),
            Output(f"{prefix}-grid-log-scale", "options"),
            Output(f"{prefix}-grid-asinh-scale", "options"),
            Output(f"{prefix}-connection-log-scale", "options"),
            Output(f"{prefix}-connection-asinh-scale", "options"),
            Output(f"{prefix}-grid-options-toggle", "options"),
            Output(f"{prefix}-connection-options-toggle", "options"),
            Output(f"{prefix}-contour-options-toggle", "options"),
            Output(f"{prefix}-well-options-toggle", "options"),
            Output(f"{prefix}-color-error", "children"),
            Input(f"{prefix}-property", "value"),
            Input(f"{prefix}-day", "value"),
            Input(f"{prefix}-layer", "value"),
            Input(f"{prefix}-show-grid", "value"),
            Input(f"{prefix}-grid-palette", "value"),
            Input(f"{prefix}-grid-log-scale", "value"),
            Input(f"{prefix}-grid-asinh-scale", "value"),
            Input(f"{prefix}-show-connections", "value"),
            Input(f"{prefix}-connection-options-toggle", "value"),
            Input(f"{prefix}-show-contours", "value"),
            Input(f"{prefix}-contour-options-toggle", "value"),
            Input(f"{prefix}-grid-options-toggle", "value"),
            Input(f"{prefix}-show-wells", "value"),
            Input(f"{prefix}-well-options-toggle", "value"),
            Input(f"{prefix}-contour-count", "value"),
            Input(f"{prefix}-connection-palette", "value"),
            Input(f"{prefix}-connection-width", "value"),
            Input(f"{prefix}-connection-segments", "value"),
            Input(f"{prefix}-connection-log-scale", "value"),
            Input(f"{prefix}-connection-asinh-scale", "value"),
            Input(f"{prefix}-well-size", "value"),
            Input(f"{prefix}-vmin", "value"),
            Input(f"{prefix}-vmax", "value"),
        )
        def _update_map(
            property_index,
            day_index,
            layer,
            show_grid_values,
            grid_palette,
            grid_log_scale_values,
            grid_asinh_scale_values,
            show_connection_values,
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
            connection_log_scale_values,
            connection_asinh_scale_values,
            well_size,
            vmin_input,
            vmax_input,
        ):
            show_grid = "show" in (show_grid_values or [])
            show_connections = has_connections and "show" in (show_connection_values or [])
            show_contours = has_contours and "show" in (show_contours_values or [])
            show_wells = has_wells and "show" in (show_wells_values or [])

            show_grid_options = show_grid and "show" in (grid_options_values or [])
            show_connection_options = (
                show_connections and "show" in (connection_options_values or [])
            )
            show_contour_options = (
                show_contours and "show" in (contour_options_values or [])
            )
            show_well_options = show_wells and "show" in (well_options_values or [])

            grid_style = {"display": "block" if show_grid_options else "none"}
            connection_style = {
                "display": "block" if show_connection_options else "none"
            }
            contour_style = {"display": "block" if show_contour_options else "none"}
            well_style = {"display": "block" if show_well_options else "none"}

            grid_log_scale = show_grid and "on" in (grid_log_scale_values or [])
            grid_asinh_scale = (
                show_grid and "on" in (grid_asinh_scale_values or []) and not grid_log_scale
            )
            connection_log_scale = (
                show_connections and "on" in (connection_log_scale_values or [])
            )
            connection_asinh_scale = (
                show_connections
                and "on" in (connection_asinh_scale_values or [])
                and not connection_log_scale
            )

            grid_log_options = [
                {
                    "label": "Log",
                    "value": "on",
                    "disabled": (not show_grid) or grid_asinh_scale,
                }
            ]
            grid_asinh_options = [
                {
                    "label": "Asinh",
                    "value": "on",
                    "disabled": (not show_grid) or grid_log_scale,
                }
            ]
            connection_log_options = [
                {
                    "label": "Log",
                    "value": "on",
                    "disabled": (
                        (not has_connections)
                        or (not show_connections)
                        or connection_asinh_scale
                    ),
                }
            ]
            connection_asinh_options = [
                {
                    "label": "Asinh",
                    "value": "on",
                    "disabled": (
                        (not has_connections)
                        or (not show_connections)
                        or connection_log_scale
                    ),
                }
            ]
            grid_options = [
                {"label": "Options", "value": "show", "disabled": not show_grid}
            ]
            connection_options = [
                {
                    "label": "Options",
                    "value": "show",
                    "disabled": (not has_connections) or (not show_connections),
                }
            ]
            contour_options = [
                {
                    "label": "Options",
                    "value": "show",
                    "disabled": (not has_contours) or (not show_contours),
                }
            ]
            well_options = [
                {
                    "label": "Options",
                    "value": "show",
                    "disabled": (not has_wells) or (not show_wells),
                }
            ]

            prop_data = map_plot.grid_data[int(property_index), :, :]
            if grid_log_scale:
                pos = prop_data[np.isfinite(prop_data) & (prop_data > 0)]
                _auto_vmin = float(np.nanmin(pos)) if pos.size > 0 else None
                _auto_vmax = float(np.nanmax(pos)) if pos.size > 0 else None
            else:
                fin = prop_data[np.isfinite(prop_data)]
                _auto_vmin = float(np.nanmin(fin)) if fin.size > 0 else None
                _auto_vmax = float(np.nanmax(fin)) if fin.size > 0 else None

            scale_mode = "log" if grid_log_scale else "asinh" if grid_asinh_scale else "linear"

            color_limits, color_error = _parse_color_limits(
                vmin_input,
                vmax_input,
                scale_mode,
                auto_vmin=_auto_vmin, auto_vmax=_auto_vmax,
            )

            fig = map_plot.create_map_figure(
                property_index=int(property_index),
                day_index=int(day_index),
                layer=int(layer),
                palette=str(grid_palette),
                grid_log_scale=grid_log_scale,
                grid_asinh_scale=grid_asinh_scale,
                color_limits=color_limits,
                add_grid=show_grid,
                add_connections=show_connections,
                add_contours=show_contours,
                add_wells=show_wells,
                contour_count=int(contour_count),
                connection_palette=str(connection_palette),
                connection_log_scale=connection_log_scale,
                connection_asinh_scale=connection_asinh_scale,
                connection_width=float(connection_width),
                connection_line_segments=int(connection_segments),
                well_size_percent=float(well_size),
            )
            fig.update_layout(autosize=True, width=None, height=None)
            return (
                fig,
                grid_style,
                connection_style,
                contour_style,
                well_style,
                grid_log_options,
                grid_asinh_options,
                connection_log_options,
                connection_asinh_options,
                grid_options,
                connection_options,
                contour_options,
                well_options,
                color_error,
            )

    def _register_map_compare_callbacks(self, app, prefix, map_compare):
        """Register callbacks for DashMapCompare in multi-panel context."""
        map_a = map_compare.map_plot_a
        map_b = map_compare.map_plot_b
        n_layers = len(map_a.layer_sizes)
        has_contours = map_a.has_contours() or map_b.has_contours()
        has_wells = map_a.has_wells() or map_b.has_wells()

        @app.callback(
            Output(f"{prefix}-graph-a", "figure"),
            Output(f"{prefix}-graph-b", "figure"),
            Output(f"{prefix}-grid-controls-group", "style"),
            Output(f"{prefix}-well-controls-group", "style"),
            Output(f"{prefix}-contour-controls-group", "style"),
            Output(f"{prefix}-color-error", "children"),
            Output(f"{prefix}-grid-log", "options"),
            Output(f"{prefix}-grid-asinh", "options"),
            Input(f"{prefix}-property", "value"),
            Input(f"{prefix}-day", "value"),
            Input(f"{prefix}-layer", "value"),
            Input(f"{prefix}-show-grid", "value"),
            Input(f"{prefix}-grid-log", "value"),
            Input(f"{prefix}-grid-asinh", "value"),
            Input(f"{prefix}-grid-options", "value"),
            Input(f"{prefix}-palette", "value"),
            Input(f"{prefix}-vmin", "value"),
            Input(f"{prefix}-vmax", "value"),
            Input(f"{prefix}-show-wells", "value"),
            Input(f"{prefix}-well-options-toggle", "value"),
            Input(f"{prefix}-well-size", "value"),
            Input(f"{prefix}-show-contours", "value"),
            Input(f"{prefix}-contour-options", "value"),
            Input(f"{prefix}-contour-count", "value"),
        )
        def _update_compare(
            property_index, day_index, layer,
            show_grid_values, grid_log_values, grid_asinh_values, grid_options_values, palette,
            vmin_input, vmax_input,
            show_wells_values, well_options_values, well_size,
            show_contours_values, contour_options_values,
            contour_count,
        ):
            show_grid = "show" in (show_grid_values or [])
            grid_log = show_grid and "on" in (grid_log_values or [])
            grid_asinh = show_grid and "on" in (grid_asinh_values or []) and not grid_log
            show_grid_options = show_grid and "show" in (grid_options_values or [])
            show_wells_flag = has_wells and "show" in (show_wells_values or [])
            show_well_options = show_wells_flag and "show" in (well_options_values or [])
            show_contours = has_contours and "show" in (show_contours_values or [])
            show_contour_options = show_contours and "show" in (contour_options_values or [])

            grid_style = {"display": "block" if show_grid_options else "none"}
            well_style = {"display": "block" if show_well_options else "none"}
            contour_style = {"display": "block" if show_contour_options else "none"}
            grid_log_options = [{
                "label": "Log",
                "value": "on",
                "disabled": (not show_grid) or grid_asinh,
            }]
            grid_asinh_options = [{
                "label": "Asinh",
                "value": "on",
                "disabled": (not show_grid) or grid_log,
            }]

            synced = map_compare._compute_synced_limits(int(property_index), grid_log)
            scale_mode = "log" if grid_log else "asinh" if grid_asinh else "linear"
            color_limits, color_error = _parse_color_limits(
                vmin_input,
                vmax_input,
                scale_mode,
                auto_vmin=synced[0], auto_vmax=synced[1],
            )
            if color_limits is None and not color_error:
                color_limits = synced

            show_wells_a = show_wells_flag and map_a.has_wells()
            show_wells_b = show_wells_flag and map_b.has_wells()
            show_contours_a = show_contours and map_a.has_contours()
            show_contours_b = show_contours and map_b.has_contours()

            fig_a = map_a.create_map_figure(
                property_index=int(property_index),
                day_index=int(day_index),
                layer=int(layer),
                palette=str(palette),
                grid_log_scale=grid_log,
                grid_asinh_scale=grid_asinh,
                color_limits=color_limits,
                add_grid=show_grid,
                add_connections=False,
                add_contours=show_contours_a,
                add_wells=show_wells_a,
                well_size_percent=float(well_size) if well_size else 20.0,
                contour_count=int(contour_count),
            )
            fig_b = map_b.create_map_figure(
                property_index=int(property_index),
                day_index=int(day_index),
                layer=int(layer),
                palette=str(palette),
                grid_log_scale=grid_log,
                grid_asinh_scale=grid_asinh,
                color_limits=color_limits,
                add_grid=show_grid,
                add_connections=False,
                add_contours=show_contours_b,
                add_wells=show_wells_b,
                well_size_percent=float(well_size) if well_size else 20.0,
                contour_count=int(contour_count),
            )
            for fig in (fig_a, fig_b):
                fig.update_layout(autosize=True, width=None, height=None)

            return (
                fig_a, fig_b,
                grid_style, well_style, contour_style,
                color_error,
                grid_log_options,
                grid_asinh_options,
            )

    def _register_line_callbacks(self, app):
        for idx, line_plot in enumerate(self.line_plots.values()):
            prefix = f"mp-line-{idx}"

            self._register_line_callback_factory(app=app, prefix=prefix, line_plot=line_plot)

    def _register_line_callback_factory(self, app, prefix, line_plot):

        @app.callback(
            Output(f"{prefix}-graph", "figure"),
            Input(f"{prefix}-log-y", "value"),
            Input(f"{prefix}-log-y2", "value"),
        )
        def _update_line(log_y_values, log_y2_values, _plot=line_plot):
            fig = _plot.create_line_figure(
                log_scale="on" in (log_y_values or []),
                log_scale_secondary="on" in (log_y2_values or []),
                marker_mode=True,
            )
            fig.update_layout(autosize=True, width=None, height=None)
            return fig

    def _register_scatter_callbacks(self, app):
        for idx, scatter_plot in enumerate(self.scatter_plots.values()):
            prefix = f"mp-scatter-{idx}"

            self._register_scatter_callback_factory(
                app=app,
                prefix=prefix,
                scatter_plot=scatter_plot,
            )

    def _register_scatter_callback_factory(self, app, prefix, scatter_plot):

        @app.callback(
            Output(f"{prefix}-graph", "figure"),
            Input(f"{prefix}-property", "value"),
            Input(f"{prefix}-log-x", "value"),
            Input(f"{prefix}-log-y", "value"),
            Input(f"{prefix}-xy-line", "value"),
            Input(f"{prefix}-equal-axes", "value"),
        )
        def _update_scatter(
            property_name,
            log_x_values,
            log_y_values,
            xy_line_values,
            equal_axes_values,
            _plot=scatter_plot,
        ):
            selected_property = property_name if property_name else []
            fig = _plot.create_scatter_figure(
                property_name=selected_property,
                log_x="on" in (log_x_values or []),
                log_y="on" in (log_y_values or []),
                show_xy_line="on" in (xy_line_values or []),
                equal_axes="on" in (equal_axes_values or []),
            )
            fig.update_layout(autosize=True, width=None, height=None)
            return fig

    def _register_table_callbacks(self, app):
        for idx, table_plot in enumerate(self.table_plots.values()):
            prefix = f"mp-table-{idx}"

            self._register_table_callback_factory(
                app=app, prefix=prefix, table_plot=table_plot, idx=idx)

    def _register_table_callback_factory(self, app, prefix, table_plot, idx):
        @app.callback(
            Output(f"{prefix}-table", "page_size"),
            Input(f"{prefix}-page-size", "value"),
        )
        def _update_table_page_size(page_size):
            return int(page_size)

        @app.callback(
            Output(f"{prefix}-download", "data"),
            Input(f"{prefix}-download-btn", "n_clicks"),
            prevent_initial_call=True,
        )
        def _download_table_csv(n_clicks, _plot=table_plot, _idx=idx):
            if not n_clicks:
                return no_update
            return dcc.send_data_frame(
                _plot.table_data.to_csv,
                f"table_panel_{_idx+1}.csv",
                index=False,
            )

    def create_app(self):
        """Create a Dash app with nested tabs and automatic callbacks."""
        app = Dash(__name__)
        app.layout = self.create_layout()
        self._register_map_callbacks(app)
        self._register_line_callbacks(app)
        self._register_scatter_callbacks(app)
        self._register_table_callbacks(app)
        return app


class DashMapCompare:
    """Synchronized dual-map comparison view for two DashMapPlot objects.

    Both maps are controlled by a single shared control panel. Axes are
    kept in sync when the user pans or zooms either map. Color limits are
    automatically derived from the combined data range so both maps use
    the same colour scale.

    Parameters
    ----------
    map_plot_a, map_plot_b : DashMapPlot
        The two maps to compare. Both must have the same
        (n_properties, n_days, n_layers).
    label_a, label_b : str
        Labels shown above each map.
    layout : {"side_by_side", "stacked"}
        Initial orientation of the two map panels (can be toggled in-app).
    title : str
        Title displayed at the top of the app.
    """

    def __init__(
        self,
        map_plot_a,
        map_plot_b,
        label_a="Map A",
        label_b="Map B",
        layout="side_by_side",
        title="Map Comparison",
    ):
        if not isinstance(map_plot_a, DashMapPlot) or not isinstance(map_plot_b, DashMapPlot):
            raise ValueError(
                "map_plot_a and map_plot_b must both be DashMapPlot instances."
            )
        a = map_plot_a.grid_data
        b = map_plot_b.grid_data
        n_layers_a = len(map_plot_a.layer_sizes)
        n_layers_b = len(map_plot_b.layer_sizes)
        if a.shape[0] != b.shape[0] or a.shape[1] != b.shape[1] or n_layers_a != n_layers_b:
            raise ValueError(
                "Both maps must have the same (n_properties, n_days, n_layers). "
                f"Map A: shape={a.shape[:2]}, layers={n_layers_a}. "
                f"Map B: shape={b.shape[:2]}, layers={n_layers_b}."
            )
        if layout not in ("side_by_side", "stacked"):
            raise ValueError("layout must be 'side_by_side' or 'stacked'.")

        self.map_plot_a = map_plot_a
        self.map_plot_b = map_plot_b
        self.label_a = str(label_a)
        self.label_b = str(label_b)
        self.layout = layout
        self.title = str(title)

    def _compute_synced_limits(self, property_index, log_scale):
        """Return [vmin, vmax] in original data space covering both maps."""
        prop_a = self.map_plot_a.grid_data[int(property_index), :, :]
        prop_b = self.map_plot_b.grid_data[int(property_index), :, :]
        if log_scale:
            pos_a = prop_a[np.isfinite(prop_a) & (prop_a > 0)]
            pos_b = prop_b[np.isfinite(prop_b) & (prop_b > 0)]
            combined = np.concatenate([pos_a, pos_b]) if (pos_a.size + pos_b.size) > 0 else None
        else:
            fin_a = prop_a[np.isfinite(prop_a)]
            fin_b = prop_b[np.isfinite(prop_b)]
            combined = np.concatenate([fin_a, fin_b]) if (fin_a.size + fin_b.size) > 0 else None

        if combined is None or combined.size == 0:
            return [0.0, 1.0]
        vmin = float(np.nanmin(combined))
        vmax = float(np.nanmax(combined))
        if np.isclose(vmin, vmax):
            vmax = vmin + 1.0
        return [vmin, vmax]

    def create_app(self, prefix="cmp"):
        """Create a Dash app with synchronized dual-map view.

        Parameters
        ----------
        prefix : str
            HTML element ID prefix; change this when embedding multiple
            compare views in the same Dash app.
        """
        map_a = self.map_plot_a
        map_b = self.map_plot_b
        n_properties, n_days, _ = map_a.grid_data.shape
        n_layers = len(map_a.layer_sizes)
        has_contours = map_a.has_contours() or map_b.has_contours()
        has_wells = map_a.has_wells() or map_b.has_wells()

        init_limits = self._compute_synced_limits(0, log_scale=False)
        init_fig_a = map_a.create_map_figure(
            property_index=0, day_index=0, layer=1,
            add_grid=True, add_connections=False,
            add_contours=False, add_wells=False,
            color_limits=init_limits,
        )
        init_fig_b = map_b.create_map_figure(
            property_index=0, day_index=0, layer=1,
            add_grid=True, add_connections=False,
            add_contours=False, add_wells=False,
            color_limits=init_limits,
        )
        for fig in (init_fig_a, init_fig_b):
            fig.update_layout(autosize=True, width=None, height=None)

        def _maps_container_style(layout_val):
            direction = "row" if layout_val == "side_by_side" else "column"
            return {
                "display": "flex",
                "flexDirection": direction,
                "flex": "1 1 auto",
                "minHeight": "0",
                "gap": "8px",
            }

        app = Dash(__name__)
        app.layout = html.Div(
            [
                html.H3(self.title, style={"margin": "0 0 8px 0"}),
                html.Div(
                    [
                        # ── Controls panel ──────────────────────────────
                        html.Div(
                            [
                                html.Label("Property"),
                                dcc.Dropdown(
                                    id=f"{prefix}-property",
                                    options=[
                                        {"label": map_a.property_names[i], "value": i}
                                        for i in range(n_properties)
                                    ],
                                    value=0,
                                    clearable=False,
                                ),
                                html.Br(),
                                html.Label("Layer"),
                                dcc.Slider(
                                    id=f"{prefix}-layer",
                                    min=1,
                                    max=max(1, n_layers),
                                    step=1,
                                    value=1,
                                    marks={1: "1", n_layers: str(n_layers)},
                                    tooltip=_SLIDER_TOOLTIP,
                                    disabled=n_layers == 1,
                                ),
                                html.Br(),
                                html.Label("Day"),
                                dcc.Slider(
                                    id=f"{prefix}-day",
                                    min=0,
                                    max=max(0, n_days - 1),
                                    step=1,
                                    value=0,
                                    marks={0: "0", max(0, n_days - 1): str(max(0, n_days - 1))},
                                    tooltip=_SLIDER_TOOLTIP,
                                ),
                                html.Hr(style={"margin": "12px 0"}),
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id=f"{prefix}-show-grid",
                                            options=[{"label": "Grid", "value": "show"}],
                                            value=["show"],
                                            style={"marginRight": "12px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-grid-log",
                                            options=[{"label": "Log", "value": "on"}],
                                            value=[],
                                            style={"marginRight": "12px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-grid-asinh",
                                            options=[{"label": "Asinh", "value": "on"}],
                                            value=[],
                                            style={"marginRight": "12px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-grid-options",
                                            options=[{"label": "Options", "value": "show"}],
                                            value=[],
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "columnGap": "8px",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Label("Grid palette"),
                                        dcc.Dropdown(
                                            id=f"{prefix}-palette",
                                            options=PALETTE_OPTIONS,
                                            value="Turbo",
                                            clearable=False,
                                        ),
                                        html.Div(
                                            [
                                                html.Label(
                                                    "Color limits",
                                                    style={"fontSize": "12px"},
                                                ),
                                                html.Div(
                                                    [
                                                        dcc.Input(
                                                            id=f"{prefix}-vmin",
                                                            type="number",
                                                            placeholder="Min (auto)",
                                                            debounce=True,
                                                            style=_INPUT_SMALL,
                                                        ),
                                                        html.Span(
                                                            "–",
                                                            style={"margin": "0 4px"},
                                                        ),
                                                        dcc.Input(
                                                            id=f"{prefix}-vmax",
                                                            type="number",
                                                            placeholder="Max (auto)",
                                                            debounce=True,
                                                            style=_INPUT_SMALL,
                                                        ),
                                                    ],
                                                    style=_COLOR_LIMITS_STYLE,
                                                ),
                                                html.Div(
                                                    id=f"{prefix}-color-error",
                                                    style=_COLOR_ERROR_STYLE,
                                                ),
                                            ],
                                            style={"marginTop": "8px"},
                                        ),
                                    ],
                                    id=f"{prefix}-grid-controls-group",
                                    style={"display": "none"},
                                ),
                                html.Hr(style={"margin": "12px 0"}),
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id=f"{prefix}-show-wells",
                                            options=[
                                                {
                                                    "label": "Wells",
                                                    "value": "show",
                                                    "disabled": not has_wells,
                                                }
                                            ],
                                            value=[],
                                            style={"marginRight": "12px"},
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                                html.Hr(style={"margin": "12px 0"}),
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id=f"{prefix}-show-contours",
                                            options=[
                                                {
                                                    "label": "Contours",
                                                    "value": "show",
                                                    "disabled": not has_contours,
                                                }
                                            ],
                                            value=[],
                                            style={"marginRight": "12px"},
                                        ),
                                        dcc.Checklist(
                                            id=f"{prefix}-contour-options",
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
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Contour count"),
                                        dcc.Slider(
                                            id=f"{prefix}-contour-count",
                                            min=2,
                                            max=15,
                                            step=1,
                                            value=7,
                                            disabled=not has_contours,
                                            tooltip=_SLIDER_TOOLTIP,
                                        ),
                                    ],
                                    id=f"{prefix}-contour-controls-group",
                                    style={"display": "none"},
                                ),
                                html.Hr(style={"margin": "12px 0"}),
                                html.Label("View layout"),
                                dcc.RadioItems(
                                    id=f"{prefix}-layout-toggle",
                                    options=[
                                        {"label": "Side by side", "value": "side_by_side"},
                                        {"label": "Stacked", "value": "stacked"},
                                    ],
                                    value=self.layout,
                                    style={"fontSize": "13px"},
                                ),
                            ],
                            style={
                                "flex": "0 0 280px",
                                "paddingRight": "12px",
                                "overflowY": "auto",
                            },
                        ),
                        # ── Two map graphs ───────────────────────────────
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label(
                                            self.label_a,
                                            style={"fontWeight": "600", "marginBottom": "4px"},
                                        ),
                                        dcc.Graph(
                                            id=f"{prefix}-graph-a",
                                            figure=init_fig_a,
                                            responsive=True,
                                            style={"flex": "1 1 auto", "minHeight": "0"},
                                            config={
                                                "displaylogo": False,
                                                "scrollZoom": True,
                                                "modeBarButtonsToRemove": [
                                                    "select2d",
                                                    "lasso2d",
                                                ],
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "flex": "1 1 auto",
                                        "minHeight": "0",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Label(
                                            self.label_b,
                                            style={"fontWeight": "600", "marginBottom": "4px"},
                                        ),
                                        dcc.Graph(
                                            id=f"{prefix}-graph-b",
                                            figure=init_fig_b,
                                            responsive=True,
                                            style={"flex": "1 1 auto", "minHeight": "0"},
                                            config={
                                                "displaylogo": False,
                                                "scrollZoom": True,
                                                "modeBarButtonsToRemove": [
                                                    "select2d",
                                                    "lasso2d",
                                                ],
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "flex": "1 1 auto",
                                        "minHeight": "0",
                                    },
                                ),
                            ],
                            id=f"{prefix}-maps-container",
                            style=_maps_container_style(self.layout),
                        ),
                    ],
                    style={
                        "display": "flex",
                        "height": "calc(100vh - 80px)",
                        "minHeight": "0",
                    },
                ),
            ],
            style={
                "padding": "12px",
                "boxSizing": "border-box",
                "height": "100vh",
                "overflow": "hidden",
            },
        )

        # ── Main figures callback ────────────────────────────────────────
        @app.callback(
            Output(f"{prefix}-graph-a", "figure"),
            Output(f"{prefix}-graph-b", "figure"),
            Output(f"{prefix}-grid-controls-group", "style"),
            Output(f"{prefix}-contour-controls-group", "style"),
            Output(f"{prefix}-color-error", "children"),
            Output(f"{prefix}-maps-container", "style"),
            Output(f"{prefix}-grid-log", "options"),
            Output(f"{prefix}-grid-asinh", "options"),
            Input(f"{prefix}-property", "value"),
            Input(f"{prefix}-day", "value"),
            Input(f"{prefix}-layer", "value"),
            Input(f"{prefix}-show-grid", "value"),
            Input(f"{prefix}-grid-log", "value"),
            Input(f"{prefix}-grid-asinh", "value"),
            Input(f"{prefix}-grid-options", "value"),
            Input(f"{prefix}-palette", "value"),
            Input(f"{prefix}-vmin", "value"),
            Input(f"{prefix}-vmax", "value"),
            Input(f"{prefix}-show-wells", "value"),
            Input(f"{prefix}-show-contours", "value"),
            Input(f"{prefix}-contour-options", "value"),
            Input(f"{prefix}-contour-count", "value"),
            Input(f"{prefix}-layout-toggle", "value"),
        )
        def _update_compare(
            property_index, day_index, layer,
            show_grid_values, grid_log_values, grid_asinh_values, grid_options_values, palette,
            vmin_input, vmax_input,
            show_wells_values, show_contours_values, contour_options_values,
            contour_count, layout_toggle,
        ):
            show_grid = "show" in (show_grid_values or [])
            grid_log = show_grid and "on" in (grid_log_values or [])
            grid_asinh = show_grid and "on" in (grid_asinh_values or []) and not grid_log
            show_grid_options = show_grid and "show" in (grid_options_values or [])
            show_contours = has_contours and "show" in (show_contours_values or [])
            show_wells_flag = has_wells and "show" in (show_wells_values or [])
            show_contour_options = show_contours and "show" in (contour_options_values or [])

            grid_style = {"display": "block" if show_grid_options else "none"}
            contour_style = {"display": "block" if show_contour_options else "none"}
            grid_log_options = [{
                "label": "Log",
                "value": "on",
                "disabled": (not show_grid) or grid_asinh,
            }]
            grid_asinh_options = [{
                "label": "Asinh",
                "value": "on",
                "disabled": (not show_grid) or grid_log,
            }]

            synced = self._compute_synced_limits(int(property_index), grid_log)
            scale_mode = "log" if grid_log else "asinh" if grid_asinh else "linear"
            color_limits, color_error = _parse_color_limits(
                vmin_input,
                vmax_input,
                scale_mode,
                auto_vmin=synced[0], auto_vmax=synced[1],
            )
            if color_limits is None and not color_error:
                color_limits = synced

            show_wells_a = show_wells_flag and map_a.has_wells()
            show_wells_b = show_wells_flag and map_b.has_wells()
            show_contours_a = show_contours and map_a.has_contours()
            show_contours_b = show_contours and map_b.has_contours()

            fig_a = map_a.create_map_figure(
                property_index=int(property_index),
                day_index=int(day_index),
                layer=int(layer),
                palette=str(palette),
                grid_log_scale=grid_log,
                grid_asinh_scale=grid_asinh,
                color_limits=color_limits,
                add_grid=show_grid,
                add_connections=False,
                add_contours=show_contours_a,
                add_wells=show_wells_a,
                contour_count=int(contour_count),
            )
            fig_b = map_b.create_map_figure(
                property_index=int(property_index),
                day_index=int(day_index),
                layer=int(layer),
                palette=str(palette),
                grid_log_scale=grid_log,
                grid_asinh_scale=grid_asinh,
                color_limits=color_limits,
                add_grid=show_grid,
                add_connections=False,
                add_contours=show_contours_b,
                add_wells=show_wells_b,
                contour_count=int(contour_count),
            )
            for fig in (fig_a, fig_b):
                fig.update_layout(autosize=True, width=None, height=None)

            return (
                fig_a, fig_b,
                grid_style, contour_style,
                color_error,
                _maps_container_style(layout_toggle),
                grid_log_options,
                grid_asinh_options,
            )

        # ── Axis sync callback ───────────────────────────────────────────
        @app.callback(
            Output(f"{prefix}-graph-a", "figure", allow_duplicate=True),
            Output(f"{prefix}-graph-b", "figure", allow_duplicate=True),
            Input(f"{prefix}-graph-a", "relayoutData"),
            Input(f"{prefix}-graph-b", "relayoutData"),
            prevent_initial_call=True,
        )
        def _sync_axes(relay_a, relay_b):
            trigger = ctx.triggered_id
            relay = relay_a if trigger == f"{prefix}-graph-a" else relay_b
            if not relay:
                return no_update, no_update

            patched = Patch()
            xr0 = relay.get("xaxis.range[0]")
            xr1 = relay.get("xaxis.range[1]")
            yr0 = relay.get("yaxis.range[0]")
            yr1 = relay.get("yaxis.range[1]")

            if relay.get("xaxis.autorange") or relay.get("autosize"):
                patched["layout"]["xaxis"]["autorange"] = True
            elif xr0 is not None and xr1 is not None:
                patched["layout"]["xaxis"]["range"] = [xr0, xr1]
                patched["layout"]["xaxis"]["autorange"] = False

            if relay.get("yaxis.autorange") or relay.get("autosize"):
                patched["layout"]["yaxis"]["autorange"] = True
            elif yr0 is not None and yr1 is not None:
                patched["layout"]["yaxis"]["range"] = [yr0, yr1]
                patched["layout"]["yaxis"]["autorange"] = False

            if trigger == f"{prefix}-graph-a":
                return no_update, patched
            return patched, no_update

        return app
