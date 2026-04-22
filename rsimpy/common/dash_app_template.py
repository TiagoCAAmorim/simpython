"""Minimal Dash app template for map workflows.

This module provides a small, testable Dash application skeleton that will be
expanded in later steps to host map, line, scatter, and table components.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import pandas as pd

from rsimpy.cmg.sr3reader import Sr3Reader
from rsimpy.cmg.sr3reader.plot_dash import PlotHandlerDash
from rsimpy.common.plot_dashboard import DashMapCompare

from rsimpy.common.plot_dash import (
    DashLinePlot,
    DashMapPlot,
    DashScatterPlot,
    DashTable,
    add_triangle_trace,
)
from rsimpy.common.plot_dashboard import DashMapCompare, DashMultiPanelDashboard


DEMO_EXAMPLES = ("step4generic", "sr3", "compare")


PALETTE_OPTIONS = [
    {"label": "Turbo", "value": "Turbo"},
    {"label": "Viridis", "value": "Viridis"},
    {"label": "Plasma", "value": "Plasma"},
    {"label": "Inferno", "value": "Inferno"},
    {"label": "Magma", "value": "Magma"},
    {"label": "Cividis", "value": "Cividis"},
    {"label": "Greys", "value": "Greys"},
]


def build_triangle_demo_figure(direction="up", size=0.3, show_triangle=True):
    """Build a small figure used to validate controls + callback wiring."""
    fig = go.Figure()
    fig.update_layout(
        title="Dash Map Template - Triangle Demo",
        xaxis_title="X",
        yaxis_title="Y",
        xaxis={"range": [0.0, 1.0]},
        yaxis={"range": [0.0, 1.0], "scaleanchor": "x", "scaleratio": 1},
        template="plotly_white",
        margin={"l": 30, "r": 20, "t": 40, "b": 30},
    )

    if show_triangle:
        add_triangle_trace(
            fig=fig,
            center_x=0.5,
            center_y=0.5,
            size=float(size),
            direction=direction,
            line_color="black",
            fill_color="#cc2f2f",
            name="triangle",
        )

    return fig


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


def build_step_2_2_demo_map_plot(n_rows=10, n_cols=20, n_days=5):
    """Build the working example with two layers and cross-layer triangles."""
    layer1_rows, layer1_cols = n_rows, n_cols
    layer2_rows, layer2_cols = n_rows-1, n_cols-1
    layer3_rows, layer3_cols = n_rows-2, n_cols-2

    # Create grid vertices and shift origin to (1000, 10000) for demo
    origin_x, origin_y = 1000.0, 10000.0
    offset = np.array([origin_x, origin_y, 0.0])
    layer1_vertices = _make_regular_grid_vertices(layer1_rows, layer1_cols) + offset
    layer2_vertices = _make_regular_grid_vertices(layer2_rows, layer2_cols) + offset
    layer3_vertices = _make_regular_grid_vertices(layer3_rows, layer3_cols) + offset

    # Add synthetic z variation for contour rendering in Step 2.4.
    layer_list = [layer1_vertices, layer2_vertices, layer3_vertices]
    for layer_idx, layer_vertices in enumerate(layer_list, start=1):
        local_x = layer_vertices[:, :, 0] - origin_x
        local_y = layer_vertices[:, :, 1] - origin_y
        z_offset = 2.0 * local_x + 1.0 * local_y**2
        layer_vertices[:, :, 2] = z_offset + 10.0 * float(layer_idx)

    vertices = np.concatenate(
        [layer1_vertices, layer2_vertices, layer3_vertices], axis=0
    )
    layer_sizes = [
        layer1_rows * layer1_cols,
        layer2_rows * layer2_cols,
        layer3_rows * layer3_cols,
    ]
    n_cells = vertices.shape[0]

    base_index = np.arange(n_cells, dtype=float)
    row_values = np.concatenate([
        np.array(
            [row + 1 for row in range(layer1_rows) for _ in range(layer1_cols)],
            dtype=float,
        ),
        np.array(
            [row + 1 for row in range(layer2_rows) for _ in range(layer2_cols)],
            dtype=float,
        ),
        np.array(
            [row + 1 for row in range(layer3_rows) for _ in range(layer3_cols)],
            dtype=float,
        ),
    ])
    col_values = np.concatenate([
        np.array(
            [col + 1 for _ in range(layer1_rows) for col in range(layer1_cols)],
            dtype=float,
        ),
        np.array(
            [col + 1 for _ in range(layer2_rows) for col in range(layer2_cols)],
            dtype=float,
        ),
        np.array(
            [col + 1 for _ in range(layer3_rows) for col in range(layer3_cols)],
            dtype=float,
        ),
    ])

    grid_data = np.zeros((4, n_days, n_cells), dtype=float)
    for day in range(n_days):
        grid_data[0, day, :] = base_index
        grid_data[1, day, :] = col_values
        grid_data[2, day, :] = row_values
        grid_data[3, day, :] = base_index + 30.0 * float(day)

    mean_z_values = np.mean(vertices[:, :, 2], axis=1)
    grid_data = np.concatenate(
        [grid_data, np.zeros((1, n_days, n_cells), dtype=float)], axis=0
    )
    for day in range(n_days):
        grid_data[4, day, :] = mean_z_values

    property_names = ["Cell Index", "Column", "Row", "Index + 30*Day", "Mean Z"]
    cell_names = [
        f"({row+1},{col+1},1)"
        for row in range(layer1_rows)
        for col in range(layer1_cols)
    ] + [
        f"({row+1},{col+1},2)"
        for row in range(layer2_rows)
        for col in range(layer2_cols)
    ] + [
        f"({row+1},{col+1},3)"
        for row in range(layer3_rows)
        for col in range(layer3_cols)
    ]

    conn_pairs = []
    # Same-layer neighbor connections inside layer 1.
    for row in range(layer1_rows):
        for col in range(layer1_cols):
            idx = row * layer1_cols + col
            if col < layer1_cols - 1:
                conn_pairs.append((idx, idx + 1))
            if row < layer1_rows - 1:
                conn_pairs.append((idx, idx + layer1_cols))
    # Same-layer neighbor connections inside layer 2.
    layer2_offset = layer_sizes[0]
    for row in range(layer2_rows):
        for col in range(layer2_cols):
            idx = layer2_offset + row * layer2_cols + col
            if col < layer2_cols - 1:
                conn_pairs.append((idx, idx + 1))
            if row < layer2_rows - 1:
                conn_pairs.append((idx, idx + layer2_cols))
    # Same-layer neighbor connections inside layer 3.
    layer3_offset = layer_sizes[0] + layer_sizes[1]
    for row in range(layer3_rows):
        for col in range(layer3_cols):
            idx = layer3_offset + row * layer3_cols + col
            if col < layer3_cols - 1:
                conn_pairs.append((idx, idx + 1))
            if row < layer3_rows - 1:
                conn_pairs.append((idx, idx + layer3_cols))

    # Cross-layer connections so that the middle layer shows both up and down triangles.
    for idx in range(min(layer_sizes[1], layer_sizes[2])):
        conn_pairs.append((layer2_offset + idx, idx))
        conn_pairs.append((layer2_offset + idx, layer3_offset + idx))

    connection_indices = np.asarray(conn_pairs, dtype=int).T
    n_connections = connection_indices.shape[1]
    connection_data = np.zeros((1, n_days, n_connections), dtype=float)
    for day in range(n_days):
        connection_data[0, day, :] = float(day + 1)

    wells = {
        "WELL-A,prod": np.asarray([0, layer2_offset + 1, layer3_offset + 2], dtype=int),
        "WELL-B,injw": np.asarray([5, layer2_offset + 6, layer3_offset + 7], dtype=int),
        "WELL-C,inj": np.asarray(
            [10, layer2_offset + n_cols + 10, layer3_offset + 2*n_cols + 10],
            dtype=int,
        ),
        "WELL-E,injg": np.asarray([16, layer3_offset + 15], dtype=int),
        "WELL-D,closed": np.asarray([24], dtype=int),
    }

    return DashMapPlot(
        vertices=vertices,
        layer_sizes=layer_sizes,
        grid_data=grid_data,
        property_names=property_names,
        cell_names=cell_names,
        connection_indices=connection_indices,
        connection_data=connection_data,
        connection_property_names=["Connectivity"],
        wells=wells,
        title="Step 2.2 - Interactive Map Controls",
        width=1000,
        height=700,
    )


def create_dash_template_app(map_plot=None):
    """Return the simplest example dashboard used for upgrade testing.

    The previous inline HTML/callback template was replaced by a thin wrapper
    so this module can serve as a launcher for example apps while the reusable
    Dash behavior lives in the shared dashboard modules.
    """
    del map_plot
    return create_step_4_generic_wrapper_working_example_app()


def build_step_3_demo_line_plot(n_days=15):
    """Build a line-plot object used by the Step 3 working example."""
    x_values = np.arange(np.datetime64("2026-01-01"), np.datetime64("2026-01-01") + int(n_days))
    t = np.arange(int(n_days), dtype=float)
    y_values = np.vstack(
        [
            200.0 + 15.0 * np.sin(0.45 * t),
            120.0 + 3.0 * t,
            0.18 + 0.03 * np.cos(0.35 * t),
        ]
    )
    return DashLinePlot(
        x_values=x_values,
        y_values=y_values,
        property_names=["Pressure", "Water Rate", "Water Cut"],
        secondary_y=[2],
        title="Step 3.1 - Line Plot Example",
        width=1000,
        height=420,
    )


def build_step_3_demo_scatter_plot(n_points=120, seed=7):
    """Build a scatter-plot object used by the Step 3 working example."""
    rng = np.random.default_rng(int(seed))
    x1 = rng.normal(loc=0.0, scale=1.0, size=int(n_points))
    y1 = 0.8 * x1 + rng.normal(loc=0.0, scale=0.35, size=int(n_points))
    x2 = rng.normal(loc=2.5, scale=0.9, size=int(n_points))
    y2 = -0.55 * x2 + 2.0 + rng.normal(loc=0.0, scale=0.3, size=int(n_points))
    return DashScatterPlot(
        scatter_data={
            "Permeability vs Porosity": np.column_stack([x1, y1]),
            "Pressure vs Saturation": np.column_stack([x2, y2]),
        },
        title="Step 3.2 - Scatter Plot Example",
        width=1000,
        height=420,
    )


def build_step_3_demo_table(n_rows=30):
    """Build a table object used by the Step 3 working example."""
    rows = int(n_rows)
    table_df = pd.DataFrame(
        {
            "Well": [f"W-{i+1:02d}" for i in range(rows)],
            "Type": ["prod" if i % 3 else "injw" for i in range(rows)],
            "Layer": [(i % 4) + 1 for i in range(rows)],
            "CumOil": np.round(1500.0 + 25.0 * np.arange(rows), 2),
            "CumWater": np.round(800.0 + 17.5 * np.arange(rows), 2),
        }
    )
    return DashTable(
        table_data=table_df,
        title="Step 3.3 - Table Example",
        page_size=10,
        width=1000,
        height=420,
    )


def create_step_4_generic_wrapper_working_example_app():
    """Create a working example using the generic dict-based multi-panel wrapper."""
    map_panels = {
        "Map A": build_step_2_2_demo_map_plot(n_rows=8, n_cols=12, n_days=4),
        "Map B": build_step_2_2_demo_map_plot(n_rows=7, n_cols=10, n_days=4),
    }

    line_panels = {
        "Line A": build_step_3_demo_line_plot(n_days=14),
        "Line B": DashLinePlot(
            x_values=np.arange(
                np.datetime64("2026-03-01"),
                np.datetime64("2026-03-01") + 14,
            ),
            y_values=np.vstack(
                [
                    150.0 + 10.0 * np.sin(0.30 * np.arange(14, dtype=float)),
                    100.0 + 4.0 * np.arange(14, dtype=float),
                    0.16 + 0.02 * np.cos(0.50 * np.arange(14, dtype=float)),
                ]
            ),
            property_names=["Pressure B", "Liquid Rate B", "Water Cut B"],
            secondary_y=[2],
            title="Line B",
            width=1000,
            height=380,
        ),
    }

    scatter_panels = {
        "Scatter A": build_step_3_demo_scatter_plot(n_points=100, seed=11),
        "Scatter B": DashScatterPlot(
            scatter_data={
                "Productivity Index": np.column_stack(
                    [
                        np.linspace(0.5, 20.0, 80),
                        4.0 + 0.8 * np.log(np.linspace(0.5, 20.0, 80)),
                    ]
                ),
                "GOR vs Pressure": np.column_stack(
                    [
                        np.linspace(150.0, 450.0, 80),
                        600.0 - 0.9 * np.linspace(150.0, 450.0, 80),
                    ]
                ),
            },
            title="Scatter B",
            width=1000,
            height=380,
        ),
    }

    table_panels = {
        "Table A": build_step_3_demo_table(n_rows=24),
        "Table B": DashTable(
            table_data=pd.DataFrame(
                {
                    "Well": [f"PX-{i+1:02d}" for i in range(18)],
                    "Type": ["prod" if i % 2 == 0 else "injw" for i in range(18)],
                    "Layer": [(i % 3) + 1 for i in range(18)],
                    "CumGas": np.round(120.0 + 13.2 * np.arange(18), 2),
                    "BHP": np.round(250.0 - 1.6 * np.arange(18), 2),
                }
            ),
            title="Table B",
            page_size=10,
            width=1000,
            height=380,
        ),
    }

    wrapper = DashMultiPanelDashboard(
        map_plots=map_panels,
        line_plots=line_panels,
        scatter_plots=scatter_panels,
        table_plots=table_panels,
        title="rsimpy Dash - Step 4 Generic Wrapper Example",
    )
    return wrapper.create_app()


def _get_common_sr3_grid_days(*sr3_readers):
    """Return the shared grid days after normalizing floating-point drift."""
    day_sets = []
    for reader in sr3_readers:
        rounded_days = np.round(np.asarray(reader.dates.get_days("grid"), dtype=float), 0)
        day_sets.append(set(rounded_days.tolist()))

    common_days = sorted(set.intersection(*day_sets))
    if not common_days:
        raise ValueError("No common grid days found between the SR3 files.")
    return np.asarray(common_days, dtype=float)


def create_sr3_working_example_app():
    """Create a runnable SR3-backed dashboard example app."""
    sr3_file = Path("tests/sr3/base_case_3a.sr3")
    sr3_compare_file = Path("tests/sr3/base_case_bo.sr3")
    if not sr3_file.exists():
        raise FileNotFoundError(f"SR3 example file not found: {sr3_file}")
    if not sr3_compare_file.exists():
        raise FileNotFoundError(f"SR3 example file not found: {sr3_compare_file}")

    sr3 = Sr3Reader(str(sr3_file))
    sr3_compare = Sr3Reader(str(sr3_compare_file))

    common_grid_days = _get_common_sr3_grid_days(sr3, sr3_compare)
    common_properties = [("matrix", "POR"), ("matrix", "PERMI"), ("matrix", "PERMJ"), ("matrix", "PRES")]

    # Create map tabs from base_case_3a
    map_obj_1 = sr3.plots.make_map(
        properties=[("matrix", "BLOCKDEPTH"), ("matrix", "POR")],
        days=sr3.dates.get_days("grid")[:3],
        title="Map A",
    )
    map_obj_2 = sr3.plots.make_map(
        properties=[("matrix", "PRES")],
        days=sr3.dates.get_days("grid")[:10],
        title="Map B",
    )

    # Create synchronized comparison maps using common properties and common days
    plots_a = PlotHandlerDash(sr3)
    map_compare_a = plots_a.make_map(
        properties=common_properties,
        days=common_grid_days,
        title="Base Case 3a",
    )
    plots_b = PlotHandlerDash(sr3_compare)
    map_compare_b = plots_b.make_map(
        properties=common_properties,
        days=common_grid_days,
        title="Base Case BO",
    )
    compare_map = DashMapCompare(
        map_plot_a=map_compare_a,
        map_plot_b=map_compare_b,
        label_a="3a",
        label_b="BO",
        title="Map Compare",
    )

    days = sr3.dates.get_days("well")
    line_obj = sr3.plots.make_line(
        series={
            "P11 Qo": ("well", "P11", "QO"),
            "P11 BHP": ("well", "P11", "BHP", True),
        },
        days=days,
        title="Line A",
    )
    scatter_obj = sr3.plots.make_scatter(
        data={
            "Qo vs BHP": ("well", "P11", "QO", "BHP"),
        },
        days=days,
        title="Scatter A",
    )
    table_obj = sr3.plots.make_table(
        series=[
            ("well", "P11", "NP"),
            ("well", "P11", "BHP"),
        ],
        days=days,
        title="Table A",
    )

    panel = sr3.plots.dashboard(
        maps={"Map A": map_obj_1, "Map B": map_obj_2, "Map Compare": compare_map},
        lines={"Line A": line_obj},
        scatter={"Scatter A": scatter_obj},
        table={"Table A": table_obj},
        title="SR3 Dash Working Example",
    )
    return panel.app


def build_map_compare_demo(n_rows=10, n_cols=15, n_days=5):
    """Build two DashMapPlot objects for the map comparison demo.

    Map A uses base values; Map B adds a small perturbation to the same data,
    simulating a comparison between two model runs.
    """
    rng = np.random.default_rng(42)
    layer_sizes_a = [n_rows * n_cols, (n_rows - 1) * (n_cols - 1)]
    layer_sizes_b = list(layer_sizes_a)

    def _make_verts(rows, cols):
        verts = _make_regular_grid_vertices(rows, cols)
        verts[:, :, 0] *= 10.0
        verts[:, :, 1] *= 10.0
        return verts

    verts_l1 = _make_verts(n_rows, n_cols)
    verts_l2 = _make_verts(n_rows - 1, n_cols - 1)
    vertices = np.concatenate([verts_l1, verts_l2], axis=0)
    n_cells = vertices.shape[0]

    base_data = np.zeros((3, n_days, n_cells), dtype=float)
    for d in range(n_days):
        base_data[0, d, :] = np.arange(n_cells, dtype=float) + 1.0
        base_data[1, d, :] = (np.arange(n_cells, dtype=float) % n_cols) + 1.0
        base_data[2, d, :] = 50.0 + 20.0 * float(d) + rng.uniform(0, 5, n_cells)

    perturbed_data = base_data.copy()
    perturbed_data[2] *= 1.0 + rng.uniform(-0.15, 0.15, (n_days, n_cells))

    property_names = ["Cell Index", "Column", "Pressure"]
    day_labels = [str(d * 30) for d in range(n_days)]

    map_a = DashMapPlot(
        vertices=vertices,
        layer_sizes=layer_sizes_a,
        grid_data=base_data,
        property_names=property_names,
        day_labels=day_labels,
        title="Base Case",
    )
    map_b = DashMapPlot(
        vertices=vertices,
        layer_sizes=layer_sizes_b,
        grid_data=perturbed_data,
        property_names=property_names,
        day_labels=day_labels,
        title="Perturbed Case",
    )
    return DashMapCompare(
        map_plot_a=map_a,
        map_plot_b=map_b,
        label_a="Base Case",
        label_b="Perturbed Case",
        title="Map Comparison Demo",
    )


def create_map_compare_app():
    """Create a map comparison Dash app using synthetic demo data."""
    return build_map_compare_demo().create_app()


def create_working_example_app(example="sr3"):
    """Create a named working example app.

    Parameters
    ----------
    example : str
        Supported values are "step4generic", "sr3", and "compare".
    """
    choice = str(example).strip().lower()
    if choice == "step4generic":
        return create_step_4_generic_wrapper_working_example_app()
    if choice == "sr3":
        return create_sr3_working_example_app()
    if choice == "compare":
        return create_map_compare_app()
    raise ValueError("example must be 'step4generic', 'sr3', or 'compare'.")


def _parse_cli_args():
    """Parse CLI args for choosing which demo app to run."""
    parser = argparse.ArgumentParser(
        description="Run rsimpy Dash working examples."
    )
    parser.add_argument(
        "--example",
        choices=["step4generic", "sr3", "compare"],
        default="sr3",
        help="Select which demo app to run.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable Dash debug mode.",
    )
    parser.add_argument(
        "--list-examples",
        action="store_true",
        help="Print available example names and exit.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_cli_args()
    if args.list_examples:
        print("\n".join(DEMO_EXAMPLES))
        raise SystemExit(0)
    demo_app = create_working_example_app(example=args.example)
    demo_app.run(debug=bool(args.debug))
