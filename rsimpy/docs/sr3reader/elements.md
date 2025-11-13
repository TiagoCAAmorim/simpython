# Elements and Hierarchy

The Elements component of SR3Reader manages simulation elements and their hierarchical relationships, including wells, groups, sectors, layers, and grid regions.

## Overview

The elements manager provides access to:
- Element lists by type
- Parent-child relationships in the hierarchy
- Layer connection and perforation data
- Component definitions for compositional models

## Element Types

### Available Element Types

- **well**: Individual wells (producers and injectors)
- **group**: Well groups for operational management
- **sector**: Sectors or regions of the reservoir
- **layer**: Individual perforated layers/connections
- **grid**: Grid regions (MATRIX, FRACTURE for dual-porosity)

## Methods

### get(element_type)

Get all elements of a specific type.

```python
# Get all wells
wells = sr3.elements.get("well")
well_names = list(wells.keys())

# Get all groups
groups = sr3.elements.get("group")
group_names = list(groups.keys())

# Get grid regions
grid_regions = sr3.elements.get("grid")
# Returns: {'MATRIX': {...}} or {'MATRIX': {...}, 'FRACTURE': {...}}
```

**Parameters:**
- **element_type** (`str`): Type of element - "well", "group", "sector", "layer", or "grid"

**Returns:** `dict` - Dictionary with element names as keys

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get all wells
wells = sr3.elements.get("well")
print(f"Found {len(wells)} wells:")
for well_name in list(wells.keys())[:10]:
    print(f"  {well_name}")

# Check for dual-porosity
grid_regions = sr3.elements.get("grid")
is_2phi2k = "FRACTURE" in grid_regions
print(f"Dual-porosity model: {is_2phi2k}")
```

### get_parent(element_type, element_name)

Get the parent element in the hierarchy.

```python
# Get parent group of a well
parent_group = sr3.elements.get_parent(
    element_type="well",
    element_name="PROD-01"
)

# Get parent of a group
field_group = sr3.elements.get_parent(
    element_type="group",
    element_name="PLAT1-PRO"
)

# Get parent well of a layer
parent_well = sr3.elements.get_parent(
    element_type="layer",
    element_name="P13{28,24,48}"
)
```

**Parameters:**
- **element_type** (`str`): Type of element
- **element_name** (`str`): Name of the element

**Returns:** `str` - Name of parent element, or empty string if no parent

**Hierarchy Structure:**

```
FIELD (sector)
├── FIELD-PRO (group)
│   ├── PLAT1-PRO (group)
│   │   ├── P-PLAT1-PRO (group)
│   │   │   ├── P11 (well)
│   │   │   │   ├── P11{23,25,49} (layer)
│   │   │   │   ├── P11{23,25,50} (layer)
│   │   │   │   └── ...
│   │   │   ├── P12 (well)
│   │   │   └── ...
│   │   └── I-PLAT1-PRO (group)
│   │       ├── I11 (well)
│   │       └── ...
│   └── PLAT-TLD-PRO (group)
│       └── ...
└── FIELD-INJ (group)
    └── ...
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

well_name = "PROD-01"

# Trace hierarchy upwards
element = well_name
element_type = "well"

print(f"Hierarchy for {well_name}:")
while element:
    print(f"  {element_type}: {element}")

    # Get parent
    parent = sr3.elements.get_parent(element_type, element)

    if not parent:
        break

    # Move up the hierarchy
    element = parent
    if element_type == "well":
        element_type = "group"
    elif element_type == "group":
        # Groups can have group parents
        element_type = "group"
    elif element_type == "layer":
        element_type = "well"
```

### get_children(element_type, element_name)

Get all child elements in the hierarchy.

```python
# Get all wells in a group
wells_in_group = sr3.elements.get_children(
    element_type="well",
    element_name="PLAT1-PRO"
)

# Get all subgroups
subgroups = sr3.elements.get_children(
    element_type="group",
    element_name="FIELD-PRO"
)

# Get all layers for a well
well_layers = sr3.elements.get_children(
    element_type="layer",
    element_name="PROD-01"
)
```

**Parameters:**
- **element_type** (`str`): Type of child elements to retrieve
- **element_name** (`str`): Name of parent element

**Returns:** `list` - List of child element names

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get all producers
field_producers = sr3.elements.get_children(
    element_type="well",
    element_name="FIELD-PRO"
)

print(f"Total producers: {len(field_producers)}")

# Get wells by platform
platforms = ["PLAT1-PRO", "PLAT2-PRO", "PLAT-TLD-PRO"]

for platform in platforms:
    try:
        wells = sr3.elements.get_children(
            element_type="well",
            element_name=platform
        )
        print(f"{platform}: {len(wells)} wells")
    except:
        print(f"{platform}: Not found")

# Get detailed layer information for a well
well_name = "PROD-01"
layers = sr3.elements.get_children(
    element_type="layer",
    element_name=well_name
)

print(f"\n{well_name} has {len(layers)} layers:")
for layer in layers[:5]:  # First 5
    print(f"  {layer}")
```

### get_layer_data(data_name)

Get layer-specific data (connections or perforations).

```python
# Get connection indices
connections = sr3.elements.get_layer_data(data_name="connection")

# Get perforation status
perforations = sr3.elements.get_layer_data(data_name="perf")
```

**Parameters:**
- **data_name** (`str`): "connection" or "perf"

**Returns:** `dict` - Dictionary mapping layer names to values

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get connection data
connections = sr3.elements.get_layer_data(data_name="connection")

# Check connection index for specific layer
layer_name = "I11{31,10,76}"
if layer_name in connections:
    conn_idx = connections[layer_name]
    print(f"Layer {layer_name} connection index: {conn_idx}")

# Get perforation status
perforations = sr3.elements.get_layer_data(data_name="perf")

# Count perforated vs non-perforated layers
perf_count = sum(1 for is_perf in perforations.values() if is_perf)
total = len(perforations)
print(f"Perforated layers: {perf_count}/{total}")

# Check specific layer
layer_name = "P11{23,25,219}"
if layer_name in perforations:
    is_perforated = perforations[layer_name]
    status = "perforated" if is_perforated else "not perforated"
    print(f"Layer {layer_name}: {status}")
```

## Compositional Models

### get_components_list()

For compositional models (GEM), get the list of components.

```python
components = sr3.properties.get_components_list()

# Returns dict like:
# {
#     0: "CO2",
#     1: "N2 toCH4",
#     2: "C2HtoNC5",
#     3: "C6ttoC19",
#     4: "C29toC63",
#     5: "WATER"
# }
```

**Returns:** `dict` - Dictionary mapping component index to name

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("gem_model.sr3")

# Get components
components = sr3.properties.get_components_list()

print("Model components:")
for idx, comp_name in components.items():
    print(f"  {idx}: {comp_name}")

# Access component-specific properties
well_data = sr3.data.get(
    element_type="well",
    properties=[f"OILCMOLSC({comp})" for comp in components.values()],
    elements=["PROD-01"]
)
```

## Practical Examples

### Example 1: Analyze Well Organization

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get all wells
all_wells = sr3.elements.get("well")
well_names = list(all_wells.keys())

# Classify wells
producers = [w for w in well_names if w.startswith('P')]
injectors = [w for w in well_names if w.startswith('I')]

print(f"Total wells: {len(well_names)}")
print(f"  Producers: {len(producers)}")
print(f"  Injectors: {len(injectors)}")

# Analyze group structure
all_groups = sr3.elements.get("group")
print(f"\nTotal groups: {len(all_groups)}")

# Count wells per group
for group_name in all_groups.keys():
    wells = sr3.elements.get_children("well", group_name)
    if wells:
        print(f"  {group_name}: {len(wells)} wells")
```

### Example 2: Extract Well Completions

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

well_name = "PROD-01"

# Get all layers for the well
layers = sr3.elements.get_children("layer", well_name)

print(f"{well_name} completion:")
print(f"  Total layers: {len(layers)}")

# Parse layer information (format: "WELL{I,J,K}")
import re

layer_info = []
for layer in layers:
    match = re.match(r'(.+)\{(\d+),(\d+),(\d+)\}', layer)
    if match:
        well, i, j, k = match.groups()
        layer_info.append({
            'layer': layer,
            'I': int(i),
            'J': int(j),
            'K': int(k)
        })

# Find depth range
k_values = [info['K'] for info in layer_info]
print(f"  K range: {min(k_values)} to {max(k_values)}")

# Check perforation status
perforations = sr3.elements.get_layer_data("perf")
perf_layers = [layer for layer in layers if perforations.get(layer, False)]
print(f"  Perforated: {len(perf_layers)}/{len(layers)}")
```

### Example 3: Build Group Hierarchy Tree

```python
from rsimpy.cmg.sr3reader import Sr3Reader

def build_tree(sr3, element_type, element_name, level=0):
    """Recursively build hierarchy tree"""
    indent = "  " * level
    print(f"{indent}{element_name}")

    if element_type == "well":
        # Wells don't have children
        return

    # Get children
    if element_type == "group":
        # Groups can have group children
        child_groups = sr3.elements.get_children("group", element_name)
        for child in child_groups:
            build_tree(sr3, "group", child, level + 1)

        # And well children
        child_wells = sr3.elements.get_children("well", element_name)
        for child in child_wells:
            print(f"{'  ' * (level + 1)}{child} (well)")

sr3 = Sr3Reader("simulation.sr3")

# Build tree starting from field
print("Production Hierarchy:")
build_tree(sr3, "group", "FIELD-PRO", level=0)
```

### Example 4: Identify Dual-Porosity Regions

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Check grid regions
grid_regions = sr3.elements.get("grid")

print("Grid regions found:")
for region in grid_regions.keys():
    print(f"  {region}")

if "FRACTURE" in grid_regions:
    print("\nThis is a dual-porosity (2phi2k) model")

    # Get grid sizes
    n_active = sr3.grid.get_size("n_active")
    n_matrix = sr3.grid.get_size("n_active_matrix")
    n_fracture = sr3.grid.get_size("n_active_fracture")

    print(f"  Total active cells: {n_active}")
    print(f"  Matrix cells: {n_matrix}")
    print(f"  Fracture cells: {n_fracture}")
else:
    print("\nThis is a single-porosity model")
```

### Example 5: Map Wells to Platform/Region

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get all wells
all_wells = list(sr3.elements.get("well").keys())

# Build well-to-platform mapping
well_platform = {}

for well in all_wells:
    # Trace to find platform
    parent = sr3.elements.get_parent("well", well)

    while parent:
        # Check if this looks like a platform name
        if "PLAT" in parent.upper():
            well_platform[well] = parent
            break

        # Move up
        parent = sr3.elements.get_parent("group", parent)

    if well not in well_platform:
        well_platform[well] = "Unknown"

# Summarize by platform
from collections import Counter
platform_counts = Counter(well_platform.values())

print("Wells by platform:")
for platform, count in platform_counts.most_common():
    print(f"  {platform}: {count} wells")

    # Show example wells
    example_wells = [w for w, p in well_platform.items() if p == platform][:3]
    print(f"    Examples: {', '.join(example_wells)}")
```

## Element Naming Conventions

### Wells
- Often prefixed with type: `P` for producer, `I` for injector
- May include location: `P11`, `I-NORTH-01`
- Water injectors may have suffix: `I11-W`

### Groups
- Hierarchical naming: `FIELD-PRO`, `PLAT1-PRO`, `P-PLAT1-PRO`
- Suffixes indicate type: `-PRO` for producers, `-INJ` for injectors
- Default groups: `Default-Group-PRO`, `Default-Group-INJ`

### Layers
- Format: `WELLNAME{I,J,K}`
- Example: `P11{23,25,49}` = well P11, cell (23,25,49)
- Includes all connections, not just perforated intervals

### Sectors
- Typically `FIELD` for field-wide
- May include geographic regions
- Can be custom-defined in simulator input

## Common Issues and Solutions

### Issue: Element not found

```python
try:
    parent = sr3.elements.get_parent("well", "WELL-01")
except KeyError:
    print("Well WELL-01 not found in model")

    # Check available wells
    wells = sr3.elements.get("well")
    print(f"Available wells: {list(wells.keys())[:10]}")
```

### Issue: Empty children list

```python
children = sr3.elements.get_children("well", "GROUP-01")

if not children:
    print("No wells found in GROUP-01")

    # Check if group exists
    groups = sr3.elements.get("group")
    if "GROUP-01" in groups:
        print("Group exists but has no well children")
    else:
        print("Group does not exist")
```

### Issue: Understanding layer names

```python
import re

layer_name = "P11{23,25,49}"

# Parse layer information
match = re.match(r'(.+)\{(\d+),(\d+),(\d+)\}', layer_name)
if match:
    well_name, i, j, k = match.groups()
    print(f"Well: {well_name}")
    print(f"Cell IJK: ({i}, {j}, {k})")

    # Get parent well
    parent = sr3.elements.get_parent("layer", layer_name)
    print(f"Parent well: {parent}")
```

## Related Documentation

- [Properties & Data Access](properties.md)
- [Grid Operations](grid.md)
- [SR3Reader Overview](overview.md)
- [Quick Examples](../quick_examples.md)
