# Grid Operations

The Grid component provides access to grid dimensions, cell indexing, and coordinate transformations for both single and dual-porosity models.

## Overview

The grid manager provides:
- Grid dimension queries
- Active/complete cell index conversions
- Support for 2phi2k (dual-porosity/dual-permeability) models
- Coordinate extraction interface
- Grid property access

## Grid Dimensions

### get_size(size_type)

Get various grid size parameters.

```python
# Get IJK dimensions
ni, nj, nk = sr3.grid.get_size("nijk")

# Get number of active cells
n_active = sr3.grid.get_size("n_active")

# Get total number of cells (including inactive)
n_cells = sr3.grid.get_size("n_cells")
```

**Parameters:**
- **size_type** (`str`): Type of size to retrieve

**Size Types:**
- `"nijk"` - Returns tuple `(NI, NJ, NK)` - Grid dimensions
- `"n_active"` - Returns `int` - Number of active cells (matrix + fracture)
- `"n_cells"` - Returns `int` - Total cells including inactive (ni × nj × nk × n_regions)
- `"n_active_matrix"` - Returns `int` - Active matrix cells (2phi2k only)
- `"n_active_fracture"` - Returns `int` - Active fracture cells (2phi2k only)

**Returns:** `tuple` or `int` depending on size_type

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")
print(f"Grid dimensions: {ni} × {nj} × {nk}")

# Get active cells
n_active = sr3.grid.get_size("n_active")
n_total = ni * nj * nk
inactive = n_total - n_active

print(f"Active cells: {n_active:,}")
print(f"Inactive cells: {inactive:,}")
print(f"Activity: {n_active/n_total*100:.1f}%")

# Check for dual-porosity
try:
    n_matrix = sr3.grid.get_size("n_active_matrix")
    n_fracture = sr3.grid.get_size("n_active_fracture")

    print("\nDual-porosity model:")
    print(f"  Matrix cells: {n_matrix:,}")
    print(f"  Fracture cells: {n_fracture:,}")
except:
    print("\nSingle-porosity model")
```

## Cell Index Conversion

### active2complete(active_indices)

Convert active cell indices to complete grid indices.

```python
# Single cell
complete_idx = sr3.grid.active2complete(1)

# Multiple cells
complete_indices = sr3.grid.active2complete([1, 2, 3, 4, 5])
```

**Parameters:**
- **active_indices** (`int` or `list`): Active cell index/indices (1-indexed)

**Returns:** `int` or `list` - Complete grid index/indices

**Note:**
- Active cells are numbered 1 to n_active
- Complete cells are numbered 1 to (ni × nj × nk)
- Inactive cells have no corresponding active index

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Convert first 10 active cells
active_indices = list(range(1, 11))
complete_indices = sr3.grid.active2complete(active_indices)

print("Active -> Complete mapping:")
for act, comp in zip(active_indices, complete_indices):
    print(f"  Active {act:4d} -> Complete {comp:5d}")

# Get properties for specific active cells
last_day = sr3.dates.get_days("grid")[-1]

grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES"],
    elements="MATRIX",
    days=last_day,
    active_only=True
)

# First 5 active cells pressures
pressure = grid_data["PRES"].sel(day=last_day).values
print(f"\nFirst 5 active cells pressure:")
for i in range(5):
    print(f"  Active {i+1}: {pressure[i]:.1f}")
```

### complete2active(complete_indices)

Convert complete grid indices to active cell indices.

```python
# Single cell
active_idx = sr3.grid.complete2active(100)

# Multiple cells
active_indices = sr3.grid.complete2active([100, 200, 300])
```

**Parameters:**
- **complete_indices** (`int` or `list`): Complete grid index/indices (1-indexed)

**Returns:** `int` or `list` - Active cell index/indices (0 for inactive cells)

**Note:**
- Returns 0 for inactive cells
- Use this to filter out inactive cells from complete grid arrays

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")

# Check which cells in a layer are active
layer_k = 50
layer_cells = []

for j in range(1, nj + 1):
    for i in range(1, ni + 1):
        # Calculate complete cell index
        cell_idx = (layer_k - 1) * ni * nj + (j - 1) * ni + i
        layer_cells.append(cell_idx)

# Convert to active indices
active_indices = sr3.grid.complete2active(layer_cells)

# Count active cells in layer
n_active_in_layer = sum(1 for idx in active_indices if idx > 0)
print(f"Layer {layer_k}:")
print(f"  Total cells: {len(layer_cells)}")
print(f"  Active cells: {n_active_in_layer}")
print(f"  Activity: {n_active_in_layer/len(layer_cells)*100:.1f}%")

# Get active cell indices (non-zero)
active_in_layer = [idx for idx in active_indices if idx > 0]
print(f"  Active indices: {active_in_layer[:10]}..." if len(active_in_layer) > 10 else active_in_layer)
```

## Grid Properties

### Accessing Grid Data

Grid properties can be accessed in two modes:

#### Active Cells Only (Default)

```python
# Get active cells only
grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO"],
    elements="MATRIX",
    days=365,
    active_only=True  # Default
)

# Returns array of length n_active
pressure = grid_data["PRES"].sel(day=365).values
print(f"Array length: {len(pressure)} (n_active)")
```

#### Complete Grid (Including Inactive)

```python
# Get complete grid
grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO"],
    elements="MATRIX",
    days=365,
    active_only=False
)

# Returns array of length ni*nj*nk
pressure = grid_data["PRES"].sel(day=365).values
print(f"Array length: {len(pressure)} (ni*nj*nk)")

# Inactive cells typically have zero or special values
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get dimensions
ni, nj, nk = sr3.grid.get_size("nijk")
n_active = sr3.grid.get_size("n_active")

last_day = sr3.dates.get_days("grid")[-1]

# Get active cells data
active_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO"],
    elements="MATRIX",
    days=last_day,
    active_only=True
)

pres_active = active_data["PRES"].sel(day=last_day).values
so_active = active_data["SO"].sel(day=last_day).values

print(f"Active data:")
print(f"  Length: {len(pres_active)}")
print(f"  Pressure range: {pres_active.min():.1f} to {pres_active.max():.1f}")

# Get complete grid data
complete_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO"],
    elements="MATRIX",
    days=last_day,
    active_only=False
)

pres_complete = complete_data["PRES"].sel(day=last_day).values
so_complete = complete_data["SO"].sel(day=last_day).values

print(f"\nComplete grid data:")
print(f"  Length: {len(pres_complete)}")
print(f"  Non-zero cells: {np.count_nonzero(pres_complete)}")
```

## Dual-Porosity Models (2phi2k)

For dual-porosity/dual-permeability models, cells are duplicated for matrix and fracture.

### Grid Structure

```
Complete cell numbering:
- Cells 1 to ni*nj*nk: Matrix region
- Cells ni*nj*nk+1 to 2*ni*nj*nk: Fracture region

Active cell numbering:
- Cells 1 to n_active_matrix: Active matrix cells
- Cells n_active_matrix+1 to n_active: Active fracture cells
```

### Accessing Matrix and Fracture Data

```python
# Matrix data
matrix_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO"],
    elements="MATRIX",
    days=365
)

# Fracture data
fracture_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO"],
    elements="FRACTURE",
    days=365
)

# Both regions
both_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO"],
    elements=["MATRIX", "FRACTURE"],
    days=365
)
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

sr3 = Sr3Reader("dual_porosity.sr3")

# Check if dual-porosity
grid_regions = sr3.elements.get("grid")
if "FRACTURE" not in grid_regions:
    print("Not a dual-porosity model")
    exit()

# Get grid sizes
ni, nj, nk = sr3.grid.get_size("nijk")
n_matrix = sr3.grid.get_size("n_active_matrix")
n_fracture = sr3.grid.get_size("n_active_fracture")

print(f"Dual-porosity model: {ni}×{nj}×{nk}")
print(f"  Matrix active: {n_matrix}")
print(f"  Fracture active: {n_fracture}")

# Get final state
last_day = sr3.dates.get_days("grid")[-1]

# Extract data for both regions
data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "SO"],
    elements=["MATRIX", "FRACTURE"],
    days=last_day,
    active_only=True
)

pres = data["PRES"].sel(day=last_day).values
so = data["SO"].sel(day=last_day).values

# Separate matrix and fracture
pres_matrix = pres[:n_matrix]
pres_fracture = pres[n_matrix:]

so_matrix = so[:n_matrix]
so_fracture = so[n_matrix:]

# Compare
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Pressure comparison
axes[0, 0].hist(pres_matrix, bins=50, alpha=0.7, label='Matrix')
axes[0, 0].hist(pres_fracture, bins=50, alpha=0.7, label='Fracture')
axes[0, 0].set_xlabel("Pressure")
axes[0, 0].set_title("Pressure Distribution")
axes[0, 0].legend()
axes[0, 0].grid(True)

# Saturation comparison
axes[0, 1].hist(so_matrix, bins=50, alpha=0.7, label='Matrix')
axes[0, 1].hist(so_fracture, bins=50, alpha=0.7, label='Fracture')
axes[0, 1].set_xlabel("Oil Saturation")
axes[0, 1].set_title("Saturation Distribution")
axes[0, 1].legend()
axes[0, 1].grid(True)

# Scatter plots
axes[1, 0].scatter(pres_matrix, pres_fracture, alpha=0.5, s=1)
axes[1, 0].plot([pres.min(), pres.max()], [pres.min(), pres.max()], 'r--')
axes[1, 0].set_xlabel("Matrix Pressure")
axes[1, 0].set_ylabel("Fracture Pressure")
axes[1, 0].set_title("Pressure Comparison")
axes[1, 0].grid(True)

axes[1, 1].scatter(so_matrix, so_fracture, alpha=0.5, s=1)
axes[1, 1].plot([0, 1], [0, 1], 'r--')
axes[1, 1].set_xlabel("Matrix So")
axes[1, 1].set_ylabel("Fracture So")
axes[1, 1].set_title("Saturation Comparison")
axes[1, 1].grid(True)

plt.tight_layout()
plt.savefig("dual_porosity_comparison.png")
```

## Reshaping Grid Data

To reshape 1D arrays back to 3D grid:

```python
# For active cells (requires handling inactive cells)
# This is more complex and typically requires building a mapping

# For complete grid
ni, nj, nk = sr3.grid.get_size("nijk")

# Get complete grid data
grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES"],
    elements="MATRIX",
    days=365,
    active_only=False
)

pressure_1d = grid_data["PRES"].sel(day=365).values

# Reshape to 3D (K, J, I) - Fortran order
pressure_3d = pressure_1d.reshape((nk, nj, ni), order='F')

# Extract layer 50
layer_50 = pressure_3d[49, :, :]  # 0-indexed
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")

# Get depth (static property)
depth_data = sr3.data.get(
    element_type="grid",
    properties=["BLOCKDEPTH"],
    elements="MATRIX",
    days=0,
    active_only=False
)

depth_1d = depth_data["BLOCKDEPTH"].sel(day=0).values

# Reshape to 3D
depth_3d = depth_1d.reshape((nk, nj, ni), order='F')

# Extract and plot a specific layer
layer_k = 50
layer_depth = depth_3d[layer_k-1, :, :]

plt.figure(figsize=(10, 8))
plt.imshow(layer_depth, aspect='auto', cmap='terrain_r')
plt.colorbar(label='Depth (m)')
plt.xlabel('I')
plt.ylabel('J')
plt.title(f'Layer {layer_k} Depth')
plt.savefig(f'layer_{layer_k}_depth.png')

# Plot vertical cross-section (I-K plane at J=nj//2)
j_section = nj // 2
section = depth_3d[:, j_section, :]

plt.figure(figsize=(12, 6))
plt.imshow(section, aspect='auto', cmap='terrain_r', origin='lower')
plt.colorbar(label='Depth (m)')
plt.xlabel('I')
plt.ylabel('K')
plt.title(f'Vertical Section at J={j_section}')
plt.savefig(f'section_j{j_section}.png')
```

## Practical Examples

### Example 1: Calculate Bulk Volume Statistics

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get bulk volumes (active cells only)
grid_data = sr3.data.get(
    element_type="grid",
    properties=["BVOL", "POR", "BLOCKPVOL"],
    elements="MATRIX",
    days=0,
    active_only=True
)

bvol = grid_data["BVOL"].sel(day=0).values
por = grid_data["POR"].sel(day=0).values
pv = grid_data["BLOCKPVOL"].sel(day=0).values

print("Reservoir Volume Statistics:")
print(f"  Total bulk volume: {np.sum(bvol):,.0f} m³")
print(f"  Total pore volume: {np.sum(pv):,.0f} m³")
print(f"  Average porosity: {np.mean(por):.3f}")
print(f"  Porosity range: {np.min(por):.3f} to {np.max(por):.3f}")
```

### Example 2: Calculate Oil in Place

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get initial state
grid_data = sr3.data.get(
    element_type="grid",
    properties=["BLOCKPVOL", "SO", "BO"],
    elements="MATRIX",
    days=0,
    active_only=True
)

pv = grid_data["BLOCKPVOL"].sel(day=0).values
so = grid_data["SO"].sel(day=0).values
bo = grid_data["BO"].sel(day=0).values

# Calculate OOIP (stock tank volumes)
ooip_per_cell = pv * so / bo
ooip_total = np.sum(ooip_per_cell)

print(f"Original Oil in Place:")
print(f"  Total: {ooip_total:,.0f} m³")
print(f"  Million barrels: {ooip_total * 6.2898e-6:,.1f} MMbbl")
```

### Example 3: Identify High Permeability Zones

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get permeability
grid_data = sr3.data.get(
    element_type="grid",
    properties=["PERMI", "PERMJ", "PERMK"],
    elements="MATRIX",
    days=0,
    active_only=True
)

permi = grid_data["PERMI"].sel(day=0).values
permj = grid_data["PERMJ"].sel(day=0).values
permk = grid_data["PERMK"].sel(day=0).values

# Calculate geometric mean
perm_avg = (permi * permj * permk) ** (1/3)

# Find high perm zones (top 10%)
threshold = np.percentile(perm_avg, 90)
high_perm_cells = np.where(perm_avg > threshold)[0]

print(f"Permeability Analysis:")
print(f"  Mean permeability: {np.mean(perm_avg):.1f} md")
print(f"  Median permeability: {np.median(perm_avg):.1f} md")
print(f"  90th percentile: {threshold:.1f} md")
print(f"  High perm cells: {len(high_perm_cells)} ({len(high_perm_cells)/len(perm_avg)*100:.1f}%)")

# Convert to complete grid indices
n_active = sr3.grid.get_size("n_active")
active_indices = high_perm_cells + 1  # Convert to 1-indexed
complete_indices = sr3.grid.active2complete(active_indices.tolist())

print(f"  Complete grid indices: {complete_indices[:10]}...")
```

## Related Documentation

- [Elements & Hierarchy](elements.md)
- [Properties & Data Access](properties.md)
- [Coordinates & Connections](coordinates.md)
- [SR3Reader Overview](overview.md)
