"""
Test script for the PlotHandler class.
"""
import unittest
from pathlib import Path
from bokeh.plotting import show
from matplotlib import contour

import context  # noqa # pylint: disable=unused-import
from rsimpy.cmg.sr3reader import Sr3Reader


class TestPlotHandler(unittest.TestCase):
    """Tests for PlotHandler functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are expensive to create."""
        cls.test_file = Path("tests/sr3/base_case_3a.sr3")
        if not cls.test_file.exists():
            raise FileNotFoundError(f"Test file not found: {cls.test_file}")
        cls.sr3 = Sr3Reader(str(cls.test_file))
        cls.show = True

    def test_sr3_reader_loads(self):
        """Test that SR3 file loads successfully."""
        self.assertIsNotNone(self.sr3, "SR3 reader should not be None")
        self.assertIsNotNone(self.sr3.plot, "PlotHandler should be available")

    def test_plot_map_returns_panel(self):
        """Test that plot_map returns a valid Bokeh panel."""
        days = self.sr3.dates.get_days('grid')
        self.assertGreater(len(days), 0, "Should have at least one day available")

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="PERMI",
            days=days[0],
            layers=[89],
            width=800,
            height=600,
            palette='Turbo',
            log_scale=True,
            color_limits=(0.1, 500),
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        # Bokeh panels/layouts have a children attribute
        self.assertTrue(hasattr(panel, 'children') or hasattr(panel, 'renderers'),
                       "Panel should be a valid Bokeh layout or figure")
        if self.show:
            show(panel)

    def test_plot_map_with_multiple_days(self):
        """Test that plot_map works with multiple days."""
        days = self.sr3.dates.get_days('grid')

        # Test with first few days
        test_days = days[:min(3, len(days))]

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="PRES",
            days=test_days,
            layers=[89],
            title="Test Plot: PRES over time",
            width=800,
            height=600
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.show:
            show(panel)

    def test_plot_map_with_different_properties(self):
        """Test that plot_map works with different properties."""
        days = self.sr3.dates.get_days('grid')
        properties = ["PRES", "PERMI"]

        for prop in properties:
            with self.subTest(property_name=prop):
                panel = self.sr3.plot.plot_map(
                    element="matrix",
                    property_name=prop,
                    days=days[0],
                    layers=[89],
                    width=800,
                    height=600
                )
                self.assertIsNotNone(panel, f"Panel should not be None for {prop}")

    def test_plot_map_with_custom_colors(self):
        """Test that plot_map works with custom color settings."""
        days = self.sr3.dates.get_days('grid')

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="PERMI",
            days=days[0],
            layers=[89],
            width=800,
            height=600,
            palette='Viridis',
            log_scale=False,
            out_of_range_colors=('gray', 'red'),
            nan_inf_color='gray',
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.show:
            show(panel)

    def test_plot_map_with_complete_property_and_contour(self):
        """Test that plot_map works with complete grid property and contour lines."""
        days = self.sr3.dates.get_days('grid')

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="BLOCKDEPTH",
            days=days[0],
            layers=range(50, 90),
            width=800,
            height=600,
            palette='Viridis',
            log_scale=False,
            out_of_range_colors=('gray', 'red'),
            nan_inf_color='gray',
            contour_step=50.0,
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.show:
            show(panel)


if __name__ == '__main__':
    unittest.main()
