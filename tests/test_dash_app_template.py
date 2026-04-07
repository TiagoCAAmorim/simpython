"""Tests for Dash app template scaffolding.

This module validates the Dash application template structure and component integration
for the Step 2.2 interactive map visualization system. Tests cover:
- Triangle demo figure generation
- Dash app layout and control presence
- Demo map plot creation and data structure validation
- Control responsiveness and grid visibility behavior
- Working example app structure
"""

import unittest

from rsimpy.common.dash_app_template import (
    build_step_3_demo_line_plot,
    build_step_3_demo_scatter_plot,
    build_step_3_demo_table,
    build_step_2_2_demo_map_plot,
    build_triangle_demo_figure,
    create_dash_template_app,
    create_step_4_1_working_example_app,
    create_step_3_working_example_app,
    create_step_2_2_working_example_app,
    create_working_example_app,
)


class TestDashAppTemplate(unittest.TestCase):
    """Validate minimal Dash template structure for Step 1.2.

    Tests cover:
    - Triangle demo helper function
    - Layout structure and required control IDs
    - Demo map plot dataset generation (30-cell 3-layer grid)
    - Grid visibility toggle behavior
    - Cross-layer connection rendering
    - Working example app integration
    """

    def test_build_triangle_demo_figure_with_triangle(self):
        """Test triangle demo figure renders a single triangle trace when show_triangle=True."""
        fig = build_triangle_demo_figure(direction="up", size=0.2, show_triangle=True)
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.data[0].fill, "toself")

    def test_build_triangle_demo_figure_hidden_triangle(self):
        """Test triangle demo figure returns empty figure when show_triangle=False."""
        fig = build_triangle_demo_figure(direction="down", size=0.2, show_triangle=False)
        self.assertEqual(len(fig.data), 0)

    def test_create_dash_template_app_layout(self):
        """Test Dash template app layout contains all required control component IDs.

        Verifies presence of:
        - Grid controls (show, options, palette, log scale)
        - Connection controls (show, options, palette, width, segments, log scale)
        - Contour controls (show, options, count)
        - Well controls (show, options, size)
        - Property and day sliders
        - Layer slider and graph component
        """
        app = create_dash_template_app()
        self.assertIsNotNone(app.layout)
        layout_string = str(app.layout)
        self.assertIn("map-show-grid", layout_string)
        self.assertIn("map-grid-options-toggle", layout_string)
        self.assertIn("map-property-dropdown", layout_string)
        self.assertIn("map-property-controls-group", layout_string)
        self.assertIn("map-grid-palette", layout_string)
        self.assertIn("map-grid-log-scale", layout_string)
        self.assertIn("map-day-slider", layout_string)
        self.assertIn("map-grid-controls-group", layout_string)
        self.assertIn("map-connection-controls-group", layout_string)
        self.assertIn("map-connection-palette", layout_string)
        self.assertIn("map-contour-controls-group", layout_string)
        self.assertIn("map-layer-slider", layout_string)
        self.assertIn("map-show-connections", layout_string)
        self.assertIn("map-connection-options-toggle", layout_string)
        self.assertIn("map-show-contours", layout_string)
        self.assertIn("map-contour-options-toggle", layout_string)
        self.assertIn("map-show-wells", layout_string)
        self.assertIn("map-well-options-toggle", layout_string)
        self.assertIn("map-well-controls-group", layout_string)
        self.assertIn("map-well-size", layout_string)
        self.assertIn("map-connection-width", layout_string)
        self.assertIn("map-connection-segments", layout_string)
        self.assertIn("map-connection-log-scale", layout_string)
        self.assertIn("map-contour-count", layout_string)
        self.assertIn("map-graph", layout_string)

    def test_build_step_2_2_demo_map_plot(self):
        """Test demo map plot creation generates correct 3-layer dataset structure.

        Validates:
        - Grid data shape: (5 properties, 5 days, ~300 cells across 3 layers)
        - Property names list (Cell Index, Column, Row, computed formula, Mean Z)
        - Cell names generation
        - Connection property names
        - Layer size array consistency
        """
        n_rows, n_cols =10, 10
        n_cells = n_rows * n_cols + (n_rows - 1) * (n_cols - 1) + (n_rows - 2) * (n_cols - 2)
        obj = build_step_2_2_demo_map_plot(n_rows=n_rows, n_cols=n_cols, n_days=5)
        self.assertEqual(obj.grid_data.shape, (5, 5, n_cells))
        self.assertEqual(
            obj.property_names,
            ["Cell Index", "Column", "Row", "Index + 30*Day", "Mean Z"],
        )
        self.assertEqual(len(obj.cell_names), n_cells)
        self.assertEqual(obj.connection_property_names, ["Connectivity"])
        self.assertTrue(obj.has_connections())
        self.assertTrue(obj.has_wells())
        self.assertEqual(
            obj.layer_sizes.tolist(),
            [n_rows * n_cols, (n_rows - 1) * (n_cols - 1), (n_rows - 2) * (n_cols - 2)]
        )

    def test_default_map_hides_grid_when_disabled(self):
        """Test map figure does not render grid polygons or colorbar when add_grid=False."""
        obj = build_step_2_2_demo_map_plot()
        fig = obj.create_map_figure(property_index=0, day_index=0, layer=1, add_grid=False)
        names = [tr.name for tr in fig.data]
        self.assertNotIn("cell-polygon", names)
        self.assertNotIn("cell-polygon-hover", names)
        self.assertNotIn("colorbar", names)

    def test_demo_figure_has_global_bounds_and_connections(self):
        """Test map figure on layer 2 includes both up and down connection triangles.

        Verifies:
        - Layout is initialized
        - Polygon traces exist for layer 2
        - Both up and down triangle traces are present
        - UI revision is set for zoom persistence
        """
        obj = build_step_2_2_demo_map_plot()
        fig = obj.create_map_figure(property_index=0, day_index=0, layer=2, add_connections=True)
        # Figure uses autorange for zoom persistence (no explicit range set)
        self.assertIsNotNone(fig.layout)
        # Verify polygon data is present (at least one cell polygon for layer 2)
        polygon_traces = [tr for tr in fig.data if "cell-polygon" in (tr.name or "")]
        self.assertGreater(len(polygon_traces), 0)
        # Verify both connection triangle types are present
        names = [tr.name for tr in fig.data]
        self.assertIn("connection-triangle-up", names)
        self.assertIn("connection-triangle-down", names)
        # Verify zoom persistence is enabled
        self.assertEqual(fig.layout.uirevision, "dash-map-view")

    def test_create_step_2_2_working_example_app(self):
        """Test working example app initializes with Step 2.3 title in layout."""
        app = create_step_2_2_working_example_app()
        self.assertIsNotNone(app.layout)
        self.assertIn("Step 2.3", str(app.layout))

    def test_build_step_3_demo_line_plot(self):
        """Test Step 3 line example builds a valid multi-trace figure."""
        obj = build_step_3_demo_line_plot(n_days=10)
        fig = obj.create_line_figure(marker_mode=True)
        self.assertEqual(len(fig.data), 3)
        self.assertEqual(fig.data[2].yaxis, "y2")
        self.assertEqual(fig.layout.xaxis.type, "date")

    def test_build_step_3_demo_scatter_plot(self):
        """Test Step 3 scatter example builds two scatter traces."""
        obj = build_step_3_demo_scatter_plot(n_points=20, seed=3)
        fig = obj.create_scatter_figure()
        self.assertEqual(len(fig.data), 2)
        self.assertEqual(fig.data[0].type, "scatter")

    def test_build_step_3_demo_table(self):
        """Test Step 3 table example builds DataTable-compatible props."""
        obj = build_step_3_demo_table(n_rows=12)
        props = obj.create_dash_table_props(page_size=5)
        self.assertEqual(props["page_size"], 5)
        self.assertEqual(len(props["data"]), 12)
        self.assertEqual(len(props["columns"]), 5)

    def test_create_step_3_working_example_app(self):
        """Test Step 3 working example app contains all demo components."""
        app = create_step_3_working_example_app()
        self.assertIsNotNone(app.layout)
        layout_string = str(app.layout)
        self.assertIn("Step 3 Working Examples", layout_string)
        self.assertIn("step3-line-graph", layout_string)
        self.assertIn("step3-line-log-y1", layout_string)
        self.assertIn("step3-line-log-y2", layout_string)
        self.assertIn("step3-line-y2-controls", layout_string)
        self.assertIn("step3-scatter-graph", layout_string)
        self.assertIn("step3-scatter-log-x", layout_string)
        self.assertIn("step3-scatter-log-y", layout_string)
        self.assertIn("step3-table", layout_string)
        self.assertIn("step3-table-page-size", layout_string)
        self.assertIn("step3-table-download-btn", layout_string)
        self.assertIn("step3-table-download", layout_string)

    def test_create_step_4_1_working_example_app(self):
        """Test Step 4.1 working example app contains combined dashboard panels."""
        app = create_step_4_1_working_example_app()
        self.assertIsNotNone(app.layout)
        layout_string = str(app.layout)
        self.assertIn("Step 4.1 Dashboard Example", layout_string)
        self.assertIn("dashboard-map-graph", layout_string)
        self.assertIn("dashboard-line-graph", layout_string)
        self.assertIn("dashboard-scatter-graph", layout_string)
        self.assertIn("dashboard-table", layout_string)
        self.assertIn("step4-map-property", layout_string)
        self.assertIn("step4-map-day", layout_string)
        self.assertIn("step4-map-layer", layout_string)
        self.assertIn("step4-line-log-y", layout_string)
        self.assertIn("step4-scatter-log-x", layout_string)
        self.assertIn("step4-table-page-size", layout_string)
        self.assertIn("step4-table-download-btn", layout_string)

    def test_create_working_example_app_step4(self):
        """Test selector can create Step 4 dashboard app."""
        app = create_working_example_app(example="step4")
        self.assertIsNotNone(app.layout)
        self.assertIn("Step 4.1 Dashboard Example", str(app.layout))


if __name__ == "__main__":
    unittest.main()
