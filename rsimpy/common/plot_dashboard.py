"""Dashboard composition utilities for Dash-based plot components."""

from __future__ import annotations

from dash import Dash, dash_table, dcc, html


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
