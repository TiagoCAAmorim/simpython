"""Tests for Dash app template scaffolding."""

import unittest

from rsimpy.common.dash_app_template import (
    build_step_2_2_demo_map_plot,
    build_triangle_demo_figure,
    create_dash_template_app,
    create_step_2_2_working_example_app,
)


class TestDashAppTemplate(unittest.TestCase):
    """Validate minimal Dash template structure for Step 1.2."""

    def test_build_triangle_demo_figure_with_triangle(self):
        fig = build_triangle_demo_figure(direction="up", size=0.2, show_triangle=True)
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.data[0].fill, "toself")

    def test_build_triangle_demo_figure_hidden_triangle(self):
        fig = build_triangle_demo_figure(direction="down", size=0.2, show_triangle=False)
        self.assertEqual(len(fig.data), 0)

    def test_create_dash_template_app_layout(self):
        app = create_dash_template_app()
        self.assertIsNotNone(app.layout)
        layout_string = str(app.layout)
        self.assertIn("map-show-grid", layout_string)
        self.assertIn("map-property-dropdown", layout_string)
        self.assertIn("map-property-controls-group", layout_string)
        self.assertIn("map-grid-palette", layout_string)
        self.assertIn("map-day-slider", layout_string)
        self.assertIn("map-grid-controls-group", layout_string)
        self.assertIn("map-connection-controls-group", layout_string)
        self.assertIn("map-connection-palette", layout_string)
        self.assertIn("map-contour-controls-group", layout_string)
        self.assertIn("map-layer-slider", layout_string)
        self.assertIn("map-show-connections", layout_string)
        self.assertIn("map-show-contours", layout_string)
        self.assertIn("map-connection-width", layout_string)
        self.assertIn("map-connection-segments", layout_string)
        self.assertIn("map-contour-count", layout_string)
        self.assertIn("map-graph", layout_string)

    def test_build_step_2_2_demo_map_plot(self):
        obj = build_step_2_2_demo_map_plot()
        self.assertEqual(obj.grid_data.shape, (5, 5, 54))
        self.assertEqual(
            obj.property_names,
            ["Cell Index", "Column", "Row", "Index + 30*Day", "Mean Z"],
        )
        self.assertEqual(len(obj.cell_names), 54)
        self.assertEqual(obj.connection_property_names, ["Connectivity"])
        self.assertTrue(obj.has_connections())
        self.assertEqual(obj.layer_sizes.tolist(), [30, 12, 12])

    def test_default_map_hides_grid_when_disabled(self):
        obj = build_step_2_2_demo_map_plot()
        fig = obj.create_map_figure(property_index=0, day_index=0, layer=1, add_grid=False)
        names = [tr.name for tr in fig.data]
        self.assertNotIn("cell-polygon", names)
        self.assertNotIn("cell-polygon-hover", names)
        self.assertNotIn("colorbar", names)

    def test_demo_figure_has_global_bounds_and_connections(self):
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
        app = create_step_2_2_working_example_app()
        self.assertIsNotNone(app.layout)
        self.assertIn("Step 2.3", str(app.layout))


if __name__ == "__main__":
    unittest.main()
