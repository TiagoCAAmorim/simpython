"""Tests for Dash plotting foundation utilities."""

import unittest

import numpy as np

from rsimpy.common.plot_dash import (
    DashMapPlot,
    add_triangle_trace,
    build_layer_per_cell,
    create_triangle_vertices,
    _determine_contour_levels,
    _get_contour_segments_triangle,
    validate_layer_sizes,
)


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
    """Validate early Dash plotting building blocks."""

    def test_validate_layer_sizes(self):
        sizes = validate_layer_sizes([2, 3, 1], n_cells=6)
        np.testing.assert_array_equal(sizes, np.array([2, 3, 1]))

    def test_build_layer_per_cell(self):
        layer_per_cell = build_layer_per_cell([2, 3])
        np.testing.assert_array_equal(layer_per_cell, np.array([1, 1, 2, 2, 2]))

    def test_determine_contour_levels_uses_global_range(self):
        vertices = np.zeros((2, 4, 3), dtype=float)
        vertices[0, :, 2] = [0.0, 10.0, 10.0, 0.0]
        vertices[1, :, 2] = [100.0, 110.0, 110.0, 100.0]

        levels = _determine_contour_levels(vertices, contour_count=3)
        np.testing.assert_allclose(levels, np.array([0.0, 50.0, 100.0]))

    def test_contour_segments_flat_edge_crosses_midpoint(self):
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
        xs, ys = create_triangle_vertices(10.0, 20.0, size=2.0, direction="up")
        self.assertEqual(len(xs), 4)
        self.assertEqual(len(ys), 4)
        self.assertGreater(ys[0], ys[1])
        self.assertGreater(ys[0], ys[2])

    def test_create_triangle_vertices_down(self):
        xs, ys = create_triangle_vertices(10.0, 20.0, size=2.0, direction="down")
        self.assertEqual(len(xs), 4)
        self.assertEqual(len(ys), 4)
        self.assertLess(ys[0], ys[1])
        self.assertLess(ys[0], ys[2])

    def test_add_triangle_trace(self):
        try:
            import plotly.graph_objects as go
        except ImportError:
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
        vertices = np.zeros((6, 4, 3), dtype=float)
        obj = DashMapPlot(vertices=vertices, layer_sizes=[2, 2, 2])
        self.assertEqual(obj.grid_data.shape, (1, 1, 6))
        self.assertEqual(obj.property_names, ["Cell Index"])

    def test_dash_map_plot_renders_only_selected_layer(self):
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
        """Manual smoke case requested in plan: 30 cells, single layer, cell index property."""
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
        polygon_hover_traces = [tr for tr in fig.data if tr.name == "cell-polygon-hover"]
        self.assertEqual(len(polygon_traces), 30)
        self.assertEqual(len(polygon_hover_traces), 30)
        self.assertIn("(1,1)", polygon_hover_traces[0].text[0])
        self.assertIn("(5,6)", polygon_hover_traces[-1].text[0])
        self.assertIn("Cell Index", polygon_hover_traces[0].text[0])
        self.assertEqual(polygon_hover_traces[0].hovertemplate, "%{text}<extra></extra>")
        self.assertEqual(polygon_hover_traces[0].mode, "markers")
        self.assertEqual(len(polygon_hover_traces[0].x), 9)
        self.assertEqual(polygon_traces[0].hoverinfo, "skip")
        self.assertEqual(obj.property_names, ["Cell Index"])

    def test_map_figure_renders_contours_with_count(self):
        vertices = _make_regular_grid_vertices(1, 2)
        vertices[:, :, 2] = np.asarray([
            [0.0, 10.0, 10.0, 0.0],
            [100.0, 110.0, 110.0, 100.0],
        ], dtype=float)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)

        obj = DashMapPlot(vertices=vertices, layer_sizes=[2], grid_data=grid_data, property_names=["P1"])
        fig = obj.create_map_figure(property_index=0, day_index=0, layer=1, add_contours=True, contour_count=3)
        contour_traces = [tr for tr in fig.data if tr.name == "contour-line"]
        contour_hover_traces = [tr for tr in fig.data if tr.name == "contour-line-hover"]
        self.assertGreaterEqual(len(contour_traces), 1)
        self.assertEqual(len(contour_traces), len(contour_hover_traces))
        self.assertGreaterEqual(float(contour_traces[0].line.width), 3.0)

    def test_map_figure_default_axes_use_global_polygon_bounds(self):
        vertices = _make_regular_grid_vertices(2, 2)
        grid_data = np.arange(4, dtype=float).reshape(1, 1, 4)
        obj = DashMapPlot(vertices=vertices, layer_sizes=[2, 2], grid_data=grid_data, property_names=["P1"])

        fig = obj.create_map_figure(property_index=0, day_index=0, layer=2)
        x_range = list(fig.layout.xaxis.range)
        y_range = list(fig.layout.yaxis.range)
        self.assertLessEqual(x_range[0], 0.0)
        self.assertGreaterEqual(x_range[1], 2.0)
        self.assertLessEqual(y_range[0], 0.0)
        self.assertGreaterEqual(y_range[1], 2.0)

    def test_global_color_scale_uses_all_days_for_property(self):
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
        self.assertTrue(all("e" not in str(v).lower() or "-" not in str(v) for v in grid_colorbar.marker.colorbar.ticktext))

    def test_dash_map_plot_connections_lines_and_triangles(self):
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

        first_hover_trace = [tr for tr in fig_l1.data if tr.name == "connection-line-hover"][0]
        self.assertNotIn("Connection:", first_hover_trace.text[0])
        self.assertIn("0->1", first_hover_trace.text[0])

        grid_colorbar = [tr for tr in fig_l1.data if tr.name == "colorbar"][0]
        conn_colorbar = [tr for tr in fig_l1.data if tr.name == "connection-colorbar"][0]
        self.assertLess(float(grid_colorbar.marker.colorbar.x), float(conn_colorbar.marker.colorbar.x))

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
        self.assertNotEqual(grid_colorbar.marker.colorscale, conn_colorbar.marker.colorscale)

    def test_connection_log_scale_non_positive_is_dark_gray(self):
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
        line_colors = [str(tr.line.color) for tr in fig.data if tr.name == "connection-line"]
        self.assertTrue(any("77, 77, 77" in color for color in line_colors))
        conn_colorbar = [tr for tr in fig.data if tr.name == "connection-colorbar"][0]
        self.assertEqual(str(conn_colorbar.marker.colorbar.title.text), "Connection")
        self.assertIsNotNone(conn_colorbar.marker.colorbar.ticktext)

    def test_connection_line_segments_respected(self):
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
        vertices = _make_regular_grid_vertices(1, 2)
        grid_data = np.arange(2, dtype=float).reshape(1, 1, 2)
        obj = DashMapPlot(vertices=vertices, layer_sizes=[2], grid_data=grid_data, property_names=["P1"])
        fig = obj.create_map_figure(property_index=0, day_index=0, layer=1)
        self.assertEqual(fig.layout.uirevision, "dash-map-view")

    def test_dash_map_plot_connection_validation(self):
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


if __name__ == "__main__":
    unittest.main()
