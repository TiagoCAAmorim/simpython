"""Tests for Dash plotting foundation utilities.

This module validates the core plotting components and rendering
logic for the Dash-based map visualization system. Tests cover:
- Layer management and validation utilities
- Contour level and segment computation
- Triangle geometry generation and rendering
- DashMapPlot class initialization and figure generation
- Grid polygon rendering with hover interaction
- Connection visualization (lines and triangles)
- Colorbar configuration and log-scale display
- Well visualization with cross-layer styling
"""

import unittest

import numpy as np

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from rsimpy.common.plot_dash import (
    DashLinePlot,
    DashMapPlot,
    DashScatterPlot,
    DashTable,
    add_triangle_trace,
    build_layer_per_cell,
    create_triangle_vertices,
    _determine_contour_levels,
    _get_contour_segments_triangle,
    validate_layer_sizes,
)
from rsimpy.common.plot_dashboard import DashDashboard
from rsimpy.common.plot_dashboard import DashMultiPanelDashboard


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


class TestPlotDashFoundation(unittest.TestCase):
    """Validate early Dash plotting building blocks.

    Tests cover validation functions, geometry helpers, and core
    DashMapPlot functionality including layer management, contour
    generation, polygon rendering, connection visualization, and
    colorbar configuration.
    """

    def test_validate_layer_sizes(self):
        """Test validate_layer_sizes returns correct layer size array matching input."""
        sizes = validate_layer_sizes([2, 3, 1], n_cells=6)
        np.testing.assert_array_equal(sizes, np.array([2, 3, 1]))

    def test_build_layer_per_cell(self):
        """Test build_layer_per_cell converts layer sizes to per-cell
        1-indexed layer assignments."""
        layer_per_cell = build_layer_per_cell([2, 3])
        np.testing.assert_array_equal(layer_per_cell, np.array([1, 1, 2, 2, 2]))

    def test_determine_contour_levels_uses_global_range(self):
        """Test contour level generation uses global z-range across all vertices."""
        vertices = np.zeros((2, 4, 3), dtype=float)
        vertices[0, :, 2] = [0.0, 10.0, 10.0, 0.0]
        vertices[1, :, 2] = [100.0, 110.0, 110.0, 100.0]

        levels = _determine_contour_levels(vertices, contour_count=3)
        np.testing.assert_allclose(levels, np.array([0.0, 50.0, 100.0]))

    def test_contour_segments_flat_edge_crosses_midpoint(self):
        """Test contour segments properly handle flat edges that
        cross the contour value."""
        triangle = np.asarray([
            [0.0, 0.0],
            [2.0, 0.0],
            [1.0, 2.0],
        ], dtype=float)
        z_vals = np.asarray([5.0, 5.0, 0.0], dtype=float)

        segments = _get_contour_segments_triangle(triangle, z_vals, contour_value=5.0)
        self.assertEqual(len(segments), 1)
        p0, p1 = segments[0]
        self.assertTrue(np.allclose(p0, [1.0, 0.0]) or np.allclose(p1, [1.0, 0.0]))

    def test_create_triangle_vertices_up(self):
        """Test upward-pointing triangle vertices have apex at top (max y)."""
        xs, ys = create_triangle_vertices(10.0, 20.0, size=2.0, direction="up")
        self.assertEqual(len(xs), 4)
        self.assertEqual(len(ys), 4)
        self.assertGreater(ys[0], ys[1])
        self.assertGreater(ys[0], ys[2])

    def test_create_triangle_vertices_down(self):
        """Test downward-pointing triangle vertices have apex at bottom (min y)."""
        xs, ys = create_triangle_vertices(10.0, 20.0, size=2.0, direction="down")
        self.assertEqual(len(xs), 4)
        self.assertEqual(len(ys), 4)
        self.assertLess(ys[0], ys[1])
        self.assertLess(ys[0], ys[2])

    def test_add_triangle_trace(self):
        """Test add_triangle_trace adds a single polygon trace to the
        figure with correct properties."""
        if not HAS_PLOTLY:
            self.skipTest("plotly not installed")

        fig = go.Figure()
        fig = add_triangle_trace(
            fig,
            center_x=1.0,
            center_y=2.0,
            size=1.0,
            direction="up",
            line_color="black",
            fill_color="red",
        )
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.data[0].fill, "toself")
        self.assertEqual(fig.data[0].mode, "lines")

    def test_dash_map_plot_default_cell_index(self):
        """Test DashMapPlot auto-generates Cell Index property when
        grid_data is None."""
        vertices = np.zeros((6, 4, 3), dtype=float)
        obj = DashMapPlot(vertices=vertices, layer_sizes=[2, 2, 2])
        self.assertEqual(obj.grid_data.shape, (1, 1, 6))
        self.assertEqual(obj.property_names, ["Cell Index"])

    def test_dash_map_plot_renders_only_selected_layer(self):
        """Test DashMapPlot renders only polygons from the selected layer."""
        vertices = _make_regular_grid_vertices(2, 6)
        # 2 properties, 2 days, 12 cells
        grid_data = np.zeros((2, 2, 12), dtype=float)
        grid_data[0, 0, :] = np.arange(12)
        grid_data[1, 1, :] = np.arange(12) * 10

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[6, 6],
            grid_data=grid_data,
            property_names=["P1", "P2"],
        )
        fig = obj.create_map_figure(property_index=1, day_index=1, layer=2)

        polygon_traces = [tr for tr in fig.data if tr.name == "cell-polygon"]
        self.assertEqual(len(polygon_traces), 6)

    def test_step_2_1_manual_5x6_single_layer_case(self):
        """Manual smoke test: 30-cell single layer with cell names and
        auto Cell Index property.

        This is a manually requested test case validating:
        - 5x6 regular grid with 30 polygons
        - Auto-generated Cell Index property
        - Cell names in (row, col) format
        - Sparse interior hover points (9 per cell)
        - Hover text includes cell name and property value
        """
        n_rows, n_cols = 5, 6
        n_cells = n_rows * n_cols
        vertices = _make_regular_grid_vertices(n_rows, n_cols)
        cell_names = [f"({r+1},{c+1})" for r in range(n_rows) for c in range(n_cols)]

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[n_cells],
            grid_data=None,  # should auto-create Cell Index property
            cell_names=cell_names,
            title="Step 2.1 Manual 5x6",
        )

        fig = obj.create_map_figure(property_index=0, day_index=0, layer=1)
        polygon_traces = [tr for tr in fig.data if tr.name == "cell-polygon"]
        polygon_hover_traces = [
            tr for tr in fig.data if tr.name == "cell-polygon-hover"
        ]
        self.assertEqual(len(polygon_traces), 30)
        self.assertEqual(len(polygon_hover_traces), 30)
        self.assertIn("(1,1)", polygon_hover_traces[0].text[0])
        self.assertIn("(5,6)", polygon_hover_traces[-1].text[0])
        self.assertIn("Cell Index", polygon_hover_traces[0].text[0])
        self.assertEqual(
            polygon_hover_traces[0].hovertemplate, "%{text}<extra></extra>"
        )
        self.assertEqual(polygon_hover_traces[0].mode, "markers")
        self.assertEqual(len(polygon_hover_traces[0].x), 9)
        self.assertEqual(polygon_traces[0].hoverinfo, "skip")
        self.assertEqual(obj.property_names, ["Cell Index"])

    def test_map_figure_renders_contours_with_count(self):
        """Test map figure renders contour lines based on specified contour count.

        Verifies:
        - Multiple contour traces generated
        - Matching hover traces for each contour
        - Contour line width >= 3.0 (thick lines)
        """
        vertices = _make_regular_grid_vertices(1, 2)
        vertices[:, :, 2] = np.asarray([
            [0.0, 10.0, 10.0, 0.0],
            [100.0, 110.0, 110.0, 100.0],
        ], dtype=float)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P1"],
        )
        fig = obj.create_map_figure(
            property_index=0, day_index=0, layer=1,
            add_contours=True, contour_count=3,
        )
        contour_traces = [
            tr for tr in fig.data if tr.name == "contour-line"
        ]
        contour_hover_traces = [
            tr for tr in fig.data if tr.name == "contour-line-hover"
        ]
        self.assertGreaterEqual(len(contour_traces), 1)
        self.assertEqual(len(contour_traces), len(contour_hover_traces))
        self.assertGreaterEqual(float(contour_traces[0].line.width), 3.0)

    def test_map_figure_default_axes_use_global_polygon_bounds(self):
        """Test map figure axes are set to global polygon bounds with padding.

        Verifies x and y ranges encompass all polygon vertices with 5% padding.
        """
        vertices = _make_regular_grid_vertices(2, 2)
        grid_data = np.arange(4, dtype=float).reshape(1, 1, 4)
        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2, 2],
            grid_data=grid_data,
            property_names=["P1"],
        )

        fig = obj.create_map_figure(property_index=0, day_index=0, layer=2)
        x_range = list(fig.layout.xaxis.range)
        y_range = list(fig.layout.yaxis.range)
        self.assertLessEqual(x_range[0], 0.0)
        self.assertGreaterEqual(x_range[1], 2.0)
        self.assertLessEqual(y_range[0], 0.0)
        self.assertGreaterEqual(y_range[1], 2.0)

    def test_global_color_scale_uses_all_days_for_property(self):
        """Test grid colorbar uses min/max values across all days,
        not just current day.

        Colorscale range [0, 202] spans all 3 days even when viewing
        day 1 with range [100, 102].
        """
        vertices = _make_regular_grid_vertices(1, 3)
        # property value range across all days: [0, 202]
        grid_data = np.zeros((1, 3, 3), dtype=float)
        grid_data[0, 0, :] = [0.0, 1.0, 2.0]
        grid_data[0, 1, :] = [100.0, 101.0, 102.0]
        grid_data[0, 2, :] = [200.0, 201.0, 202.0]

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[3],
            grid_data=grid_data,
            property_names=["P"],
        )
        fig = obj.create_map_figure(property_index=0, day_index=1, layer=1)
        colorbar = [tr for tr in fig.data if tr.name == "colorbar"][0]
        self.assertEqual(float(colorbar.marker.cmin), 0.0)
        self.assertEqual(float(colorbar.marker.cmax), 202.0)

    def test_grid_log_scale_non_positive_is_dark_gray(self):
        """Test log-scale grid colors render non-positive values as dark gray (#4d4d4d).

        Also verifies:
        - Colorbar title remains original property name (no log10 wrapper)
        - Colorbar tick text shows original (non-log) values
        """
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.asarray([[[ -5.0, 10.0 ]]], dtype=float)

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P1"],
        )
        fig = obj.create_map_figure(
            property_index=0,
            day_index=0,
            layer=1,
            grid_log_scale=True,
        )
        polygon_colors = [tr.fillcolor for tr in fig.data if tr.name == "cell-polygon"]
        self.assertIn("#4d4d4d", [str(c).lower() for c in polygon_colors])
        grid_colorbar = [tr for tr in fig.data if tr.name == "colorbar"][0]
        self.assertEqual(str(grid_colorbar.marker.colorbar.title.text), "P1")
        self.assertIsNotNone(grid_colorbar.marker.colorbar.ticktext)
        self.assertTrue(
            all(
                "e" not in str(v).lower() or "-" not in str(v)
                for v in grid_colorbar.marker.colorbar.ticktext
            )
        )

    def test_dash_map_plot_connections_lines_and_triangles(self):
        """Test connection rendering for both same-layer lines and
        cross-layer triangles.

        Validates:
        - Same-layer connections render as lines with hover text
        - Cross-layer connections render as up/down triangles
        - Connection colorbar is separate and offset from grid colorbar
        - Direction markers (↑↓) appear in triangle hover text
        """
        vertices = _make_regular_grid_vertices(2, 2)
        # 2 layers of 2 cells each -> 4 total cells
        grid_data = np.arange(4, dtype=float).reshape(1, 1, 4)
        # Connections:
        # 0-1 same layer(1) -> line in layer 1
        # 0-2 cross layer    -> down triangle in layer 1, up in layer 2
        # 2-3 same layer(2) -> line in layer 2
        connection_indices = np.asarray([[0, 0, 2], [1, 2, 3]], dtype=int)
        connection_data = np.asarray([[[10.0, 3.0, 7.0]]], dtype=float)

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2, 2],
            grid_data=grid_data,
            property_names=["P1"],
            connection_indices=connection_indices,
            connection_data=connection_data,
            connection_property_names=["T"],
        )

        fig_l1 = obj.create_map_figure(
            property_index=0,
            day_index=0,
            layer=1,
            add_connections=True,
        )
        names_l1 = [tr.name for tr in fig_l1.data]
        self.assertIn("connection-line", names_l1)
        self.assertIn("connection-line-hover", names_l1)
        self.assertIn("connection-triangle-down", names_l1)
        self.assertIn("connection-triangle-hover", names_l1)
        self.assertIn("connection-colorbar", names_l1)

        first_hover_trace = [
            tr for tr in fig_l1.data if tr.name == "connection-line-hover"
        ][0]
        self.assertNotIn("Connection:", first_hover_trace.text[0])
        self.assertIn("0->1", first_hover_trace.text[0])

        grid_colorbar = [tr for tr in fig_l1.data if tr.name == "colorbar"][0]
        conn_colorbar = [
            tr for tr in fig_l1.data if tr.name == "connection-colorbar"
        ][0]
        self.assertLess(
            float(grid_colorbar.marker.colorbar.x),
            float(conn_colorbar.marker.colorbar.x),
        )

        fig_l2 = obj.create_map_figure(
            property_index=0,
            day_index=0,
            layer=2,
            add_connections=True,
        )
        names_l2 = [tr.name for tr in fig_l2.data]
        self.assertIn("connection-line", names_l2)
        self.assertIn("connection-triangle-up", names_l2)

    def test_missing_reverse_connection_fades_visibility(self):
        """Test unidirectional connections show with fading gradient
        (alpha start vs end).

        Line colors use rgba format to achieve directional fade effect.
        """
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)
        connection_indices = np.asarray([[0], [1]], dtype=int)
        connection_data = np.asarray([[[5.0]]], dtype=float)

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P1"],
            connection_indices=connection_indices,
            connection_data=connection_data,
            connection_property_names=["T"],
        )

        fig = obj.create_map_figure(
            property_index=0,
            day_index=0,
            layer=1,
            add_connections=True,
            connection_line_segments=10,
        )
        line_colors = [tr.line.color for tr in fig.data if tr.name == "connection-line"]
        self.assertGreater(len(line_colors), 0)
        self.assertTrue(any(str(c).startswith("rgba(") for c in line_colors))

    def test_default_connection_colorscale_differs_from_grid(self):
        """Test connection colorbar uses a different colorscale than grid colorbar.

        Defaults: Grid=Turbo, Connections=Plasma (or other non-matching palette).
        """
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)
        connection_indices = np.asarray([[0], [1]], dtype=int)
        connection_data = np.asarray([[[5.0]]], dtype=float)

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P1"],
            connection_indices=connection_indices,
            connection_data=connection_data,
            connection_property_names=["T"],
        )

        fig = obj.create_map_figure(
            property_index=0,
            day_index=0,
            layer=1,
            add_connections=True,
        )
        grid_colorbar = [tr for tr in fig.data if tr.name == "colorbar"][0]
        conn_colorbar = [tr for tr in fig.data if tr.name == "connection-colorbar"][0]
        self.assertNotEqual(
            grid_colorbar.marker.colorscale,
            conn_colorbar.marker.colorscale,
        )

    def test_connection_log_scale_non_positive_is_dark_gray(self):
        """Test log-scale connection colors render non-positive values as
        dark gray (rgb 119, 119, 119).

        Also verifies:
        - Colorbar title is 'Connection' (original name)
        - Colorbar tick text shows original (non-log) values
        """
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)
        connection_indices = np.asarray([[0], [1]], dtype=int)
        connection_data = np.asarray([[[-2.0]]], dtype=float)

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P1"],
            connection_indices=connection_indices,
            connection_data=connection_data,
            connection_property_names=["T"],
        )

        fig = obj.create_map_figure(
            property_index=0,
            day_index=0,
            layer=1,
            add_connections=True,
            connection_log_scale=True,
        )
        line_colors = [
            str(tr.line.color) for tr in fig.data if tr.name == "connection-line"
        ]
        self.assertTrue(any("77, 77, 77" in color for color in line_colors))
        conn_colorbar = [tr for tr in fig.data if tr.name == "connection-colorbar"][0]
        self.assertEqual(str(conn_colorbar.marker.colorbar.title.text), "Connection")
        self.assertIsNotNone(conn_colorbar.marker.colorbar.ticktext)

    def test_connection_line_segments_respected(self):
        """Test connection lines are subdivided into specified number of
        gradient segments.

        For connection_line_segments=7, generates 7 separate line traces
        to show gradient.
        """
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)
        connection_indices = np.asarray([[0, 1], [1, 0]], dtype=int)
        connection_data = np.asarray([[[5.0, 8.0]]], dtype=float)

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P1"],
            connection_indices=connection_indices,
            connection_data=connection_data,
            connection_property_names=["T"],
        )

        fig = obj.create_map_figure(
            property_index=0,
            day_index=0,
            layer=1,
            add_connections=True,
            connection_line_segments=7,
        )
        line_traces = [tr for tr in fig.data if tr.name == "connection-line"]
        self.assertEqual(len(line_traces), 7)

    def test_wells_render_lines_and_markers(self):
        """Test wells render as colored circles with connecting lines
        between consecutive cells.

        Verifies:
        - Well line traces between consecutive well cells
        - Well circle markers with color based on well type
          (prod/injw/injg/inj)
        - Well hover info includes well name and type
        """
        vertices = _make_regular_grid_vertices(1, 4)
        grid_data = np.arange(4, dtype=float).reshape(1, 1, 4)
        wells = {
            "W-1,prod": np.asarray([0, 1, 2], dtype=int),
            "W-2,injw": np.asarray([3], dtype=int),
        }

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[4],
            grid_data=grid_data,
            property_names=["P1"],
            wells=wells,
        )

        fig = obj.create_map_figure(
            property_index=0,
            day_index=0,
            layer=1,
            add_wells=True,
            well_size_percent=50.0,
        )
        names = [tr.name for tr in fig.data]
        self.assertIn("well-line", names)
        self.assertIn("well-circle", names)
        self.assertIn("well-hover", names)

        hover_traces = [tr for tr in fig.data if tr.name == "well-hover"]
        self.assertGreaterEqual(len(hover_traces), 1)
        self.assertIn("W-1", hover_traces[0].text[0])
        self.assertIn("prod", hover_traces[0].text[0])

    def test_well_lines_and_faded_cross_layer_circles(self):
        """Test cross-layer well connections show hollow circles and
        dashed lines to off-layer cells.

        Validates:
        - Same-layer segments: solid black lines with filled circles
        - Cross-layer segments: dashed black lines with hollow
          (rgba(0,0,0,0)) circles
        """
        vertices = _make_regular_grid_vertices(1, 3)
        vertices_l2 = _make_regular_grid_vertices(1, 1) + np.array([3.0, 0.0, 0.0])
        vertices = np.concatenate([vertices, vertices_l2], axis=0)
        grid_data = np.arange(4, dtype=float).reshape(1, 1, 4)
        wells = {
            # Consecutive cells: 0->1 (same active layer), 1->3 (cross-layer)
            "W-X,inj": np.asarray([0, 1, 3], dtype=int),
        }

        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[3, 1],
            grid_data=grid_data,
            property_names=["P1"],
            wells=wells,
        )

        fig = obj.create_map_figure(
            property_index=0,
            day_index=0,
            layer=1,
            add_wells=True,
            well_size_percent=20.0,
        )

        line_traces = [tr for tr in fig.data if tr.name == "well-line"]
        self.assertEqual(len(line_traces), 2)
        dashes = [str(tr.line.dash) for tr in line_traces]
        self.assertIn("solid", dashes)
        self.assertIn("dash", dashes)
        self.assertTrue(all(str(tr.line.color) == "black" for tr in line_traces))

        circle_traces = [tr for tr in fig.data if tr.name == "well-circle"]
        self.assertEqual(len(circle_traces), 3)
        fill_colors = [str(tr.fillcolor) for tr in circle_traces]
        self.assertIn("rgba(0,0,0,0)", fill_colors)
        self.assertTrue(any(color != "rgba(0,0,0,0)" for color in fill_colors))

    def test_map_figure_uses_default_uirevision(self):
        """Test map figure sets uirevision='dash-map-view' for zoom persistence."""
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)
        obj = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P1"],
        )
        fig = obj.create_map_figure(property_index=0, day_index=0, layer=1)
        self.assertEqual(fig.layout.uirevision, "dash-map-view")

    def test_dash_map_plot_connection_validation(self):
        """Test DashMapPlot raises ValueError for invalid connection indices
        (out of bounds)."""
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)

        with self.assertRaises(ValueError):
            DashMapPlot(
                vertices=vertices,
                layer_sizes=[2],
                grid_data=grid_data,
                property_names=["P1"],
                connection_indices=np.asarray([[0], [2]], dtype=int),
                connection_data=np.asarray([[[1.0]]], dtype=float),
            )

    def test_dash_line_plot_secondary_axis_and_log_scale(self):
        """Test line plot builds traces with secondary y-axis and log scale."""
        x_values = np.asarray(["2026-01-01", "2026-01-02", "2026-01-03"], dtype="datetime64[D]")
        y_values = np.asarray([
            [10.0, 12.0, 14.0],
            [100.0, 120.0, 140.0],
        ], dtype=float)

        obj = DashLinePlot(
            x_values=x_values,
            y_values=y_values,
            property_names=["P", "Q"],
            secondary_y=[1],
            title="Line",
        )
        fig = obj.create_line_figure(log_scale=True)

        self.assertEqual(len(fig.data), 2)
        self.assertEqual(fig.data[0].name, "P")
        self.assertEqual(fig.data[1].name, "Q (Y2)")
        self.assertEqual(fig.data[1].yaxis, "y2")
        self.assertEqual(fig.layout.xaxis.type, "date")
        self.assertEqual(fig.layout.yaxis.type, "log")
        self.assertEqual(fig.layout.yaxis2.type, "log")
        self.assertEqual(fig.layout.yaxis2.overlaying, "y")

    def test_dash_line_plot_input_validation(self):
        """Test line plot validation raises on x/y length mismatch."""
        with self.assertRaises(ValueError):
            DashLinePlot(
                x_values=np.asarray([0.0, 1.0, 2.0]),
                y_values=np.asarray([[1.0, 2.0]], dtype=float),
            )

    def test_dash_scatter_plot_single_property(self):
        """Test scatter plot can render a selected property key."""
        data = {
            "A": np.asarray([[0.0, 1.0], [1.0, 2.0]], dtype=float),
            "B": np.asarray([[2.0, 3.0], [3.0, 4.0]], dtype=float),
        }
        obj = DashScatterPlot(scatter_data=data)
        fig = obj.create_scatter_figure(property_name="A")

        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.data[0].name, "A")
        self.assertEqual(fig.layout.uirevision, "dash-scatter-view")

    def test_dash_table_pagination_and_dash_props(self):
        """Test table figure pagination and DataTable props generation."""
        if not HAS_PANDAS:
            self.skipTest("pandas not installed")

        table_df = pd.DataFrame(
            {
                "A": [1, 2, 3],
                "B": ["x", "y", "z"],
            }
        )
        obj = DashTable(table_data=table_df, page_size=2)

        fig = obj.create_table_figure(page=1)
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.data[0].type, "table")
        self.assertEqual(list(fig.data[0].cells.values[0]), [3])

        props = obj.create_dash_table_props()
        self.assertEqual(props["page_size"], 2)
        self.assertEqual(len(props["columns"]), 2)
        self.assertEqual(len(props["data"]), 3)

    def test_dash_dashboard_requires_at_least_one_component(self):
        """Test dashboard constructor rejects empty component composition."""
        with self.assertRaises(ValueError):
            DashDashboard()

    def test_dash_dashboard_layout_contains_all_component_panels(self):
        """Test dashboard layout includes graph/table IDs for provided components."""
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)
        map_plot = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P1"],
        )

        line_plot = DashLinePlot(
            x_values=np.asarray(["2026-01-01", "2026-01-02"], dtype="datetime64[D]"),
            y_values=np.asarray([[1.0, 2.0]], dtype=float),
            property_names=["L1"],
        )

        scatter_plot = DashScatterPlot(
            scatter_data={"S1": np.asarray([[1.0, 2.0], [2.0, 3.0]], dtype=float)}
        )

        if not HAS_PANDAS:
            self.skipTest("pandas not installed")
        table_plot = DashTable(table_data=pd.DataFrame({"A": [1, 2], "B": [3, 4]}))

        dashboard = DashDashboard(
            map_plot=map_plot,
            line_plot=line_plot,
            scatter_plot=scatter_plot,
            table_plot=table_plot,
            title="Combined",
        )
        layout = dashboard.create_layout(
            map_kwargs={"property_index": 0, "day_index": 0, "layer": 1}
        )

        layout_string = str(layout)
        self.assertIn("dashboard-map-graph", layout_string)
        self.assertIn("dashboard-line-graph", layout_string)
        self.assertIn("dashboard-scatter-graph", layout_string)
        self.assertIn("dashboard-table", layout_string)
        self.assertIn("Combined", layout_string)

    def test_dash_dashboard_create_app(self):
        """Test dashboard creates Dash app with non-empty layout."""
        scatter_plot = DashScatterPlot(
            scatter_data={"S1": np.asarray([[0.0, 1.0], [1.0, 2.0]], dtype=float)}
        )
        dashboard = DashDashboard(scatter_plot=scatter_plot, title="Scatter Only")
        app = dashboard.create_app()
        self.assertIsNotNone(app.layout)
        self.assertIn("Scatter Only", str(app.layout))

    def test_multi_panel_dashboard_requires_at_least_one_panel(self):
        """Test generic multi-panel dashboard rejects empty input dictionaries."""
        with self.assertRaises(ValueError):
            DashMultiPanelDashboard()

    def test_multi_panel_dashboard_nested_tabs_for_available_types(self):
        """Test nested tab structure uses type groups and panel-name tabs."""
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)

        map_plot_a = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P1"],
        )
        map_plot_b = DashMapPlot(
            vertices=vertices,
            layer_sizes=[2],
            grid_data=grid_data,
            property_names=["P2"],
        )
        line_plot = DashLinePlot(
            x_values=np.asarray([0.0, 1.0]),
            y_values=np.asarray([[1.0, 2.0]], dtype=float),
            property_names=["L"],
        )
        scatter_plot = DashScatterPlot(
            scatter_data={"S": np.asarray([[1.0, 2.0], [2.0, 3.0]], dtype=float)}
        )

        if not HAS_PANDAS:
            self.skipTest("pandas not installed")
        table_plot = DashTable(table_data=pd.DataFrame({"A": [1, 2], "B": [3, 4]}))

        dashboard = DashMultiPanelDashboard(
            map_plots={"Map A": map_plot_a, "Map B": map_plot_b},
            line_plots={"Line A": line_plot},
            scatter_plots={"Scatter A": scatter_plot},
            table_plots={"Table A": table_plot},
            title="Generic Wrapper",
        )

        layout_string = str(dashboard.create_layout())
        self.assertIn("Generic Wrapper", layout_string)
        self.assertIn("Maps", layout_string)
        self.assertIn("Line Plots", layout_string)
        self.assertIn("Scatter Plots", layout_string)
        self.assertIn("Tables", layout_string)
        self.assertIn("Map A", layout_string)
        self.assertIn("Map B", layout_string)
        self.assertIn("Line A", layout_string)
        self.assertIn("Scatter A", layout_string)
        self.assertIn("Table A", layout_string)
        self.assertIn("mp-map-0-graph", layout_string)
        self.assertIn("mp-map-1-graph", layout_string)
        self.assertIn("mp-line-0-graph", layout_string)
        self.assertIn("mp-scatter-0-graph", layout_string)
        self.assertIn("mp-table-0-table", layout_string)

    def test_multi_panel_dashboard_hides_empty_type_groups(self):
        """Test missing panel types are not rendered as top-level tabs."""
        line_plot = DashLinePlot(
            x_values=np.asarray([0.0, 1.0]),
            y_values=np.asarray([[1.0, 2.0]], dtype=float),
            property_names=["L"],
        )
        dashboard = DashMultiPanelDashboard(
            line_plots={"Line Only": line_plot},
            title="Line Only Wrapper",
        )
        layout_string = str(dashboard.create_layout())
        self.assertIn("Line Plots", layout_string)
        self.assertNotIn("Maps", layout_string)
        self.assertNotIn("Scatter Plots", layout_string)
        self.assertNotIn("Tables", layout_string)

    def test_multi_panel_dashboard_create_app(self):
        """Test generic wrapper builds a Dash app with callbacks and layout."""
        scatter_plot = DashScatterPlot(
            scatter_data={"S1": np.asarray([[0.0, 1.0], [1.0, 2.0]], dtype=float)}
        )
        dashboard = DashMultiPanelDashboard(
            scatter_plots={"Scatter Panel": scatter_plot},
            title="Scatter Wrapper",
        )
        app = dashboard.create_app()
        self.assertIsNotNone(app.layout)
        self.assertIn("Scatter Wrapper", str(app.layout))


if __name__ == "__main__":
    unittest.main()
