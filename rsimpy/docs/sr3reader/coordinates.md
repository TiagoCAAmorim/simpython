# Grid Coordinates & Connections

The Coordinates and Connections components provide access to grid geometry, cell corner coordinates, connection topology, and transmissibilities.

## Overview

These components provide:
- 3D cell corner coordinates
- Cell face coordinates extraction
- Grid connection topology
- Transmissibility calculations
- Time-of-flight (TOF) calculations
- Visualization of grid geometry

## Cell Coordinates

### coordinates.get(cells, face)

Get 3D coordinates for cell corners.

```python
# Get coordinates for specific cells
coords = sr3.grid.coordinates.get(cells=[1, 2, 3, 4], face='K-')

# Get coordinates for a single cell
coords = sr3.grid.coordinates.get(cells=10, face='K+')
```

**Parameters:**
- **cells** (`int` or `list`): Cell index/indices (complete grid numbering, 1-indexed)
- **face** (`str`): Cell face identifier

**Valid Faces:**
- `'K-'` - Bottom face (lower K)
- `'K+'` - Top face (upper K)
- `'I-'` - West face (lower I)
- `'I+'` - East face (upper I)
- `'J-'` - South face (lower J)
- `'J+'` - North face (upper J)

**Returns:** `numpy.ndarray` - Shape `(n_cells, 4, 3)` with corner coordinates `[x, y, z]`

**Corner Ordering:**
For each face, corners are ordered counter-clockwise when viewed from outside:
- K faces: corners in I-J plane
- I faces: corners in J-K plane
- J faces: corners in I-K plane

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get coordinates for cell 1
cell_coords = sr3.grid.coordinates.get(cells=1, face='K-')

print("Cell 1 bottom face corners:")
for i, corner in enumerate(cell_coords[0]):
    x, y, z = corner
    print(f"  Corner {i+1}: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")

# Calculate cell center
center = cell_coords[0].mean(axis=0)
print(f"\nCell center: X={center[0]:.2f}, Y={center[1]:.2f}, Z={center[2]:.2f}")

# Calculate cell area (approximate)
v1 = cell_coords[0, 2] - cell_coords[0, 0]
v2 = cell_coords[0, 3] - cell_coords[0, 1]
area = 0.5 * np.linalg.norm(np.cross(v1, v2))
print(f"Face area: {area:.2f} m²")
```

### Extracting Layer Coordinates

```python
# Get dimensions
ni, nj, nk = sr3.grid.get_size("nijk")

# Calculate layer cell indices (complete grid)
layer_k = 50
layer_cells = list(range((layer_k-1)*ni*nj + 1, layer_k*ni*nj + 1))

# Get top face coordinates for entire layer
layer_coords = sr3.grid.coordinates.get(cells=layer_cells, face='K+')
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")

# Select layer
layer_k = 50

# Get all cells in layer
layer_cells = list(range((layer_k-1)*ni*nj + 1, layer_k*ni*nj + 1))

# Get top surface of layer
top_coords = sr3.grid.coordinates.get(cells=layer_cells, face='K+')

# Extract Z values (depth)
depths = top_coords[:, :, 2].mean(axis=1).reshape(nj, ni)

# Plot depth map
plt.figure(figsize=(10, 8))
plt.imshow(depths, aspect='auto', cmap='terrain_r', origin='lower')
plt.colorbar(label='Depth (m)')
plt.title(f'Layer {layer_k} Top Surface')
plt.xlabel('I')
plt.ylabel('J')
plt.savefig(f'layer_{layer_k}_surface.png')
```

## Grid Connections

### connections.get_connections(as_active)

Get grid cell connection topology.

```python
# Get connections (complete grid indices)
connections = sr3.connections.get_connections()

# Get connections (active grid indices)
connections = sr3.connections.get_connections(as_active=True)
```

**Parameters:**
- **as_active** (`bool`, optional): Return active cell indices. Default: `False`

**Returns:** `numpy.ndarray` - Shape `(n_connections, 3)` with columns `[cell1, cell2, direction]`

**Direction Codes:**
- `1` - I direction (East-West)
- `2` - J direction (North-South)
- `3` - K direction (Vertical)

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get connections
connections = sr3.connections.get_connections()

print(f"Total connections: {len(connections)}")

# Count by direction
n_i = np.sum(connections[:, 2] == 1)
n_j = np.sum(connections[:, 2] == 2)
n_k = np.sum(connections[:, 2] == 3)

print(f"I-direction: {n_i}")
print(f"J-direction: {n_j}")
print(f"K-direction: {n_k}")

# Show first 10 connections
print("\nFirst 10 connections (cell1, cell2, direction):")
for conn in connections[:10]:
    cell1, cell2, direction = conn
    dir_name = ['I', 'J', 'K'][direction-1]
    print(f"  {cell1:5d} <-> {cell2:5d}  ({dir_name})")
```

## Transmissibilities

### connections.get_transmissibilities(tof)

Calculate transmissibilities for all connections.

```python
# Get transmissibilities only
trans = sr3.connections.get_transmissibilities()

# Get transmissibilities and time-of-flight
trans_tof = sr3.connections.get_transmissibilities(tof=True)
```

**Parameters:**
- **tof** (`bool`, optional): Include time-of-flight calculation. Default: `False`

**Returns:**
- If `tof=False`: `numpy.ndarray` - Shape `(n_connections,)` with transmissibilities
- If `tof=True`: `numpy.ndarray` - Shape `(n_connections, 2)` with columns `[transmissibility, tof]`

**Units:**
- Transmissibility: m³·cp/(day·kPa) or equivalent in simulation units
- TOF: days

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get connections and transmissibilities
connections = sr3.connections.get_connections()
trans = sr3.connections.get_transmissibilities()

print(f"Transmissibility statistics:")
print(f"  Mean: {np.mean(trans):.2e}")
print(f"  Median: {np.median(trans):.2e}")
print(f"  Min: {np.min(trans):.2e}")
print(f"  Max: {np.max(trans):.2e}")

# Plot histogram by direction
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for i, (dir_code, dir_name) in enumerate([(1, 'I'), (2, 'J'), (3, 'K')]):
    mask = connections[:, 2] == dir_code
    trans_dir = trans[mask]

    axes[i].hist(np.log10(trans_dir), bins=50)
    axes[i].set_xlabel('log10(Transmissibility)')
    axes[i].set_ylabel('Count')
    axes[i].set_title(f'{dir_name}-direction')
    axes[i].grid(True)

plt.tight_layout()
plt.savefig('transmissibility_histogram.png')
```

### Time-of-Flight Analysis

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get transmissibilities with TOF
trans_tof = sr3.connections.get_transmissibilities(tof=True)
transmissibility = trans_tof[:, 0]
tof = trans_tof[:, 1]

print(f"Time-of-Flight statistics:")
print(f"  Mean: {np.mean(tof):.2f} days")
print(f"  Median: {np.median(tof):.2f} days")
print(f"  Min: {np.min(tof):.2f} days")
print(f"  Max: {np.max(tof):.2f} days")

# Find fast flow paths (low TOF)
fast_threshold = np.percentile(tof, 10)  # Bottom 10%
fast_connections = connections[tof < fast_threshold]

print(f"\nFast flow connections (TOF < {fast_threshold:.2f} days): {len(fast_connections)}")
```

## Connection String Representation

### connections.print_sconnect(connections)

Convert connection array to readable string format.

```python
# Get connections
connections = sr3.connections.get_connections()

# Convert to strings
conn_strings = sr3.connections.print_sconnect(connections)
```

**Parameters:**
- **connections** (`numpy.ndarray`): Connection array from `get_connections()`

**Returns:** `list` of `str` - Human-readable connection descriptions

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get first 10 connections
connections = sr3.connections.get_connections()[:10]

# Convert to readable strings
conn_strings = sr3.connections.print_sconnect(connections)

print("First 10 connections:")
for i, conn_str in enumerate(conn_strings, 1):
    print(f"  {i}. {conn_str}")
```

## Visualization

### coordinates.plot_planes(faces)

Plot cell face geometries.

```python
# Get face coordinates
faces = sr3.grid.coordinates.get(cells=[1, 2, 3, 4], face='K-')

# Plot
axes = sr3.grid.coordinates.plot_planes(faces)
```

**Parameters:**
- **faces** (`numpy.ndarray`): Face coordinates from `coordinates.get()`

**Returns:** `numpy.ndarray` of matplotlib axes (one per face)

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get coordinates for several cells
cells = [100, 200, 300, 400]
faces = sr3.grid.coordinates.get(cells=cells, face='K+')

# Plot faces
axes = sr3.grid.coordinates.plot_planes(faces)

plt.savefig('cell_faces.png')
plt.show()
```

### connections.plot_connection(connection)

Plot a single connection between two cells.

```python
# Get connections
connections = sr3.connections.get_connections()

# Plot first connection
axes = sr3.connections.plot_connection(connections[0])
```

**Parameters:**
- **connection** (`numpy.ndarray`): Single connection `[cell1, cell2, direction]`

**Returns:** `numpy.ndarray` of matplotlib axes showing connection geometry

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get connections
connections = sr3.connections.get_connections()

# Find a vertical connection
k_connections = connections[connections[:, 2] == 3]  # K-direction

# Plot first vertical connection
axes = sr3.connections.plot_connection(k_connections[0])

plt.savefig('vertical_connection.png')
plt.show()
```

## Practical Examples

### Example 1: Identify High-Flow Corridors

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get connections and transmissibilities
connections = sr3.connections.get_connections(as_active=True)
trans = sr3.connections.get_transmissibilities()

# Find high transmissibility connections (top 5%)
high_trans_threshold = np.percentile(trans, 95)
high_trans_mask = trans > high_trans_threshold

high_trans_connections = connections[high_trans_mask]
high_trans_values = trans[high_trans_mask]

print(f"High transmissibility corridors (>{high_trans_threshold:.2e}):")
print(f"  Total: {len(high_trans_connections)}")

# Group by direction
for dir_code, dir_name in [(1, 'I'), (2, 'J'), (3, 'K')]:
    dir_mask = high_trans_connections[:, 2] == dir_code
    n_dir = np.sum(dir_mask)
    avg_trans = np.mean(high_trans_values[dir_mask]) if n_dir > 0 else 0

    print(f"  {dir_name}-direction: {n_dir} connections, avg trans: {avg_trans:.2e}")

# Get cells involved in high-flow corridors
cells_involved = np.unique(high_trans_connections[:, :2].flatten())
print(f"\nCells in high-flow corridors: {len(cells_involved)}")
```

### Example 2: Calculate Cell Volumes

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

def calculate_cell_volume(cell_idx):
    """Calculate cell volume from corner coordinates"""
    # Get all 8 corners (top and bottom faces)
    top = sr3.grid.coordinates.get(cells=cell_idx, face='K+')[0]
    bottom = sr3.grid.coordinates.get(cells=cell_idx, face='K-')[0]

    # Calculate average area of top and bottom
    def face_area(corners):
        v1 = corners[2] - corners[0]
        v2 = corners[3] - corners[1]
        return 0.5 * np.linalg.norm(np.cross(v1, v2))

    area_top = face_area(top)
    area_bottom = face_area(bottom)
    avg_area = (area_top + area_bottom) / 2

    # Calculate height
    height = np.abs(top[:, 2].mean() - bottom[:, 2].mean())

    # Volume
    volume = avg_area * height

    return volume

# Calculate volume for first 10 cells
print("Cell volumes:")
for cell_idx in range(1, 11):
    volume = calculate_cell_volume(cell_idx)
    print(f"  Cell {cell_idx}: {volume:,.2f} m³")

# Compare with SR3 file
grid_data = sr3.data.get(
    element_type="grid",
    properties=["BVOL"],
    elements="MATRIX",
    days=0,
    active_only=False
)

bvol_file = grid_data["BVOL"].sel(day=0).values[:10]

print("\nComparison with file:")
for i in range(10):
    volume_calc = calculate_cell_volume(i+1)
    volume_file = bvol_file[i]
    diff_pct = abs(volume_calc - volume_file) / volume_file * 100
    print(f"  Cell {i+1}: Calc={volume_calc:.2f}, File={volume_file:.2f}, Diff={diff_pct:.1f}%")
```

### Example 3: Map Connection Network

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get connections (active indices)
connections = sr3.connections.get_connections(as_active=True)
trans = sr3.connections.get_transmissibilities()

# Create graph
G = nx.Graph()

# Add edges with transmissibility as weight
for conn, t in zip(connections, trans):
    cell1, cell2, direction = conn
    G.add_edge(int(cell1), int(cell2), weight=float(t), direction=int(direction))

print(f"Connection Network:")
print(f"  Nodes: {G.number_of_nodes()}")
print(f"  Edges: {G.number_of_edges()}")
print(f"  Connected: {nx.is_connected(G)}")

# Find most connected cells
degree = dict(G.degree())
top_cells = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:10]

print(f"\nMost connected cells:")
for cell, n_connections in top_cells:
    print(f"  Cell {cell}: {n_connections} connections")

# Find shortest path (in terms of number of hops)
if G.number_of_nodes() > 1:
    nodes = list(G.nodes())
    source = nodes[0]
    target = nodes[-1]

    if nx.has_path(G, source, target):
        shortest_path = nx.shortest_path(G, source, target)
        print(f"\nShortest path from {source} to {target}:")
        print(f"  Cells: {shortest_path}")
        print(f"  Hops: {len(shortest_path) - 1}")
```

### Example 4: Extract Layer Boundaries

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")

# Extract top of each layer
layer_tops = []

for k in range(1, nk + 1):
    # Get all cells in layer
    layer_cells = list(range((k-1)*ni*nj + 1, k*ni*nj + 1))

    # Get top face coordinates
    top_coords = sr3.grid.coordinates.get(cells=layer_cells, face='K+')

    # Average depth of top face
    avg_depth = top_coords[:, :, 2].mean()

    layer_tops.append({
        'layer': k,
        'top_depth': avg_depth
    })

# Calculate layer thicknesses
for i in range(len(layer_tops) - 1):
    thickness = layer_tops[i+1]['top_depth'] - layer_tops[i]['top_depth']
    layer_tops[i]['thickness'] = thickness

print("Layer boundaries:")
print(f"{'Layer':<8} {'Top (m)':<12} {'Thickness (m)':<15}")
print("-" * 35)
for layer_info in layer_tops[:10]:  # First 10 layers
    layer = layer_info['layer']
    top = layer_info['top_depth']
    thick = layer_info.get('thickness', 0)
    print(f"{layer:<8} {top:<12.2f} {thick:<15.2f}")
```

### Example 5: Visualize Connection Density

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")
n_active = sr3.grid.get_size("n_active")

# Get connections (active indices)
connections = sr3.connections.get_connections(as_active=True)

# Count connections per cell
connection_count = np.zeros(n_active + 1, dtype=int)

for conn in connections:
    cell1, cell2, _ = conn
    connection_count[cell1] += 1
    connection_count[cell2] += 1

# Remove index 0 (not used)
connection_count = connection_count[1:]

# Statistics
print("Connection density:")
print(f"  Mean: {connection_count.mean():.2f}")
print(f"  Median: {np.median(connection_count):.0f}")
print(f"  Min: {connection_count.min()}")
print(f"  Max: {connection_count.max()}")

# Plot histogram
plt.figure(figsize=(10, 6))
plt.hist(connection_count, bins=range(connection_count.min(), connection_count.max()+2))
plt.xlabel('Number of Connections')
plt.ylabel('Number of Cells')
plt.title('Connection Density Distribution')
plt.grid(True)
plt.savefig('connection_density.png')

# Identify isolated or poorly connected cells
poorly_connected = np.where(connection_count < 3)[0] + 1  # Convert to 1-indexed

if len(poorly_connected) > 0:
    print(f"\nPoorly connected cells (<3 connections): {len(poorly_connected)}")
    print(f"  Active indices: {poorly_connected[:10]}...")
```

## Common Patterns

### Get Cell Centers

```python
# Get top and bottom faces
top = sr3.grid.coordinates.get(cells=cell_idx, face='K+')[0]
bottom = sr3.grid.coordinates.get(cells=cell_idx, face='K-')[0]

# Calculate center
center = (top.mean(axis=0) + bottom.mean(axis=0)) / 2
```

### Find Neighbors

```python
# Get connections for a specific cell
connections = sr3.connections.get_connections(as_active=True)
cell_idx = 100

neighbors = connections[(connections[:, 0] == cell_idx) | (connections[:, 1] == cell_idx)]
```

### Filter Connections by Direction

```python
connections = sr3.connections.get_connections()

# Horizontal connections only
horizontal = connections[connections[:, 2] != 3]

# Vertical connections only
vertical = connections[connections[:, 2] == 3]
```

## Related Documentation

- [Grid Operations](grid.md)
- [Properties & Data Access](properties.md)
- [Plotting & Visualization](plotting.md)
- [SR3Reader Overview](overview.md)
