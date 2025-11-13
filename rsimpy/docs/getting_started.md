# Getting Started with rsimpy

## Installation

### From Source

```bash
git clone https://github.com/TiagoCAAmorim/simpython.git
cd simpython
pip install -e .
```

### Requirements

The package requires:
- Python 3.7+
- NumPy
- pandas
- xarray
- matplotlib
- bokeh (for interactive plotting)
- scipy (for interpolation and statistics)

## Basic Workflow

### 1. Reading SR3 Files

The most common use case is reading SR3 results files:

```python
from rsimpy.cmg.sr3reader import Sr3Reader

# Open an SR3 file
sr3 = Sr3Reader("path/to/simulation.sr3")

# Explore available elements
wells = sr3.elements.get("well").keys()
groups = sr3.elements.get("group").keys()

# Explore available properties
well_properties = sr3.properties.get("well").keys()
grid_properties = sr3.properties.get("grid").keys()
```

### 2. Extracting Time-Series Data

```python
# Get well data for specific timesteps
well_data = sr3.data.get(
    element_type="well",
    properties=["BHP", "OILRATSC", "WATRATSC"],
    elements=["PROD-01", "PROD-02"],
    days=[30, 90, 180, 365]
)

# Access data with xarray
bhp_prod01 = well_data["BHP"].sel(element="PROD-01").values

# Export to CSV
well_data.to_csv("well_production.csv")
```

### 3. Working with Grid Data

```python
# Get grid properties
ni, nj, nk = sr3.grid.get_size("nijk")
n_active = sr3.grid.get_size("n_active")

# Extract grid data for specific day
grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO", "SG", "SW"],
    elements="MATRIX",
    days=365.0
)

# Get pressure at day 365
pressure = grid_data["PRES"].sel(day=365.0).values
```

### 4. Grid File Operations

```python
from rsimpy.cmg.gridfile import GridFile

# Read a grid file
grid = GridFile("grid/PERM.inc")

# Get basic info
n_values = grid.get_number_values()
keyword = grid.get_keyword()

# Set grid dimensions
ni, nj, nk = 100, 50, 30
grid.set_shape([ni, nj, nk])

# Extract sub-grid
sub_grid = ((1, 50), (1, 25), (1, 10))
grid.write(file_path="grid/PERM_sub.inc", coord_range=sub_grid)
```

### 5. Template Processing

```python
from rsimpy.common.template import TemplateProcessor

# Create template with variables
template_text = """
PERMEABILITY <\var>perm[float,100,(uniform,10,500)]<var>
POROSITY <\var>por[float,0.25,(normal,0.25,0.05)]<var>
"""

# Generate experiments
processor = TemplateProcessor(
    template_path="template.dat",
    output_file_path="simulation.dat",
    n_samples=100
)

# Access generated samples
experiments = processor.experiments_table
```

## Common Patterns

### Converting Between Active and Complete Grids

```python
# Active cell index to complete cell index
complete_idx = sr3.grid.active2complete(active_cell_number)

# Complete cell index to active cell index
active_idx = sr3.grid.complete2active(complete_cell_number)
```

### Working with Element Hierarchy

```python
# Get parent group of a well
parent_group = sr3.elements.get_parent(
    element_type="well",
    element_name="PROD-01"
)

# Get all wells in a group
wells_in_group = sr3.elements.get_children(
    element_type="well",
    element_name="FIELD-PRO"
)
```

### Unit Conversions

```python
# Check current units
current_units = sr3.units.get_current()

# Change unit for a dimension
sr3.units.set_current(
    dimensionality="well liquid volume",
    unit="bbl"
)

# Get property unit string
unit_str = sr3.properties.unit("OILRATSC")  # Returns "bbl/day"
```

### Date and Time Operations

```python
from datetime import datetime

# Get available days
days = sr3.dates.get_days("well")

# Convert day to date
date = sr3.dates.day2date(day=365.0)

# Convert date to day
day = sr3.dates.date2day(date=datetime(2020, 1, 1))
```

## Tips and Best Practices

1. **Memory Management**: For large models, avoid loading all timesteps at once. Query specific days instead.

2. **Active vs Complete Grids**: Be aware of the difference between active cells (n_active) and complete grid (n_cells). Grid properties can be queried in either format using `active_only` parameter.

3. **Property Aliases**: Create aliases for frequently used properties:
   ```python
   sr3.properties.set_alias(old="OILRATSC", new="QO")
   ```

4. **Batch Operations**: Use parallel reads when extracting multiple independent properties or wells.

5. **Visualization**: Use the built-in plotting methods for quick visualization:
   ```python
   sr3.plot.plot_map(
       element="matrix",
       property_name="PRES",
       days=365,
       layers=[50]
   )
   ```

## Next Steps

- Explore [SR3Reader detailed documentation](sr3reader/overview.md)
- Learn about [DatReader for input files](datreader/overview.md)
- See [Template Processing](template.md) for uncertainty workflows
- Check [Quick Examples](quick_examples.md) for more use cases
