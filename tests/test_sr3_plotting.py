"""
Test script for the PlotHandler class.
"""
import unittest
from pathlib import Path
import numpy as np
from bokeh.plotting import save, column, figure, output_file

from rsimpy.cmg.sr3reader import Sr3Reader

def get_figure(panel):
    """Extract figure from panel (handles both direct figures and layouts)"""
    if hasattr(panel, 'select'):
        # It's a layout, find the first figure
        figs = panel.select({"type": figure})
        return next(figs) if figs else None
    return panel  # It's already a figure

class TestPlotHandler(unittest.TestCase):
    """Tests for PlotHandler functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are expensive to create."""
        cls.test_file = Path("tests/sr3/base_case_3a.sr3")
        if not cls.test_file.exists():
            raise FileNotFoundError(f"Test file not found: {cls.test_file}")
        cls.sr3 = Sr3Reader(str(cls.test_file))
        cls.save = True

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
        if self.save:
            output_file("test_plot_map_returns_panel.html")
            save(panel)

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
            height=600,
            contour_step=50.0,
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.save:
            output_file("test_plot_map_with_multiple_days.html")
            save(panel)

    def test_plot_map_with_different_properties(self):
        """Test that plot_map works with different properties."""
        days = self.sr3.dates.get_days('grid')
        properties = ["PRES", "PERMI", "POR"]

        panels = []
        for prop in properties:
            with self.subTest(property_name=prop):
                panel = self.sr3.plot.plot_map(
                    element="matrix",
                    property_name=prop,
                    days=days[0],
                    layers=[89],
                    width=800,
                    height=600,
                    log_scale=prop in ["PERMI"],  # Log scale for PERMI only
                )
                self.assertIsNotNone(panel, f"Panel should not be None for {prop}")
                panels.append(panel)

        # Sync all figures to the first one's ranges
        if len(panels) > 1:
            fig_refs = [get_figure(panel) for panel in panels]
            for fig in fig_refs[1:]:
                fig.x_range = fig_refs[0].x_range
                fig.y_range = fig_refs[0].y_range

        if self.save:
            output_file("test_plot_map_with_different_properties.html")
            save(column(*panels))

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
        if self.save:
            output_file("test_plot_map_with_custom_colors.html")
            save(panel)

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
            add_top=True,
            palette='Viridis',
            log_scale=False,
            out_of_range_colors=('gray', 'red'),
            nan_inf_color='gray',
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.save:
            output_file("test_plot_map_with_complete_property_and_contour.html")
            save(panel)

    def test_plot_map_with_connections(self):
        """Test that plot_map works with connections."""
        days = self.sr3.dates.get_days('grid')

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="PERMJ",
            days=days[0],
            layers=[86,87],
            width=1600,
            height=600,
            add_top=True,
            add_connections=True,
            palette='Turbo',
            log_scale=True,
            out_of_range_colors=None,
            nan_inf_color=None,
            ijk_labels=True,
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.save:
            output_file("test_plot_map_with_connections.html")
            save(panel)

    def test_plot_map_with_wells(self):
        """Test that plot_map works with connections."""
        days = self.sr3.dates.get_days('grid')

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="PERMJ",
            days=days[0],
            layers=[86,87],
            width=1600,
            height=600,
            add_top=True,
            add_connections=False,
            add_wells=True,
            well_property_name="WELLID",
            palette='Turbo',
            log_scale=True,
            out_of_range_colors=None,
            nan_inf_color=None,
            ijk_labels=True,
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.save:
            output_file("test_plot_map_with_wells.html")
            save(panel)

    def test_plot_map_with_wells_dates(self):
        """Test that plot_map works with connections and multiple dates."""
        days = self.sr3.dates.get_days('grid')

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="PRES",
            days=days[0:5],
            layers=[86],
            width=1600,
            height=600,
            add_top=True,
            add_connections=False,
            add_wells=True,
            well_property_name="WELLID",
            palette='Turbo',
            log_scale=True,
            out_of_range_colors=None,
            nan_inf_color=None,
            ijk_labels=True,
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.save:
            output_file("test_plot_map_with_wells_multiple_dates.html")
            save(panel)

    def test_plot_map_with_custom_prop(self):
        """Test that plot_map works with custom property."""
        n_cells = self.sr3.grid.get_size("n_cells")
        ni, nj, _ = self.sr3.grid.get_size("nijk")
        custom_property = [i % (ni*nj) for i in range(n_cells)]

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="Cell Index",
            grid_property=custom_property,
            days=[10],
            layers=[89],
            title="Test Plot: Cell Index",
            width=800,
            height=600,
            contour_step=50.0,
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.save:
            output_file("test_plot_map_with_custom_property.html")
            save(panel)

    def test_plot_map_with_custom_prop_act(self):
        """Test that plot_map works with custom property."""
        n_cells = self.sr3.grid.get_size("n_active")
        custom_property = [i - 23380 for i in range(n_cells)]

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="Cell Index",
            grid_property=custom_property,
            days=[10],
            layers=[89],
            title="Test Plot: Cell Index",
            width=800,
            height=600,
            contour_step=50.0,
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.save:
            output_file("test_plot_map_with_custom_property_act.html")
            save(panel)

    def test_plot_map_with_custom_connections(self):
        """Test that plot_map works with custom connection values."""
        layers = [86, 87]
        day = self.sr3.dates.get_days('grid')[0]
        n_connections = self.sr3.connections.get_connections(as_active=False).shape[0]

        custom_connections = np.ones((n_connections, 1))

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="PERMJ",
            days=[day],
            layers=layers,
            add_connections=True,
            connection_property=custom_connections,
            width=1000,
            height=500,
            ijk_labels=True,
        )

        self.assertIsNotNone(panel, "Panel should not be None")

    def test_plot_map_with_invalid_custom_connections(self):
        """Test that plot_map validates custom connection values shape."""
        layers = [86, 87]
        day = self.sr3.dates.get_days('grid')[0]
        n_connections = self.sr3.connections.get_connections(as_active=False).shape[0]

        invalid_connections = np.ones((n_connections - 1, 1))

        with self.assertRaises(ValueError):
            self.sr3.plot.plot_map(
                element="matrix",
                property_name="PERMJ",
                days=[day],
                layers=layers,
                add_connections=True,
                connection_property=invalid_connections,
                width=1000,
                height=500,
                ijk_labels=True,
            )

    def test_plot_map_with_custom_connections_multiple_dates(self):
        """Test custom time-varying connection values for multiple dates."""
        days = self.sr3.dates.get_days('grid')[:3]
        layers = [86]
        n_connections = self.sr3.connections.get_connections(as_active=False).shape[0]

        custom_connections = np.ones((n_connections, len(days)))
        if len(days) > 1:
            custom_connections[:, 1:] = 2.0

        panel = self.sr3.plot.plot_map(
            element="matrix",
            property_name="PRES",
            days=days,
            layers=layers,
            add_connections=True,
            connection_property=custom_connections,
            width=1000,
            height=500,
            ijk_labels=True,
        )

        self.assertIsNotNone(panel, "Panel should not be None")
        if self.save:
            output_file("test_plot_map_with_custom_connections.html")
            save(panel)


if __name__ == '__main__':
    unittest.main()
