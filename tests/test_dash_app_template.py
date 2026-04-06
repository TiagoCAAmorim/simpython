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
        self.assertIn("map-property-dropdown", layout_string)
        self.assertIn("map-grid-palette", layout_string)
        self.assertIn("map-day-slider", layout_string)
        self.assertIn("map-connection-palette", layout_string)
        self.assertIn("map-layer-slider", layout_string)
        self.assertIn("map-show-connections", layout_string)
        self.assertIn("map-connection-width", layout_string)
        self.assertIn("map-connection-segments", layout_string)
        self.assertIn("map-graph", layout_string)

    def test_build_step_2_2_demo_map_plot(self):
        obj = build_step_2_2_demo_map_plot()
        self.assertEqual(obj.grid_data.shape, (4, 5, 54))
        self.assertEqual(
            obj.property_names,
            ["Cell Index", "Column", "Row", "Index + 30*Day"],
        )
        self.assertEqual(len(obj.cell_names), 54)
        self.assertEqual(obj.connection_property_names, ["Connectivity"])
        self.assertTrue(obj.has_connections())
        self.assertEqual(obj.layer_sizes.tolist(), [30, 12, 12])

    def test_demo_figure_has_global_bounds_and_connections(self):
        obj = build_step_2_2_demo_map_plot()
        fig = obj.create_map_figure(property_index=0, day_index=0, layer=2, add_connections=True)
        self.assertIsNotNone(fig.layout.xaxis.range)
        self.assertIsNotNone(fig.layout.yaxis.range)
        self.assertGreater(float(fig.layout.xaxis.range[1]), 5.0)
        self.assertGreater(float(fig.layout.yaxis.range[1]), 4.0)
        names = [tr.name for tr in fig.data]
        self.assertIn("connection-triangle-up", names)
        self.assertIn("connection-triangle-down", names)
        self.assertEqual(fig.layout.uirevision, "dash-map-view")

    def test_create_step_2_2_working_example_app(self):
        app = create_step_2_2_working_example_app()
        self.assertIsNotNone(app.layout)
        self.assertIn("Step 2.3", str(app.layout))


if __name__ == "__main__":
    unittest.main()
