# GridFile Module

The `GridFile` class provides functionality to read and write CMG-style ASCII grid files in the ALL format.

## Overview

Grid files in CMG typically contain property arrays (like permeability, porosity, rock type) defined on a 3D grid. The GridFile module can:

- Read grid property files in ALL format
- Write grid properties with optional sub-grid extraction
- Convert between cell numbering and IJK coordinates
- Batch process multiple grid files

## Class: GridFile

### Constructor

```python
from rsimpy.cmg.gridfile import GridFile

grid = GridFile(file_path="path/to/gridfile.inc")
```

**Parameters:**
- **file_path** (`str` or `Path`): Path to the grid file to read. If empty string, creates an empty GridFile object.

The file is automatically read upon initialization if a valid path is provided.

## Methods

### get_keyword()

Returns the keyword found in the file (e.g., "PERMK ALL", "RTYPE ALL").

```python
keyword = grid.get_keyword()
# Returns: "PERMK ALL"
```

**Returns:** `str` - The keyword string with trailing whitespace stripped.

### get_comments()

Returns the comment lines found at the beginning of the file.

```python
comments = grid.get_comments()
# Returns: String with comment lines separated by '\n'
```

**Returns:** `str` - Comment text, or empty string if no comments found.

### get_number_values()

Returns the total number of values in the grid file.

```python
n_values = grid.get_number_values()
# Returns: 533403
```

**Returns:** `int` - Total number of values in the array.

### get_values()

Returns the grid values as a NumPy array.

```python
values = grid.get_values()
# Returns: numpy.ndarray
```

**Returns:** `numpy.ndarray` - Array containing all grid values.

### set_shape()

Sets the grid dimensions (NI, NJ, NK) to enable coordinate transformations.

```python
ni, nj, nk = 100, 50, 30
grid.set_shape([ni, nj, nk])
# or
grid.set_shape((ni, nj, nk))
```

**Parameters:**
- **shape** (`list` or `tuple`): Grid dimensions as `[NI, NJ, NK]`

**Raises:**
- `ValueError`: If shape doesn't have exactly 3 elements or if product doesn't match number of values per region.

**Note:** The product `NI × NJ × NK` must equal the number of values divided by the number of regions (1 for single-porosity, 2 for dual-porosity models).

### n2ijk()

Converts cell number(s) to IJK coordinates.

```python
# Single cell
i, j, k = grid.n2ijk(cell_number)

# Multiple cells
ijk_coords = grid.n2ijk([1, 4, 9])
# Returns: array([(1,1,1), (1,2,1), (3,1,2)])

# Include region (for dual-porosity)
i, j, k, r = grid.n2ijk(cell_number, include_region=True)
```

**Parameters:**
- **n** (`int` or `array-like`): Cell number(s) to convert (1-indexed)
- **include_region** (`bool`, optional): If True, returns 4-tuple (I,J,K,R) for dual-porosity grids

**Returns:**
- Single cell: `tuple` of `(I, J, K)` or `(I, J, K, R)`
- Multiple cells: `numpy.ndarray` of tuples

**Note:** Cell numbering is 1-indexed and follows Fortran column-major ordering (I varies fastest).

### ijk2n()

Converts IJK coordinates to cell number(s).

```python
# Single cell
cell_num = grid.ijk2n((i, j, k))

# Multiple cells
cell_nums = grid.ijk2n([(1,1,1), (1,2,1), (3,1,2)])
# Returns: (1, 4, 9)

# With region specification
cell_num = grid.ijk2n((i, j, k, region))
```

**Parameters:**
- **ijk** (`tuple` or `array-like`): Coordinates as `(I,J,K)` or `(I,J,K,R)` (1-indexed)

**Returns:**
- Single cell: `int` - Cell number
- Multiple cells: `tuple` of cell numbers

### write()

Writes the grid file to disk, optionally extracting a sub-grid.

```python
# Write complete grid
grid.write(file_path="output.inc")

# Write sub-grid
sub_grid_range = ((10, 50), (5, 25), (1, 15))  # (I_min, I_max), (J_min, J_max), (K_min, K_max)
grid.write(
    file_path="sub_grid.inc",
    coord_range=sub_grid_range
)
```

**Parameters:**
- **file_path** (`str` or `Path`): Output file path
- **coord_range** (`tuple`, optional): Sub-grid specification as `((I_min, I_max), (J_min, J_max), (K_min, K_max))`. All indices are 1-indexed and inclusive.

**Note:** The output file maintains the ALL format with proper formatting (8 values per line for the data section).

### rewrite_all_grid_files()

Batch process all grid files in a directory.

```python
grid = GridFile("")  # Create empty GridFile
grid.rewrite_all_grid_files(
    folder_path="grid_files/",
    new_suffix=".new",
    verbose=True
)
```

**Parameters:**
- **folder_path** (`str` or `Path`): Directory containing grid files
- **new_suffix** (`str`, optional): New file extension (default: ".inc")
- **verbose** (`bool`, optional): Print progress messages (default: True)

**Description:** Reads all grid files in the folder and rewrites them with the specified suffix. Useful for batch conversion or reformatting.

## File Format

The GridFile module reads files in the CMG ALL format:

```
** Comments (optional, lines starting with **)
KEYWORD ALL
value1 value2 value3 value4 value5 value6 value7 value8
value9 value10 ...
```

Example PERMK file:
```
** Permeability in I direction
** Generated on 2024-01-01
PERMK ALL
100.5 150.2 200.0 125.8 175.3 190.1 155.0 145.5
130.2 160.8 ...
```

## Examples

### Example 1: Reading and Inspecting a Grid File

```python
from rsimpy.cmg.gridfile import GridFile
from pathlib import Path

# Read grid file
grid_file = Path("grid/PERMK.geo")
grid = GridFile(file_path=grid_file)

# Get basic information
n_values = grid.get_number_values()
keyword = grid.get_keyword().strip()
comments = grid.get_comments()

print(f"Keyword: {keyword}")
print(f"Total values: {n_values}")
print(f"Comments:\n{comments}")

# Set grid dimensions
ni, nj, nk = 47, 39, 291
grid.set_shape([ni, nj, nk])
```

### Example 2: Coordinate Transformations

```python
# Convert cell number to IJK
cell_num = 1000
i, j, k = grid.n2ijk(cell_num)
print(f"Cell {cell_num} is at ({i}, {j}, {k})")

# Convert IJK back to cell number
cell = grid.ijk2n((i, j, k))
assert cell == cell_num

# Batch conversion
cell_list = [1, 100, 500, 1000]
ijk_list = grid.n2ijk(cell_list)
print(ijk_list)
```

### Example 3: Extracting a Sub-Grid

```python
from rsimpy.cmg.gridfile import GridFile

# Read original grid
input_file = "grid/POROS.inc"
grid = GridFile(input_file)

# Set dimensions
ni, nj, nk = 100, 50, 30
grid.set_shape([ni, nj, nk])

# Extract central region
sub_grid_range = (
    (25, 75),   # I: cells 25-75
    (10, 40),   # J: cells 10-40
    (5, 25)     # K: cells 5-25
)

# Write sub-grid
output_file = "grid/POROS_center.inc"
grid.write(file_path=output_file, coord_range=sub_grid_range)

# Verify sub-grid
sub_grid = GridFile(output_file)
expected_size = (75-25+1) * (40-10+1) * (25-5+1)
assert sub_grid.get_number_values() == expected_size
```

### Example 4: Batch Processing Grid Files

```python
from rsimpy.cmg.gridfile import GridFile
from pathlib import Path

# Process all .geo files in a directory
grid_dir = Path("grid_files/")
output_suffix = ".inc"

# Create empty GridFile for batch processing
processor = GridFile("")
processor.rewrite_all_grid_files(
    folder_path=grid_dir,
    new_suffix=output_suffix,
    verbose=True
)

print(f"Converted all .geo files to {output_suffix} format")
```

### Example 5: Working with Dual-Porosity Grids

```python
from rsimpy.cmg.gridfile import GridFile

# Read 2phi2k grid file (contains both matrix and fracture regions)
grid = GridFile("grid/PERM_2PHI2K.inc")

# Set dimensions (note: total values = ni*nj*nk*2)
ni, nj, nk = 50, 50, 20
grid.set_shape([ni, nj, nk])

# Convert with region information
cell_num = 5000  # First cell in fracture region
i, j, k, region = grid.n2ijk(cell_num, include_region=True)
print(f"Cell {cell_num}: ({i},{j},{k}) in region {region}")

# Convert back
cell = grid.ijk2n((i, j, k, region))
assert cell == cell_num
```

### Example 6: Creating Modified Grid Properties

```python
import numpy as np
from rsimpy.cmg.gridfile import GridFile

# Read original permeability
grid = GridFile("grid/PERMI.inc")
ni, nj, nk = 100, 50, 30
grid.set_shape([ni, nj, nk])

# Get values and modify
values = grid.get_values()
modified_values = values * 1.5  # Increase permeability by 50%

# Create new GridFile with modified values
# (Note: You would need to use internal methods or recreate the file)
# This example shows the concept - actual implementation may vary

# Write modified grid
grid.write("grid/PERMI_modified.inc")
```

## Error Handling

The GridFile module raises specific exceptions:

- **FileNotFoundError**: When the specified file doesn't exist
- **ValueError**: When file format is invalid (multiple keywords, no data, wrong dimensions)

Example:
```python
from rsimpy.cmg.gridfile import GridFile

try:
    grid = GridFile("nonexistent.geo")
except FileNotFoundError:
    print("File not found!")

try:
    grid = GridFile("invalid_format.geo")
except ValueError as e:
    print(f"Invalid file format: {e}")
```

## Performance Considerations

- Files are read entirely into memory upon initialization
- For very large grids (millions of cells), memory usage may be significant
- Sub-grid extraction is efficient and doesn't require loading the entire grid
- Batch processing handles files sequentially

## Related Documentation

- [Getting Started](getting_started.md) - Basic usage examples
- [SR3Reader Grid Operations](sr3reader/grid.md) - Working with SR3 grid data
- [Quick Examples](quick_examples.md) - More practical examples
