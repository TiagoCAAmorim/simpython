"""Manual interactive check for the Map panel's "Download Maps (All Days)" button.

This is not part of the automated test suite (it opens a real Dash server and
blocks waiting for browser interaction). Run it directly:

    python tests/manual_map_download_panel.py

Then in the browser:
1. Open the "Map" tab.
2. Pick a property, zoom/pan on the map, optionally set Min/Max color limits.
3. Click "Download Maps (All Days)" and confirm a .zip downloads with one PNG
   per day, all sharing the current zoom window and color scale.
"""

from __future__ import annotations

import numpy as np

from rsimpy.common.plot_dash import DashMapPlot
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


def build_panel():
    n_rows, n_cols = 6, 8
    n_cells = n_rows * n_cols
    n_days = 12

    vertices = _make_regular_grid_vertices(n_rows, n_cols)
    cell_names = [f"({r+1},{c+1})" for r in range(n_rows) for c in range(n_cols)]
    day_labels = [str(30 * i) for i in range(n_days)]

    rng = np.random.default_rng(0)
    base = rng.uniform(50.0, 250.0, size=n_cells)
    decline = np.linspace(1.0, 0.4, n_days)
    pressure = base[None, :] * decline[:, None]

    permeability = rng.lognormal(mean=3.0, sigma=1.0, size=(n_days, n_cells))
    permeability = np.tile(permeability[0:1, :], (n_days, 1))

    grid_data = np.stack([pressure, permeability], axis=0)

    map_plot = DashMapPlot(
        vertices=vertices,
        layer_sizes=[n_cells],
        grid_data=grid_data,
        property_names=["PRES", "PERMI"],
        cell_names=cell_names,
        day_labels=day_labels,
        title="Manual Map",
    )

    dashboard = DashMultiPanelDashboard(
        map_plots={"Map": map_plot},
        title="Map Download Manual Check",
    )
    return dashboard.create_app()


if __name__ == "__main__":
    app = build_panel()
    print("Open http://127.0.0.1:8050 and try the 'Download Maps (All Days)' button.")
    app.run(debug=True)
