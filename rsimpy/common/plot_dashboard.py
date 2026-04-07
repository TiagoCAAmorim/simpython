"""Dashboard composition utilities for Dash-based plot components."""

from __future__ import annotations

from dash import Dash, Input, Output, ctx, dash_table, dcc, html, no_update

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
        self.map_plots = self._normalize_panel_dict(
            map_plots,
            expected_type=DashMapPlot,
            name="map_plots",
        )
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

    def _build_map_panel_tab(self, panel_name, map_plot, prefix):
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
                                    marks={i: str(i) for i in range(1, n_layers + 1)},
                                ),
                                html.Br(),
                                html.Label("Day"),
                                dcc.Slider(
                                    id=f"{prefix}-day",
                                    min=0,
                                    max=max(0, n_days - 1),
                                    step=1,
                                    value=0,
                                    marks={i: str(i) for i in range(n_days)},
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
        options = [{"label": "All", "value": "__all__"}] + [
            {"label": key, "value": key} for key in scatter_plot.scatter_data.keys()
        ]
        initial = scatter_plot.create_scatter_figure(property_name=None)
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
                                    value="__all__",
                                    clearable=False,
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
            has_connections = map_plot.has_connections()
            has_contours = map_plot.has_contours()
            has_wells = map_plot.has_wells()

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
                _prefix=prefix,
            ):
                trigger = ctx.triggered_id
                grid_value = [] if trigger == f"{_prefix}-show-grid" else no_update
                connection_value = (
                    [] if trigger == f"{_prefix}-show-connections" else no_update
                )
                contour_value = (
                    [] if trigger == f"{_prefix}-show-contours" else no_update
                )
                well_value = [] if trigger == f"{_prefix}-show-wells" else no_update
                return grid_value, connection_value, contour_value, well_value

            @app.callback(
                Output(f"{prefix}-graph", "figure"),
                Output(f"{prefix}-grid-controls-group", "style"),
                Output(f"{prefix}-connection-controls-group", "style"),
                Output(f"{prefix}-contour-controls-group", "style"),
                Output(f"{prefix}-well-controls-group", "style"),
                Output(f"{prefix}-grid-log-scale", "options"),
                Output(f"{prefix}-connection-log-scale", "options"),
                Output(f"{prefix}-grid-options-toggle", "options"),
                Output(f"{prefix}-connection-options-toggle", "options"),
                Output(f"{prefix}-contour-options-toggle", "options"),
                Output(f"{prefix}-well-options-toggle", "options"),
                Input(f"{prefix}-property", "value"),
                Input(f"{prefix}-day", "value"),
                Input(f"{prefix}-layer", "value"),
                Input(f"{prefix}-show-grid", "value"),
                Input(f"{prefix}-grid-palette", "value"),
                Input(f"{prefix}-grid-log-scale", "value"),
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
                Input(f"{prefix}-well-size", "value"),
            )
            def _update_map(
                property_index,
                day_index,
                layer,
                show_grid_values,
                grid_palette,
                grid_log_scale_values,
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
                well_size,
                _plot=map_plot,
                _has_connections=has_connections,
                _has_contours=has_contours,
                _has_wells=has_wells,
            ):
                show_grid = "show" in (show_grid_values or [])
                show_connections = (
                    _has_connections and "show" in (show_connection_values or [])
                )
                show_contours = _has_contours and "show" in (show_contours_values or [])
                show_wells = _has_wells and "show" in (show_wells_values or [])

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
                contour_style = {
                    "display": "block" if show_contour_options else "none"
                }
                well_style = {"display": "block" if show_well_options else "none"}

                grid_log_scale = show_grid and "on" in (grid_log_scale_values or [])
                connection_log_scale = (
                    show_connections and "on" in (connection_log_scale_values or [])
                )

                grid_log_options = [
                    {"label": "Log", "value": "on", "disabled": not show_grid}
                ]
                connection_log_options = [
                    {
                        "label": "Log",
                        "value": "on",
                        "disabled": (not _has_connections) or (not show_connections),
                    }
                ]
                grid_options = [
                    {
                        "label": "Options",
                        "value": "show",
                        "disabled": not show_grid,
                    }
                ]
                connection_options = [
                    {
                        "label": "Options",
                        "value": "show",
                        "disabled": (not _has_connections) or (not show_connections),
                    }
                ]
                contour_options = [
                    {
                        "label": "Options",
                        "value": "show",
                        "disabled": (not _has_contours) or (not show_contours),
                    }
                ]
                well_options = [
                    {
                        "label": "Options",
                        "value": "show",
                        "disabled": (not _has_wells) or (not show_wells),
                    }
                ]

                fig = _plot.create_map_figure(
                    property_index=int(property_index),
                    day_index=int(day_index),
                    layer=int(layer),
                    palette=str(grid_palette),
                    grid_log_scale=grid_log_scale,
                    add_grid=show_grid,
                    add_connections=show_connections,
                    add_contours=show_contours,
                    add_wells=show_wells,
                    contour_count=int(contour_count),
                    connection_palette=str(connection_palette),
                    connection_log_scale=connection_log_scale,
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
                    connection_log_options,
                    grid_options,
                    connection_options,
                    contour_options,
                    well_options,
                )

    def _register_line_callbacks(self, app):
        for idx, line_plot in enumerate(self.line_plots.values()):
            prefix = f"mp-line-{idx}"

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

            @app.callback(
                Output(f"{prefix}-graph", "figure"),
                Input(f"{prefix}-property", "value"),
                Input(f"{prefix}-log-x", "value"),
                Input(f"{prefix}-log-y", "value"),
            )
            def _update_scatter(
                property_name,
                log_x_values,
                log_y_values,
                _plot=scatter_plot,
            ):
                selected_property = None
                if property_name and property_name != "__all__":
                    selected_property = str(property_name)
                fig = _plot.create_scatter_figure(
                    property_name=selected_property,
                    log_x="on" in (log_x_values or []),
                    log_y="on" in (log_y_values or []),
                )
                fig.update_layout(autosize=True, width=None, height=None)
                return fig

    def _register_table_callbacks(self, app):
        for idx, table_plot in enumerate(self.table_plots.values()):
            prefix = f"mp-table-{idx}"

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
