# Properties and Data Access

The Properties component manages time-series properties and provides the main interface for extracting data from SR3 files.

## Overview

The properties manager provides:
- Lists of available properties by element type
- Property metadata (units, descriptions)
- Property aliasing for convenience
- Data extraction interface
- CSV export capabilities

## Available Properties by Element Type

### Well Properties

Common well properties include:

**Operational:**
- `WELLSTATE` - Well state
- `WELLOPMO` - Operating mode
- `WHP` - Wellhead pressure
- `BHP` - Bottom hole pressure
- `BLOCKP` - Block pressure
- `BHTEMP`, `WHTEMP` - Temperatures
- `ONFRAC` - On time fraction
- `UPTIME` - Operating time

**Rates (at surface conditions):**
- `OILRATSC` (or `QO`) - Oil rate
- `GASRATSC` (or `QG`) - Gas rate
- `WATRATSC` (or `QW`) - Water rate
- `LIQRATSC` (or `QL`) - Liquid rate
- `INLRATSC` - Injection rate
- `WTGRATSC` - Water + gas rate

**Rates (at reservoir conditions):**
- `OILRATRC` (or `QO_RC`) - Oil rate
- `GASRATRC` (or `QG_RC`) - Gas rate
- `WATRATRC` (or `QW_RC`) - Water rate

**Cumulatives (volumes):**
- `OILVOLSC` (or `NP`) - Cumulative oil
- `GASVOLSC` (or `GP`) - Cumulative gas
- `WATVOLSC` (or `WP`) - Cumulative water
- `LIQVOLSC` - Cumulative liquid

**Compositional (moles and mass):**
- `OILMOLSC`, `GASMOLSC` - Molar rates
- `OILCMOLSC(COMP)` - Component molar rates
- `OILCMASSC(COMP)` - Component mass rates

### Group Properties

Groups have similar properties to wells but aggregated:
- All rate and cumulative properties
- `PMPRES`, `GIMPRES`, `WIMPRES` - Target pressures
- `NOPWING` - Number of operating wells

### Sector Properties

Sector-wide summaries:
- `OILSECSU` - Oil in place
- `GASSECSU` - Gas in place
- `WATSECSU` - Water in place
- `OILSECPRCM` - Cumulative oil produced
- `GASSECPRCM` - Cumulative gas produced
- `WATSECPRCM` - Cumulative water produced
- `PVCUMSEC` - Cumulative pore volume
- `AVGTEMPSEC` - Average temperature
- `VOIP` - Voidage oil in place (OOIP)

### Grid Properties

**Static properties:**
- `BLOCKDEPTH` - Cell depth
- `BLOCKPVOL` - Pore volume
- `BVOL` - Bulk volume
- `POR` - Porosity
- `PERMI`, `PERMJ`, `PERMK` - Permeability
- `NET/GROSS` - Net-to-gross ratio
- `KRSETN` - Rel-perm table number

**Dynamic properties:**
- `PRES` - Pressure
- `SO`, `SG`, `SW` - Saturations
- `POROS` - Modified porosity
- `VISO`, `VISG`, `VISW` - Viscosities
- `BO`, `BG`, `BW` - Formation volume factors
- `RS` - Solution gas-oil ratio
- `KRO`, `KRG`, `KRW` - Relative permeabilities

**Compositional:**
- `Z(COMP)` - Component mole fractions
- `X(COMP)` - Liquid phase mole fractions
- `Y(COMP)` - Vapor phase mole fractions

**Thermal (STARS):**
- `TEMP` - Temperature
- `STEAMSATSTEAM` - Steam saturation

### Special Properties

Simulation metadata:
- `ELAPSED` - Elapsed CPU time
- `DELTIME` - Timestep size
- `TSTEPCUM` - Cumulative timesteps
- `NCYCCUM` - Cumulative Newton iterations
- `MBERROR` - Material balance error
- `AVGIMPL` - Average implicitness
- `MEMUSAGE` - Memory usage

## Methods

### properties.get(element_type)

Get all available properties for an element type.

```python
# Get well properties
well_props = sr3.properties.get("well")
prop_names = list(well_props.keys())

# Get grid properties
grid_props = sr3.properties.get("grid")
```

**Parameters:**
- **element_type** (`str`): "well", "group", "sector", "layer", "grid", or "special"

**Returns:** `dict` - Dictionary with property names as keys

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# List all well properties
well_props = sr3.properties.get("well")
print(f"Available well properties ({len(well_props)}):")
for prop in list(well_props.keys())[:20]:  # First 20
    print(f"  {prop}")

# Check if specific property exists
if "OILRATSC" in well_props:
    print("\nOILRATS C property is available")
```

### properties.unit(property_name)

Get the unit string for a property.

```python
# Get unit for oil rate
unit = sr3.properties.unit("OILRATSC")
# Returns: "m3/day" (depends on current unit settings)

# Get unit for pressure
unit = sr3.properties.unit("BHP")
# Returns: "kgf/cm2" (depends on current unit settings)
```

**Parameters:**
- **property_name** (`str`): Name of the property

**Returns:** `str` - Unit string

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Check units for common properties
properties = ["BHP", "OILRATSC", "PRES", "VISO"]

print("Property units:")
for prop in properties:
    unit = sr3.properties.unit(prop)
    print(f"  {prop}: {unit}")

# Change units and check again
sr3.units.set_current(dimensionality="pressure", unit="psi")
sr3.units.set_current(dimensionality="well liquid volume", unit="bbl")

print("\nAfter unit change:")
for prop in ["BHP", "OILRATSC"]:
    unit = sr3.properties.unit(prop)
    print(f"  {prop}: {unit}")
```

### properties.set_alias(old, new, return_error=True)

Create an alias for a property name.

```python
# Create short aliases
sr3.properties.set_alias(old="OILRATSC", new="QO", return_error=False)
sr3.properties.set_alias(old="GASRATSC", new="QG", return_error=False)
sr3.properties.set_alias(old="WATRATSC", new="QW", return_error=False)

# Now you can use the shorter names
data = sr3.data.get("well", ["QO", "QG", "QW"], ["PROD-01"])
```

**Parameters:**
- **old** (`str`): Original property name
- **new** (`str`): Alias name
- **return_error** (`bool`, optional): Raise error if alias exists (default: True)

**Raises:**
- `ValueError`: If alias already exists (when return_error=True)

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Create convenient aliases
aliases = {
    "OILRATSC": "QO",
    "GASRATSC": "QG",
    "WATRATSC": "QW",
    "OILVOLSC": "NP",
    "GASVOLSC": "GP",
    "WATVOLSC": "WP"
}

for original, alias in aliases.items():
    sr3.properties.set_alias(old=original, new=alias, return_error=False)

# Use aliases in queries
data = sr3.data.get(
    element_type="well",
    properties=["QO", "QG", "QW", "NP"],
    elements=["PROD-01", "PROD-02"]
)
```

## Data Extraction

### data.get()

Main method for extracting time-series data.

```python
data = sr3.data.get(
    element_type="well",
    properties=["BHP", "OILRATSC"],
    elements=["PROD-01", "PROD-02"],
    days=[30, 90, 180, 365],
    active_only=True  # For grid properties
)
```

**Parameters:**
- **element_type** (`str`): Type of element ("well", "group", "sector", "grid", "special")
- **properties** (`str` or `list`): Property name(s) to extract
- **elements** (`str` or `list`, optional): Element name(s). For grid, can be "MATRIX" or "FRACTURE"
- **days** (`float`, `list`, or `None`, optional): Specific days to extract. If None, all available days
- **active_only** (`bool`, optional): For grid data, return only active cells (default: True)

**Returns:** `xarray.Dataset` - Multi-dimensional labeled dataset

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Extract well data
well_data = sr3.data.get(
    element_type="well",
    properties=["BHP", "OILRATSC", "WATRATSC"],
    elements=["PROD-01", "PROD-02", "PROD-03"],
    days=[30, 90, 180, 365, 730]
)

# Access data for specific well and day
bhp_prod01_day365 = well_data["BHP"].sel(element="PROD-01", day=365).values

# Access all days for one well
prod01_oil = well_data["OILRATSC"].sel(element="PROD-01")

# Get as pandas DataFrame
df = well_data.to_dataframe()
```

### Grid Data Extraction

```python
# Get grid pressure at specific day
grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO", "SG", "SW"],
    elements="MATRIX",
    days=365.0,
    active_only=True
)

# Access pressure array
pressure = grid_data["PRES"].sel(day=365.0).values
# Returns: 1D array of length n_active

# Get complete grid (including inactive cells)
grid_data_complete = sr3.data.get(
    element_type="grid",
    properties=["PRES"],
    elements="MATRIX",
    days=365.0,
    active_only=False
)

# Access pressure array
pressure_complete = grid_data_complete["PRES"].sel(day=365.0).values
# Returns: 1D array of length ni*nj*nk
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")
n_active = sr3.grid.get_size("n_active")

# Get final state
last_day = sr3.dates.get_days("grid")[-1]

grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO", "SG", "SW"],
    elements="MATRIX",
    days=last_day,
    active_only=True
)

# Extract arrays
pres = grid_data["PRES"].sel(day=last_day).values
so = grid_data["SO"].sel(day=last_day).values

print(f"Active cells: {len(pres)}")
print(f"Pressure range: {pres.min():.1f} to {pres.max():.1f}")
print(f"Oil saturation range: {so.min():.3f} to {so.max():.3f}")

# Calculate statistics
print(f"\nReservoir statistics:")
print(f"  Mean pressure: {np.mean(pres):.1f}")
print(f"  Mean oil saturation: {np.mean(so):.3f}")
```

### Special Data Extraction

```python
# Get simulation statistics
special_data = sr3.data.get(
    element_type="special",
    properties=["ELAPSED", "DELTIME", "MBERROR"],
    days=[30, 90, 180, 365]
)

# Access elapsed time
elapsed = special_data["ELAPSED"].sel(element="").values
# or
elapsed = special_data["ELAPSED"].values.flatten()
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get all available days
days = sr3.dates.get_days("special")

# Extract simulation performance metrics
special_data = sr3.data.get(
    element_type="special",
    properties=["ELAPSED", "DELTIME", "NCYCCUM", "MBERROR"]
)

# Plot simulation performance
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Elapsed CPU time
elapsed = special_data["ELAPSED"].values.flatten()
axes[0, 0].plot(days, elapsed / 3600)  # Convert to hours
axes[0, 0].set_xlabel("Simulation Days")
axes[0, 0].set_ylabel("Elapsed Time (hours)")
axes[0, 0].set_title("CPU Time")
axes[0, 0].grid(True)

# Timestep size
deltime = special_data["DELTIME"].values.flatten()
axes[0, 1].semilogy(days, deltime)
axes[0, 1].set_xlabel("Simulation Days")
axes[0, 1].set_ylabel("Timestep Size (days)")
axes[0, 1].set_title("Timestep Evolution")
axes[0, 1].grid(True)

# Newton iterations
ncyc = special_data["NCYCCUM"].values.flatten()
axes[1, 0].plot(days, ncyc)
axes[1, 0].set_xlabel("Simulation Days")
axes[1, 0].set_ylabel("Cumulative Newton Iterations")
axes[1, 0].set_title("Solver Performance")
axes[1, 0].grid(True)

# Material balance error
mberror = special_data["MBERROR"].values.flatten()
axes[1, 1].semilogy(days, np.abs(mberror))
axes[1, 1].set_xlabel("Simulation Days")
axes[1, 1].set_ylabel("Material Balance Error")
axes[1, 1].set_title("Material Balance")
axes[1, 1].grid(True)

plt.tight_layout()
plt.savefig("simulation_performance.png")
```

## CSV Export

### Direct Export from Dataset

```python
# Get data
data = sr3.data.get("well", ["BHP", "OILRATSC"], ["PROD-01", "PROD-02"])

# Export to CSV
data.to_csv("well_data.csv")
```

### Using data.to_csv() Method

```python
# Export with all parameters
sr3.data.to_csv(
    filename="production_data.csv",
    element_type="well",
    properties=["OILRATSC", "WATRATSC", "GASRATSC", "BHP"],
    elements=["PROD-01", "PROD-02", "PROD-03"]
)
```

**Parameters:**
- **filename** (`str`): Output file path
- **element_type** (`str`): Type of element
- **properties** (`str` or `list`): Property name(s)
- **elements** (`str` or `list`, optional): Element name(s)
- **days** (`float`, `list`, or `None`, optional): Specific days

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Export well production data
sr3.data.to_csv(
    filename="production_rates.csv",
    element_type="well",
    properties=["OILRATSC", "GASRATSC", "WATRATSC"],
    elements=["PROD-01", "PROD-02", "PROD-03"]
)

# Export cumulative production
sr3.data.to_csv(
    filename="cumulative_production.csv",
    element_type="well",
    properties=["OILVOLSC", "GASVOLSC", "WATVOLSC"],
    elements=["PROD-01", "PROD-02", "PROD-03"]
)

# Export grid data for specific day
last_day = sr3.dates.get_days("grid")[-1]

grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO", "SG", "SW"],
    elements="MATRIX",
    days=last_day
)

grid_data.to_csv("final_grid_state.csv")
```

## Working with xarray Datasets

The data returned by `sr3.data.get()` is an xarray Dataset, which provides powerful data manipulation capabilities.

### Selecting Data

```python
# Get data
data = sr3.data.get("well", ["BHP", "OILRATSC"], ["PROD-01", "PROD-02"])

# Select specific well
prod01 = data.sel(element="PROD-01")

# Select specific day
day365 = data.sel(day=365, method="nearest")

# Select specific property, well, and day
bhp_prod01_day365 = data["BHP"].sel(element="PROD-01", day=365).values

# Select multiple wells
producers = data.sel(element=["PROD-01", "PROD-02"])
```

### Aggregations

```python
# Mean over all wells
mean_bhp = data["BHP"].mean(dim="element")

# Max oil rate
max_rate = data["OILRATSC"].max(dim="day")

# Sum across wells (field total)
field_rate = data["OILRATSC"].sum(dim="element")

# Time average
time_avg_bhp = data["BHP"].mean(dim="day")
```

### Interpolation

```python
# Interpolate to specific days
new_days = [0, 100, 200, 300, 400, 500]
interpolated = data.interp(day=new_days)
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get well data
data = sr3.data.get(
    element_type="well",
    properties=["OILRATSC", "WATRATSC"],
    elements=["PROD-01", "PROD-02", "PROD-03", "PROD-04"]
)

# Calculate field totals
field_oil = data["OILRATSC"].sum(dim="element")
field_water = data["WATRATSC"].sum(dim="element")

# Calculate water cut
watercut = field_water / (field_oil + field_water) * 100

# Plot
fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# Field rates
axes[0].plot(field_oil.day, field_oil.values, label="Oil")
axes[0].plot(field_water.day, field_water.values, label="Water")
axes[0].set_xlabel("Days")
axes[0].set_ylabel("Rate (m³/day)")
axes[0].set_title("Field Production Rates")
axes[0].legend()
axes[0].grid(True)

# Water cut
axes[1].plot(watercut.day, watercut.values)
axes[1].set_xlabel("Days")
axes[1].set_ylabel("Water Cut (%)")
axes[1].set_title("Field Water Cut")
axes[1].grid(True)

plt.tight_layout()
plt.savefig("field_production.png")
```

## Practical Examples

### Example 1: Production Decline Analysis

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

well_name = "PROD-01"

# Get production history
data = sr3.data.get(
    element_type="well",
    properties=["OILRATSC", "BHP"],
    elements=[well_name]
)

# Extract arrays
days = data.day.values
qo = data["OILRATSC"].sel(element=well_name).values
bhp = data["BHP"].sel(element=well_name).values

# Calculate decline rate (%)
decline_rate = -np.diff(qo) / qo[:-1] * 100

# Plot
fig, axes = plt.subplots(2, 1, figsize=(10, 10))

# Oil rate
axes[0].plot(days, qo)
axes[0].set_xlabel("Days")
axes[0].set_ylabel("Oil Rate (m³/day)")
axes[0].set_title(f"{well_name} - Oil Rate")
axes[0].grid(True)

# BHP
axes[1].plot(days, bhp)
axes[1].set_xlabel("Days")
axes[1].set_ylabel("BHP (kgf/cm²)")
axes[1].set_title(f"{well_name} - Bottom Hole Pressure")
axes[1].grid(True)

plt.tight_layout()
plt.savefig(f"{well_name}_decline.png")
```

### Example 2: Compare Production by Platform

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Define platforms
platforms = {
    "Platform 1": ["PROD-01", "PROD-02", "PROD-03"],
    "Platform 2": ["PROD-04", "PROD-05", "PROD-06"],
    "Platform 3": ["PROD-07", "PROD-08", "PROD-09"]
}

# Get data for all wells
all_wells = [w for wells in platforms.values() for w in wells]

data = sr3.data.get(
    element_type="well",
    properties=["OILRATSC"],
    elements=all_wells
)

# Calculate platform totals
plt.figure(figsize=(12, 6))

for platform, wells in platforms.items():
    platform_data = data.sel(element=wells)
    platform_total = platform_data["OILRATSC"].sum(dim="element")

    plt.plot(platform_total.day, platform_total.values,
             marker='o', label=platform)

plt.xlabel("Days")
plt.ylabel("Oil Rate (m³/day)")
plt.title("Oil Production by Platform")
plt.legend()
plt.grid(True)
plt.savefig("platform_production.png")
```

### Example 3: Grid Property Evolution

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get selected timesteps
days_grid = sr3.dates.get_days("grid")
selected_days = [days_grid[0], days_grid[len(days_grid)//2], days_grid[-1]]

# Extract pressure for these days
pressures = []
for day in selected_days:
    grid_data = sr3.data.get(
        element_type="grid",
        properties=["PRES"],
        elements="MATRIX",
        days=day,
        active_only=True
    )
    pressures.append(grid_data["PRES"].sel(day=day).values)

# Plot histograms
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for i, (day, pres) in enumerate(zip(selected_days, pressures)):
    axes[i].hist(pres, bins=50, alpha=0.7, edgecolor='black')
    axes[i].set_xlabel("Pressure (kgf/cm²)")
    axes[i].set_ylabel("Frequency")
    axes[i].set_title(f"Day {day:.0f}")
    axes[i].grid(True, alpha=0.3)

plt.suptitle("Reservoir Pressure Distribution Evolution")
plt.tight_layout()
plt.savefig("pressure_evolution.png")
```

## Related Documentation

- [Elements & Hierarchy](elements.md)
- [Grid Operations](grid.md)
- [Dates & Times](dates.md)
- [Units Management](units.md)
- [SR3Reader Overview](overview.md)
