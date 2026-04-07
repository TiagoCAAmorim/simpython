"""Tests for SR3-backed Dash plotting wrapper."""

from pathlib import Path
import unittest

import numpy as np

from rsimpy.cmg.sr3reader import Sr3Reader
from rsimpy.common.plot_dash import DashMapPlot, DashScatterPlot


class TestSr3PlotDash(unittest.TestCase):
    """Validate `sr3.plots` wrappers and dashboard assembly."""

    @classmethod
    def setUpClass(cls):
        cls.test_file = Path("tests/sr3/base_case_3a.sr3")
        if not cls.test_file.exists():
            raise FileNotFoundError(f"Test file not found: {cls.test_file}")
        cls.sr3 = Sr3Reader(str(cls.test_file))

    def test_make_map_basic(self):
        """Map wrapper should build a DashMapPlot from SR3 properties."""
        days = self.sr3.dates.get_days("grid")[:2]
        map_obj = self.sr3.plots.make_map(
            properties=[("matrix", "PRES"), ("matrix", "POR")],
            days=days,
            title="Map A",
        )

        self.assertIsInstance(map_obj, DashMapPlot)
        self.assertEqual(map_obj.grid_data.shape[0], 2)
        self.assertEqual(map_obj.grid_data.shape[1], 2)

    def test_make_map_mixed_complete_and_incomplete_uses_active_cells(self):
        """Mixed property completeness should trim complete arrays to active cells."""
        days = self.sr3.dates.get_days("grid")[:1]
        map_obj = self.sr3.plots.make_map(
            properties=[("matrix", "BLOCKDEPTH"), ("matrix", "POR")],
            days=days,
        )
        expected_active = self.sr3.grid.get_size("n_active_matrix")
        self.assertEqual(map_obj.grid_data.shape[2], expected_active)

    def test_make_map_direct_grid_values_shape_validation(self):
        """Direct map values should raise clear size error on mismatch."""
        days = self.sr3.dates.get_days("grid")[:2]
        with self.assertRaises(ValueError):
            self.sr3.plots.make_map(
                properties=[("matrix", "PRES")],
                days=days,
                grid_values=np.zeros((1, 2, 5), dtype=float),
            )

    def test_make_scatter_timeseries_descriptor(self):
        """Scatter wrapper should support SR3 time-series pair descriptors."""
        scatter_obj = self.sr3.plots.make_scatter(
            data={
                "Np x WCut": ("well", "P11", "NP", "WCUT"),
            },
            title="Scatter A",
        )
        self.assertIsInstance(scatter_obj, DashScatterPlot)
        self.assertIn("Np x WCut", scatter_obj.scatter_data)
        self.assertEqual(scatter_obj.scatter_data["Np x WCut"].shape[1], 2)

    def test_dashboard_wrapper_returns_runnable_panel(self):
        """Dashboard wrapper should return an object with app + run method."""
        days = self.sr3.dates.get_days("grid")[:1]
        map_obj = self.sr3.plots.make_map(properties=[("matrix", "PRES")], days=days)
        scatter_obj = self.sr3.plots.make_scatter(
            data={"Np x WCut": ("well", "P11", "NP", "WCUT")}
        )

        panel = self.sr3.plots.dashboard(
            maps={"Map 1": map_obj},
            lines={},
            scatter={"Np x WCut": scatter_obj},
            table=None,
        )

        self.assertTrue(hasattr(panel, "run"))
        self.assertTrue(hasattr(panel, "app"))
        self.assertIsNotNone(panel.app.layout)


if __name__ == "__main__":
    unittest.main()
