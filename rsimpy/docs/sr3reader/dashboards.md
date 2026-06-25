# Interactive Dashboards with Dash/Plotly

rsimpy provides interactive, web-based dashboards for visualizing SR3 simulation results using **Dash** and **Plotly**. Dashboards are highly responsive and support real-time interactivity: sliders for layer/day selection, log-scale toggles, color scale adjustment, and more.

## Quick Start: SR3 Wrapper

The simplest way to build dashboards is through the SR3 reader's `.plots.dashboard()` method.

```python
from rsimpy.cmg.sr3reader import Sr3Reader

# Open SR3 file
sr3 = Sr3Reader("simulation.sr3")

# Build map, line, scatter, and table visualizations
map_viz = sr3.plots.make_map(
    properties=["PRES", "POR"],  # Grid properties to visualize
    days=sr3.dates.get_days("grid"),  # Time steps
    title="Pressure & Porosity Map"
)

line_viz = sr3.plots.make_line(
    series={"P1 Production": ("well", "PROD-1", "QO"),
            "P1 BHP": ("well", "PROD-1", "BHP", True)},  # True = secondary Y-axis
    secondary_y=[1],  # Index of series on secondary axis
    title="Well Performance"
)

scatter_viz = sr3.plots.make_scatter(
    data={"Qo vs BHP": ("well", "PROD-1", "QO", "BHP")},
    title="Production vs Pressure"
)

# Assemble into a dashboard
dashboard = sr3.plots.dashboard(
    maps={"Base": map_viz},
    lines={"Production": line_viz},
    scatter={"Correlations": scatter_viz},
    title="SR3 Analysis Dashboard"
)

# Launch the web server
dashboard.run(host="127.0.0.1", port=8050, debug=False)
```

Then open **http://127.0.0.1:8050** in your browser.

## Component Methods

### `make_map()`

Create an interactive 2D map view of grid properties with optional well locations, connections, and contours.

```python
map_viz = sr3.plots.make_map(
    properties=["PRES"],                    # List of property names or ("element", "NAME") tuples
    days=None,                              # Days to include; None = all grid days
    title="Pressure",
    add_connections=False,                  # Show inter-cell connections
    add_wells=True,                         # Show well paths
    width=1000, height=700
)
```

**Features in UI:**
- Layer slider (1 to n_layers)
- Day slider (0 to n_days-1)
- Property dropdown
- Log scale checkbox
- Manual color limits (min/vmax inputs)
- Grid, connections, wells, contours toggles
- Palette selector

**Color Limits Behavior:**
- Leave both empty → auto from data
- Set only min → auto max (or padded if auto_max < user_min)
- Set only max → auto min (or padded if auto_min > user_max)
- Set both → use exact range

### `make_line()`

Create time-series line plots with optional secondary Y-axis.

```python
line_viz = sr3.plots.make_line(
    series={
        "Well A Oil Rate": ("well", "PROD-A", "QO"),
        "Well A BHP": ("well", "PROD-A", "BHP", True),  # True = secondary Y
    },
    days=None,                              # None = all well days
    secondary_y=[1],                        # Series indices on secondary axis
    title="Production & Pressure"
)
```

**Descriptor Format:**
- `("well", element_name, property_name)` — well time series
- `("well", element_name, property_name, True)` — well time series on secondary Y
- `("grid", "matrix"|"fracture", x_prop, y_prop)` — grid property scatter (use with `make_scatter`)

**Features in UI:**
- Log-Y and Log-Y2 toggles
- Legend with click-to-hide traces

### `make_scatter()`

Create XY scatter plots, optionally with X=Y reference line and equal axes.

```python
scatter_viz = sr3.plots.make_scatter(
    data={
        "Qo vs BHP": ("well", "PROD-1", "QO", "BHP"),
        "POR vs PERM": ("grid", "matrix", "POR", "PERMI"),
    },
    days=None,
    title="Correlations"
)
```

**Features in UI:**
- Property dropdown (all / per-dataset)
- Log-X, Log-Y toggles
- X = Y line checkbox (dashed red reference line)
- Equal axes checkbox (square plot area)

### `make_table()`

Create paginated data tables from time-series or grid properties.

```python
table_viz = sr3.plots.make_table(
    series=[
        ("well", "PROD-1", "QO"),
        ("well", "PROD-1", "BHP"),
    ],
    days=None,
    page_size=20,
    title="Well Data"
)
```

### `dashboard()`

Combine multiple visualizations into a grouped, tabbed interface.

```python
dashboard = sr3.plots.dashboard(
    maps={"Map A": map_a, "Map B": map_b},
    lines={"Production": line_viz},
    scatter={"Correlations": scatter_viz},
    table={"Well Data": table_viz},
    title="Multi-Panel SR3 Dashboard"
)

dashboard.run(host="127.0.0.1", port=8050, debug=False)
```

**Layout:**
- Top-level tabs: Maps | Line Plots | Scatter Plots | Tables
- Second level: one tab per named component
- Responsive grid layout (auto-scales with window)

## Advanced: Direct Component Usage

For custom dashboards, use the core plotting classes directly.

### `DashMapPlot` (from `rsimpy.common.plot_dash`)

Low-level map class for direct array input.

```python
from rsimpy.common.plot_dash import DashMapPlot
import numpy as np

# Define grid geometry
n_rows, n_cols, n_layers = 10, 15, 2
vertices = ...  # shape (n_cells, 4, 3) — corners of each cell in (x, y, z)
layer_sizes = [n_rows * n_cols, (n_rows - 1) * (n_cols - 1)]  # cells per layer

# Define data
n_days = 5
grid_data = np.random.rand(3, n_days, n_rows * n_cols + (n_rows-1)*(n_cols-1))  # (n_props, n_days, n_cells)

# Create map plot object
map_plot = DashMapPlot(
    vertices=vertices,
    layer_sizes=layer_sizes,
    grid_data=grid_data,
    property_names=["Pressure", "Saturation", "Permeability"],
    day_labels=["Day 0", "Day 30", "Day 60", "Day 90", "Day 120"],
    title="Custom Map"
)

# Generate static figure
fig = map_plot.create_map_figure(
    property_index=0,        # Pressure
    day_index=0,             # Day 0
    layer=1,                 # Layer 1 (1-indexed)
    palette="Turbo",         # Colorscale
    grid_log_scale=False,
    color_limits=[50, 200],  # Manual limits in original (non-log) space
    add_grid=True,
    add_wells=False
)
fig.show()
```

**Key Parameters:**
- `grid_log_scale` — Use log10 scale for colors
- `color_limits` — [vmin, vmax] in original data space (converted internally if log_scale=True)
- `nan_inf_color` — Color for NaN/infinite values (default: light gray)
- `add_connections`, `add_wells`, `add_contours` — Optional overlays

### `DashLineplot` and `DashScatterPlot`

```python
from rsimpy.common.plot_dash import DashLinePlot, DashScatterPlot
import numpy as np

# Line plot
x_dates = np.arange(np.datetime64("2025-01-01"), np.datetime64("2025-01-31"))
y_values = np.random.rand(2, len(x_dates))  # 2 series, 30 time points

line_plot = DashLinePlot(
    x_values=x_dates,
    y_values=y_values,
    property_names=["Series A", "Series B"],
    secondary_y=[1],  # Series B on secondary Y
    title="Time Series"
)

fig_line = line_plot.create_line_figure(log_scale=False)
fig_line.show()

# Scatter plot
scatter_data = {
    "Correlation 1": np.column_stack([np.random.rand(100), np.random.rand(100)]),
    "Correlation 2": np.column_stack([np.random.rand(50), np.random.rand(50)]),
}

scatter_plot = DashScatterPlot(scatter_data, title="Scatter")

fig_scatter = scatter_plot.create_scatter_figure(
    property_name="Correlation 1",
    show_xy_line=True,      # Red dashed X=Y reference
    equal_axes=True,        # Square axis ranges
    log_x=False, log_y=False
)
fig_scatter.show()
```

### Multi-Panel Dashboard (Low-Level)

```python
from rsimpy.common.plot_dashboard import DashMultiPanelDashboard

dashboard = DashMultiPanelDashboard(
    map_plots={"Map 1": map_plot_1, "Map 2": map_plot_2},
    line_plots={"Line 1": line_plot_1},
    scatter_plots={"Scatter 1": scatter_plot_1},
    title="Custom Multi-Panel"
)

app = dashboard.create_app()
app.run_server(debug=False, port=8050)
```

### Dual-Map Comparison

Compare two DashMapPlot objects side-by-side with synchronized axes and shared color scales.

```python
from rsimpy.common.plot_dashboard import DashMapCompare

compare = DashMapCompare(
    map_plot_a=base_map,
    map_plot_b=perturbed_map,
    label_a="Base Case",
    label_b="Perturbed Case",
    layout="side_by_side",  # or "stacked"
    title="Case Comparison"
)

app = compare.create_app(prefix="cmp")
app.run_server(debug=False, port=8050)
```

**Features:**
- Synchronized pan/zoom on both maps
- Shared color scale derived from combined data range
- Manual color limit UI
- Layout toggle (side-by-side ↔ stacked)

## Installation & Requirements

```bash
pip install dash plotly plotly-orca numpy pandas
```

## Performance Tips

1. **Limit data size**: Render fewer days or layers initially; users can filter in UI
2. **Use log scale sparingly**: Log color scales are slower on very large grids
3. **Disable overlays**: Wells, connections, and contours add rendering cost
4. **Run with debug=False**: Development mode has overhead
5. **Connection limits**: For >5000 connections, consider downsampling

## Common Issues

| Issue | Solution |
|-------|----------|
| "Port already in use" | Change port: `dashboard.run(port=8051)` |
| No wells appear | Check `add_wells=True` and verify well cell indices |
| Color scale inverted | Use `palette="Turbo_r"` for reversed colorscale |
| Slow on large grids | Disable connections/contours; use `add_grid=False` initially |
| Manual color limits ignored | Ensure both min and max are set (not just one) |

## See Also

- [SR3Reader Overview](overview.md)
- [Grid Operations](grid.md)
- [Plotting (Bokeh)](plotting.md)
