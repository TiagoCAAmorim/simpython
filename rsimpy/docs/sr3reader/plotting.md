# Interactive Visualization with Bokeh

The Plot component provides interactive visualization of grid properties using Bokeh, enabling dynamic exploration of 3D simulation data.

## Overview

The plotting manager provides:
- Interactive 2D property maps
- Multiple layer visualization
- Time animation across timesteps
- Customizable color palettes and scales
- Contour overlays
- Connection visualization
- Export to HTML for sharing

## Basic Map Plotting

### plot.plot_map()

Create an interactive map of grid properties.

```python
# Basic property map
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=365,
    layers=[50]
)

# Display in browser
from bokeh.plotting import show
show(panel)
```

**Parameters:**

**Required:**
- **element** (`str`): Grid element - `"matrix"` or `"fracture"`
- **property_name** (`str`): Property to plot (e.g., `"PRES"`, `"SO"`, `"PERMI"`)
- **days** (`float` or `list`): Simulation day(s) to plot
- **layers** (`int`, `list`, or `range`): Layer number(s) to plot

**Optional:**
- **width** (`int`): Plot width in pixels. Default: `800`
- **height** (`int`): Plot height in pixels. Default: `600`
- **title** (`str`): Plot title. Default: auto-generated
- **palette** (`str`): Color palette name. Default: `'Turbo'`
- **log_scale** (`bool`): Use logarithmic color scale. Default: `False`
- **color_limits** (`tuple`): Manual `(min, max)` for color scale. Default: auto
- **contour_step** (`float`): Add contour lines at this interval. Default: `None`
- **add_top** (`bool`): Add depth contours. Default: `False`
- **add_connections** (`bool`): Show grid connections. Default: `False`
- **out_of_range_colors** (`tuple`): Colors for values outside limits `(low, high)`. Default: `None`
- **nan_inf_color** (`str`): Color for NaN/Inf values. Default: `None`

**Returns:** Bokeh panel/layout object

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show, output_file

sr3 = Sr3Reader("simulation.sr3")

# Get available days
days = sr3.dates.get_days("grid")

# Create pressure map
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=days[-1],  # Last day
    layers=[89],
    width=1000,
    height=800,
    title="Reservoir Pressure",
    palette='Viridis',
    log_scale=False
)

# Save to HTML
output_file("pressure_map.html")
show(panel)
```

## Property Visualization

### Static Properties

Plot reservoir properties that don't change with time:

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show

sr3 = Sr3Reader("simulation.sr3")

# Permeability map (log scale)
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PERMI",
    days=0,
    layers=[89],
    palette='Turbo',
    log_scale=True,
    color_limits=(0.1, 500),
    title="I-Direction Permeability (md)"
)

show(panel)
```

### Dynamic Properties

Plot properties that change during simulation:

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show

sr3 = Sr3Reader("simulation.sr3")

# Get timesteps
days = sr3.dates.get_days("grid")

# Oil saturation at final day
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="SO",
    days=days[-1],
    layers=range(85, 95),  # Multiple layers
    title="Oil Saturation",
    palette='RdYlBu_r',  # Red-Yellow-Blue reversed
    color_limits=(0, 1)
)

show(panel)
```

## Time Animation

### Multiple Timesteps

Create animations by passing multiple days:

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show

sr3 = Sr3Reader("simulation.sr3")

# Get timesteps
days = sr3.dates.get_days("grid")

# Select every 10th day
plot_days = days[::10]

# Create animated pressure map
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=plot_days,
    layers=[89],
    width=1000,
    height=700,
    title="Pressure Evolution",
    palette='Plasma'
)

show(panel)
```

**Note:** The resulting panel includes a time slider for interactive exploration

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show, output_file

sr3 = Sr3Reader("simulation.sr3")

# Get quarterly snapshots
days = sr3.dates.get_days("grid")
quarterly_days = days[::90][:8]  # First 8 quarters

# Multi-layer, multi-time visualization
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="SO",
    days=quarterly_days,
    layers=range(85, 95, 2),  # Every other layer
    width=1200,
    height=800,
    title="Oil Saturation Evolution",
    palette='RdYlGn',
    color_limits=(0.2, 0.8),
    contour_step=0.1
)

output_file("saturation_evolution.html")
show(panel)
```

## Color Palettes

### Available Palettes

Bokeh provides many color palettes:

**Sequential:**
- `'Viridis'`, `'Plasma'`, `'Inferno'`, `'Magma'`, `'Cividis'`
- `'Greys'`, `'Blues'`, `'Greens'`, `'Reds'`, `'Purples'`
- `'Turbo'` (recommended for technical data)

**Diverging:**
- `'RdYlBu'`, `'RdYlBu_r'` (reversed)
- `'RdYlGn'`, `'RdYlGn_r'`
- `'Spectral'`, `'Spectral_r'`

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show
from bokeh.layouts import gridplot

sr3 = Sr3Reader("simulation.sr3")

# Compare different palettes
palettes = ['Viridis', 'Plasma', 'Turbo', 'RdYlBu']
panels = []

for palette in palettes:
    panel = sr3.plot.plot_map(
        element="matrix",
        property_name="PRES",
        days=365,
        layers=[89],
        width=400,
        height=400,
        palette=palette,
        title=f"Palette: {palette}"
    )
    panels.append(panel)

# Arrange in grid
grid = gridplot([panels[:2], panels[2:]])
show(grid)
```

## Logarithmic Scale

For properties spanning multiple orders of magnitude (e.g., permeability):

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show

sr3 = Sr3Reader("simulation.sr3")

# Permeability with log scale
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PERMI",
    days=0,
    layers=[89],
    log_scale=True,
    color_limits=(0.1, 1000),
    palette='Turbo',
    title="Permeability (log scale)"
)

show(panel)
```

## Contour Lines

Add contour lines to emphasize gradients:

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show

sr3 = Sr3Reader("simulation.sr3")

# Pressure with contours every 100 kPa
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=365,
    layers=[89],
    contour_step=100.0,
    palette='Viridis',
    title="Pressure with Contours"
)

show(panel)
```

## Depth Contours

Overlay structural depth contours:

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show

sr3 = Sr3Reader("simulation.sr3")

# Property map with depth contours
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PERMI",
    days=0,
    layers=range(85, 95),
    add_top=True,  # Add depth contours
    log_scale=True,
    palette='Turbo',
    title="Permeability with Structure"
)

show(panel)
```

## Connection Visualization

Show grid connections to understand connectivity:

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show

sr3 = Sr3Reader("simulation.sr3")

# Show connections
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PERMI",
    days=0,
    layers=[87],
    add_connections=True,
    log_scale=True,
    palette='Turbo',
    title="Permeability with Connections"
)

show(panel)
```

## Practical Examples

### Example 1: Drainage Pattern Visualization

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show, output_file

sr3 = Sr3Reader("simulation.sr3")

# Get timesteps
days = sr3.dates.get_days("grid")

# Select key timesteps
key_days = [days[0], days[len(days)//4], days[len(days)//2], days[-1]]

# Create saturation maps
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="SO",
    days=key_days,
    layers=range(85, 95),  # Main producing interval
    width=1400,
    height=900,
    title="Oil Drainage Pattern",
    palette='RdYlGn',
    color_limits=(0.15, 0.75),
    contour_step=0.1,
    add_top=True
)

output_file("drainage_pattern.html")
show(panel)

print("Interactive drainage pattern visualization saved to drainage_pattern.html")
```

### Example 2: Pressure Depletion Analysis

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show, output_file
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get timesteps
days = sr3.dates.get_days("grid")

# Monthly snapshots for first year
monthly_days = days[days <= 365][::30]

# Pressure depletion
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=monthly_days,
    layers=[89],
    width=1200,
    height=800,
    title="Pressure Depletion (Monthly)",
    palette='Plasma',
    contour_step=500,  # 500 kPa contours
    out_of_range_colors=('blue', 'red'),  # Low=blue, High=red
)

output_file("pressure_depletion.html")
show(panel)
```

### Example 3: Permeability Heterogeneity

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show, output_file
from bokeh.layouts import column

sr3 = Sr3Reader("simulation.sr3")

# Create maps for different permeability directions
properties = ['PERMI', 'PERMJ', 'PERMK']
panels = []

for prop in properties:
    panel = sr3.plot.plot_map(
        element="matrix",
        property_name=prop,
        days=0,
        layers=range(85, 95, 2),  # Every other layer
        width=1200,
        height=400,
        title=f"{prop} Distribution",
        palette='Turbo',
        log_scale=True,
        color_limits=(0.1, 500),
        add_top=True
    )
    panels.append(panel)

# Stack vertically
layout = column(*panels)

output_file("permeability_heterogeneity.html")
show(layout)
```

### Example 4: Dual-Porosity Comparison

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show, output_file
from bokeh.layouts import row

sr3 = Sr3Reader("simulation.sr3")

# Check if dual-porosity
grid_regions = sr3.elements.get("grid")
if "FRACTURE" not in grid_regions:
    print("Not a dual-porosity model")
    exit()

# Get last day
days = sr3.dates.get_days("grid")
last_day = days[-1]

# Create side-by-side comparison
panel_matrix = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=last_day,
    layers=range(85, 95),
    width=600,
    height=800,
    title="Matrix Pressure",
    palette='Viridis'
)

panel_fracture = sr3.plot.plot_map(
    element="fracture",
    property_name="PRES",
    days=last_day,
    layers=range(85, 95),
    width=600,
    height=800,
    title="Fracture Pressure",
    palette='Viridis'
)

# Side by side
layout = row(panel_matrix, panel_fracture)

output_file("dual_porosity_comparison.html")
show(layout)
```

### Example 5: Complete Reservoir Characterization

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show, output_file
from bokeh.layouts import gridplot

sr3 = Sr3Reader("simulation.sr3")

# Static properties
static_props = [
    ("PERMI", "I-Permeability (md)", True, (0.1, 500)),
    ("POR", "Porosity", False, (0.05, 0.35)),
    ("BLOCKDEPTH", "Depth (m)", False, None),
    ("BLOCKPVOL", "Pore Volume (m³)", True, None),
]

panels = []
for prop, title, log, limits in static_props:
    panel = sr3.plot.plot_map(
        element="matrix",
        property_name=prop,
        days=0,
        layers=[89],
        width=500,
        height=400,
        title=title,
        palette='Turbo',
        log_scale=log,
        color_limits=limits
    )
    panels.append(panel)

# Arrange in 2x2 grid
grid = gridplot([[panels[0], panels[1]], [panels[2], panels[3]]])

output_file("reservoir_characterization.html")
show(grid)
```

## Exporting Visualizations

### Save as HTML

```python
from bokeh.plotting import output_file, show

# Create plot
panel = sr3.plot.plot_map(...)

# Save to HTML file
output_file("output.html")
show(panel)
```

### Embed in Web Application

```python
from bokeh.embed import components

# Create plot
panel = sr3.plot.plot_map(...)

# Get script and div for embedding
script, div = components(panel)

# Use in web template
html_template = f"""
<html>
<head>
    <script src="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.js"></script>
</head>
<body>
    {div}
    {script}
</body>
</html>
"""
```

## Tips and Best Practices

### Performance

For large grids or many timesteps:

```python
# Reduce number of layers
layers = range(85, 95, 5)  # Every 5th layer

# Reduce number of timesteps
days = sr3.dates.get_days("grid")[::20]  # Every 20th timestep

# Use smaller plot size
width = 600
height = 500
```

### Color Scale Selection

**Linear scale:** Use for most properties with limited range
- Saturations (0-1)
- Porosity (0.05-0.40)
- Pressure (when range < 2 orders of magnitude)

**Logarithmic scale:** Use for properties spanning multiple orders
- Permeability (0.01-10,000 md)
- Transmissibility
- Rate properties with wide range

```python
# Check data range first
grid_data = sr3.data.get(
    element_type="grid",
    properties=["PERMI"],
    elements="MATRIX",
    days=0,
    active_only=True
)

perm = grid_data["PERMI"].sel(day=0).values
print(f"Permeability range: {perm.min():.2f} to {perm.max():.2f} md")

# If max/min > 100, use log scale
use_log = (perm.max() / perm.min()) > 100
```

### Layer Selection

For thick reservoirs, select representative layers:

```python
ni, nj, nk = sr3.grid.get_size("nijk")

# Top, middle, bottom
layers = [1, nk//2, nk]

# Evenly spaced
layers = list(range(1, nk+1, max(1, nk//10)))

# Main producing interval (user knowledge)
layers = range(85, 95)
```

### Handling NaN/Inf Values

```python
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=365,
    layers=[89],
    nan_inf_color='gray',  # Show inactive/invalid cells as gray
    out_of_range_colors=('blue', 'red')  # Low/high extremes
)
```

## Common Patterns

### Quick Pressure Check

```python
days = sr3.dates.get_days("grid")
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=days[-1],
    layers=[89],
    width=800,
    height=600
)
show(panel)
```

### Compare Multiple Properties

```python
from bokeh.layouts import column

properties = ["PRES", "SO", "PERMI"]
panels = [
    sr3.plot.plot_map(
        element="matrix",
        property_name=prop,
        days=365,
        layers=[89],
        width=1000,
        height=400,
        log_scale=(prop == "PERMI")
    )
    for prop in properties
]

show(column(*panels))
```

### Animation Loop

```python
# Get all timesteps
days = sr3.dates.get_days("grid")

# Create animation
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="SO",
    days=days,  # All days
    layers=[89],
    width=1000,
    height=800
)

show(panel)
# Use slider to animate through time
```

## Related Documentation

- [Properties & Data Access](properties.md)
- [Grid Operations](grid.md)
- [Dates & Time Management](dates.md)
- [SR3Reader Overview](overview.md)
