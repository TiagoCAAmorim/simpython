# SR3Reader Overview

The `Sr3Reader` class is the primary interface for reading and analyzing CMG SR3 results files. It provides comprehensive access to simulation results including time-series data, grid properties, element hierarchies, and metadata.

## Overview

SR3 files are binary results files produced by CMG simulators (IMEX, GEM, STARS). The Sr3Reader module provides:

- **Time-series data** for wells, groups, sectors, and grid properties
- **Element management** including hierarchies and relationships
- **Grid operations** for single and dual-porosity models
- **Unit conversions** with comprehensive unit system support
- **Date/time handling** with flexible querying
- **Coordinate extraction** and connection analysis
- **Relative permeability tables** and interpolation
- **Interactive visualization** with Bokeh
- **Data export** to CSV, pandas, and xarray formats

## Quick Start

```python
from rsimpy.cmg.sr3reader import Sr3Reader

# Open SR3 file
sr3 = Sr3Reader("simulation.sr3")

# Get well production data
well_data = sr3.data.get(
    element_type="well",
    properties=["BHP", "OILRATSC", "WATRATSC"],
    elements=["PROD-01", "PROD-02"],
    days=[30, 90, 180, 365]
)

# Access specific values
bhp_prod01 = well_data["BHP"].sel(element="PROD-01", day=365).values

# Export to CSV
well_data.to_csv("production_data.csv")
```

## Class: Sr3Reader

### Constructor

```python
sr3 = Sr3Reader(
    file_path="path/to/simulation.sr3",
    auto_read=True,
    verbose=False
)
```

**Parameters:**
- **file_path** (`str` or `Path`): Path to the SR3 file
- **auto_read** (`bool`, optional): Automatically read file upon initialization (default: True)
- **verbose** (`bool`, optional): Print progress messages (default: False)

**Attributes:**
- `file_path`: Path to the SR3 file
- `elements`: Element manager for hierarchies
- `properties`: Property manager for time-series
- `grid`: Grid manager for dimensions and coordinates
- `dates`: Date/time manager
- `units`: Unit conversion manager
- `data`: Data accessor for time-series queries
- `krel`: Relative permeability manager
- `connections`: Connection manager
- `plot`: Plotting interface (if available)

## Main Components

### 1. Elements ([detailed docs](elements.md))

Manage simulation elements and their hierarchies:

```python
# Get available elements
wells = sr3.elements.get("well").keys()
groups = sr3.elements.get("group").keys()

# Query hierarchy
parent = sr3.elements.get_parent("well", "PROD-01")
children = sr3.elements.get_children("well", "FIELD-PRO")
```

**Element Types:**
- `well`: Individual wells
- `group`: Well groups
- `sector`: Sectors/regions
- `layer`: Perforated layers
- `grid`: Grid regions (MATRIX, FRACTURE)

### 2. Properties ([detailed docs](properties.md))

Access available properties and their metadata:

```python
# Get available properties by element type
well_props = sr3.properties.get("well").keys()
grid_props = sr3.properties.get("grid").keys()

# Get property unit
unit_str = sr3.properties.unit("OILRATSC")  # "m3/day"

# Create alias for convenience
sr3.properties.set_alias(old="OILRATSC", new="QO")
```

**Property Categories:**
- Well properties: BHP, rates, cumulatives, composition
- Group properties: Aggregated well data
- Sector properties: Regional summaries, OOIP, OGIP
- Grid properties: Pressure, saturation, composition, fluid properties
- Special properties: Timestep info, solver statistics

### 3. Grid ([detailed docs](grid.md))

Grid information and cell indexing:

```python
# Get grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")
n_active = sr3.grid.get_size("n_active")
n_cells = sr3.grid.get_size("n_cells")

# Convert between active and complete numbering
complete_idx = sr3.grid.active2complete([1, 2, 3])
active_idx = sr3.grid.complete2active([100, 200, 300])
```

**Grid Features:**
- Single and dual-porosity support
- Active vs complete cell indexing
- Coordinate extraction
- 2phi2k (dual-porosity/dual-permeability) support

### 4. Data Access ([detailed docs](properties.md))

Extract time-series and grid data:

```python
# Well data
well_data = sr3.data.get(
    element_type="well",
    properties=["BHP", "OILRATSC"],
    elements=["PROD-01", "PROD-02"],
    days=[30, 90, 180, 365]
)

# Grid data
grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO"],
    elements="MATRIX",
    days=365.0,
    active_only=True
)

# Special simulation data
special_data = sr3.data.get(
    element_type="special",
    properties="ELAPSED",
    days=[30, 90, 180, 365]
)
```

**Data Features:**
- Returns xarray Dataset for easy manipulation
- Supports multiple properties and elements
- Flexible day/timestep selection
- CSV export capability

### 5. Dates and Times ([detailed docs](dates.md))

Handle simulation dates and timesteps:

```python
from datetime import datetime

# Get available timesteps
days = sr3.dates.get_days("well")
dates = sr3.dates.get_dates("well")
timesteps = sr3.dates.get_timesteps()

# Convert between days and dates
date = sr3.dates.day2date(day=365.0)
day = sr3.dates.date2day(date=datetime(2020, 1, 1))
```

**Date Features:**
- Support for different element types (may have different output frequencies)
- Conversion between simulation days and calendar dates
- Timestep management

### 6. Units ([detailed docs](units.md))

Manage unit conversions:

```python
# Get current units
units = sr3.units.get_current()
pressure_unit = sr3.units.get_current("pressure")

# Change units
sr3.units.set_current(dimensionality="pressure", unit="psi")
sr3.units.set_current(dimensionality="well liquid volume", unit="bbl")

# Add custom unit
sr3.units.add(old="m3", new="Mbbl", gain=6.2898, offset=0.0)
```

**Unit Features:**
- Comprehensive unit system covering all CMG dimensions
- Custom unit definitions
- Automatic conversion for data queries
- Unit-aware property names

### 7. Coordinates and Connections ([detailed docs](coordinates.md))

Extract grid geometry and connections:

```python
# Get cell coordinates
coords = sr3.grid.coordinates.get(cells=[1, 2, 3], face='K-')

# Get connections
connections = sr3.connections.get_connections()
trans = sr3.connections.get_transmissibilities()

# Plot faces
axes = sr3.grid.coordinates.plot_planes(coords)
```

**Coordinate Features:**
- Corner-point geometry extraction
- Face coordinates (I+, I-, J+, J-, K+, K-)
- Connection identification
- Transmissibility calculations

### 8. Relative Permeability ([detailed docs](krel.md))

Access and interpolate relative permeability tables:

```python
# Get kr table
krel_table = sr3.krel.get(table_number=1)

# Interpolate values
krw = sr3.krel.get_krw(table_number=1, sw=0.5)
krg = sr3.krel.get_krg(table_number=1, sg=0.3)
kro = sr3.krel.get_kro(table_number=1, sw=0.5, sg=0.2)

# Export table
krel_table.to_csv("krel_table_1.csv")
```

**Krel Features:**
- Water-oil and gas-liquid systems
- Stone's method for three-phase systems
- Interpolation for arbitrary saturations
- CSV export

### 9. Plotting ([detailed docs](plotting.md))

Interactive visualization with Bokeh:

```python
# Plot grid property
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=365,
    layers=[50, 60, 70],
    palette='Viridis',
    log_scale=False,
    add_connections=True
)

# Display
from bokeh.plotting import show
show(panel)
```

**Plotting Features:**
- Interactive Bokeh maps
- Multiple timesteps and layers
- Contour lines
- Connection visualization
- Customizable color scales and palettes

## Supported Simulators

### IMEX (Black Oil)
- Single and dual-porosity models
- Oil, gas, and water phases
- Components: oil, gas, water

### GEM (Compositional)
- Single and dual-porosity models
- Multiple components
- Full compositional tracking
- EOS calculations

### STARS (Thermal)
- Thermal properties
- Steam and heat tracking
- Geomechanics (if enabled)

## Data Structure

SR3Reader returns data in xarray Dataset format, which provides:

- **Labeled dimensions**: Easy indexing by element name, property, day
- **Coordinate-based selection**: `.sel()` method for intuitive querying
- **Vectorized operations**: Apply operations across dimensions
- **Metadata preservation**: Units and attributes maintained
- **Export options**: CSV, NetCDF, pandas DataFrame

Example xarray usage:
```python
# Get data
data = sr3.data.get("well", ["BHP", "OILRATSC"], ["PROD-01", "PROD-02"])

# Select specific well and day
prod01_bhp = data["BHP"].sel(element="PROD-01", day=365).values

# Aggregate operations
mean_bhp = data["BHP"].mean(dim="day")
max_rate = data["OILRATSC"].max(dim="element")

# Export subset
data.sel(element="PROD-01").to_dataframe().to_csv("prod01.csv")
```

## Performance Tips

1. **Query specific days**: Avoid loading all timesteps when you only need specific dates
2. **Use active_only=True**: For grid data, active cells are typically much smaller than complete grid
3. **Batch queries**: Request multiple properties/elements in a single call
4. **Property aliases**: Use shorter names for frequently accessed properties
5. **Memory management**: Close or delete Sr3Reader objects when done with large files

## Common Workflows

### Production Data Analysis
```python
# Get well production history
prod_data = sr3.data.get(
    element_type="well",
    properties=["OILRATSC", "WATRATSC", "GASRATSC", "BHP"],
    elements=["PROD-01", "PROD-02", "PROD-03"]
)

# Calculate cumulative production manually or use NP property
cum_data = sr3.data.get(
    element_type="well",
    properties=["NP", "WP", "GP"],
    elements=["PROD-01", "PROD-02", "PROD-03"]
)

# Export for analysis
prod_data.to_csv("production_rates.csv")
cum_data.to_csv("cumulative_production.csv")
```

### Grid Property Extraction
```python
# Get final state
last_day = sr3.dates.get_days("grid")[-1]

grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO", "SG", "SW"],
    elements="MATRIX",
    days=last_day,
    active_only=True
)

# Reshape to grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")
pressure = grid_data["PRES"].sel(day=last_day).values
# Note: This is active cells only, may need padding for complete grid
```

### History Matching Preparation
```python
# Extract observed wells at specific dates
import datetime

dates = [
    datetime.datetime(2020, 1, 1),
    datetime.datetime(2020, 4, 1),
    datetime.datetime(2020, 7, 1),
]

days = [sr3.dates.date2day(d) for d in dates]

obs_data = sr3.data.get(
    element_type="well",
    properties=["OILRATSC", "WATRATSC", "BHP"],
    elements=["OBS-01", "OBS-02"],
    days=days
)

obs_data.to_csv("observed_data_for_matching.csv")
```

## Error Handling

Common exceptions and their meanings:

- **FileNotFoundError**: SR3 file doesn't exist
- **KeyError**: Requested property or element not found
- **ValueError**: Invalid parameter values (e.g., wrong element type)
- **IndexError**: Invalid cell numbers or indices

Example error handling:
```python
try:
    sr3 = Sr3Reader("simulation.sr3")
    data = sr3.data.get("well", "INVALID_PROP", "WELL-01")
except FileNotFoundError:
    print("SR3 file not found")
except KeyError as e:
    print(f"Property or element not found: {e}")
```

## Module Documentation

For detailed information on specific components:

- [Elements & Hierarchy](elements.md)
- [Properties & Data Access](properties.md)
- [Grid Operations](grid.md)
- [Dates & Times](dates.md)
- [Units Management](units.md)
- [Coordinates & Connections](coordinates.md)
- [Relative Permeability](krel.md)
- [Visualization & Plotting](plotting.md)

## Related Documentation

- [Getting Started](../getting_started.md)
- [Quick Examples](../quick_examples.md)
- [GridFile Module](../gridfile.md)
