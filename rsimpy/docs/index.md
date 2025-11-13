# rsimpy Documentation

**rsimpy** is a Python package for handling reservoir simulation files, with a primary focus on CMG (Computer Modelling Group) file formats.

## Table of Contents

1. [Getting Started](getting_started.md)
2. [Installation](installation.md)
3. [Modules Overview](#modules-overview)
4. [Quick Examples](quick_examples.md)

## Modules Overview

### CMG Module (`rsimpy.cmg`)

Tools for reading and writing CMG simulation files:

- **[SR3Reader](sr3reader/overview.md)** - Read and analyze SR3 results files
  - [Elements & Hierarchy](sr3reader/elements.md)
  - [Properties & Data](sr3reader/properties.md)
  - [Grid Operations](sr3reader/grid.md)
  - [Dates & Times](sr3reader/dates.md)
  - [Units Management](sr3reader/units.md)
  - [Coordinates & Connections](sr3reader/coordinates.md)
  - [Relative Permeability](sr3reader/krel.md)
  - [Visualization & Plotting](sr3reader/plotting.md)

- **[GridFile](gridfile.md)** - Read/write ASCII grid files (ALL format)

- **[DatReader](datreader/overview.md)** - Parse and process .dat input files
  - [Keywords & Structure](datreader/parser.md)
  - [Dates & Schedule](datreader/dates.md)
  - [Wells & Operations](datreader/wells.md)
  - [PVT Tables](datreader/pvt.md)

- **[OutReader](outreader.md)** - Extract data from .out output files

### Common Module (`rsimpy.common`)

Utility modules for common tasks:

- **[TemplateProcessor](template.md)** - Generate files from templates with parameter sampling
- **[Interpolation](interpolation.md)** - Interpolation utilities for PVT and other data
- **[File Utilities](file_utils.md)** - Common file handling operations

## Key Features

### SR3Reader
- Read SR3 binary results files from IMEX, GEM, and STARS
- Support for 2phi2k (dual porosity/dual permeability) models
- Extract time-series data for wells, groups, sectors, and grid properties
- Query element hierarchy (wells, groups, layers)
- Handle unit conversions
- Export data to CSV, pandas DataFrames, or xarray Datasets
- Read relative permeability tables
- Grid coordinate extraction and visualization
- Connection transmissibility calculations
- Interactive plotting with Bokeh

### GridFile
- Read/write CMG ASCII grid files in ALL format
- Support for coordinate transformations (IJK ↔ cell number)
- Sub-grid extraction
- Batch processing of multiple grid files

### DatReader
- Parse DAT input files with flexible keyword filtering
- Extract dates, well definitions, and operational constraints
- Read PVT tables and interpolate properties
- Schedule manipulation and daily timestep generation

### OutReader
- Detect simulator type (IMEX, GEM, STARS)
- Extract well index data
- Parse connection information

### TemplateProcessor
- Define variables with statistical distributions
- Generate multiple realizations for uncertainty analysis
- Support for uniform, normal, lognormal, triangular, and categorical distributions
- Import variables from CSV tables
- Batch file generation

## Supported Simulators

- **CMG IMEX** - Black oil simulator
- **CMG GEM** - Compositional and unconventional simulator
- **CMG STARS** - Thermal and advanced processes simulator

## Quick Start

```python
from rsimpy.cmg.sr3reader import Sr3Reader

# Open SR3 file
sr3 = Sr3Reader("simulation.sr3")

# Get well production data
well_data = sr3.data.get(
    element_type="well",
    properties=["BHP", "OILRATSC"],
    elements=["PROD-01", "PROD-02"]
)

# Export to CSV
well_data.to_csv("production_data.csv")
```

## Documentation Conventions

- **Required parameters** are shown in bold
- *Optional parameters* are shown in italics
- Code examples are provided throughout
- Return types are documented for all methods

## License

See [LICENSE](../../LICENSE) file for details.

## Contributing

Contributions are welcome! Please see the repository for contribution guidelines.
