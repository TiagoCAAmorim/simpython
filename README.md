# simpython
Python code and helpers for reservoir simulation analysis.

## rsimpy - Reservoir Simulation File Handler

**rsimpy** is a comprehensive Python package for handling CMG (Computer Modelling Group) reservoir simulation files. It provides tools for reading results files (SR3), processing input/output files (DAT/OUT), manipulating grid properties, and generating parametric studies.

### Key Features

* **SR3Reader** - Read and analyze SR3 binary results files
  - Support for IMEX, GEM, and STARS simulators
  - Time-series data extraction for wells, groups, and grid properties
  - Element hierarchy management
  - Unit conversions and date/time handling
  - Relative permeability tables and PVT data
  - Interactive visualization with Bokeh
  - Export to CSV, pandas, and xarray formats

* **GridFile** - Read/write CMG ASCII grid files (ALL format)
  - Support for single and dual-porosity models
  - IJK coordinate transformations
  - Sub-grid extraction
  - Batch processing capabilities

* **DatReader** - Parse and process DAT input files
  - Keyword extraction and filtering
  - Date/schedule manipulation
  - Well definition extraction
  - PVT table reading and interpolation

* **TemplateProcessor** - Template-based file generation
  - Parameter sampling with various distributions
  - Uncertainty quantification workflows
  - Ensemble generation for Monte Carlo simulations

* **OutReader** - Extract data from OUT files
  - Well index extraction
  - Simulator type detection
  - Connection information parsing

### Documentation

Comprehensive documentation is available in the `rsimpy/docs/` directory:

- **[Main Index](rsimpy/docs/index.md)** - Overview and module listing
- **[Getting Started](rsimpy/docs/getting_started.md)** - Installation and basic usage
- **[Installation Guide](rsimpy/docs/installation.md)** - Detailed setup instructions
- **[Quick Examples](rsimpy/docs/quick_examples.md)** - Practical code examples

**Module Documentation:**
- [SR3Reader](rsimpy/docs/sr3reader/overview.md) - SR3 results file handling
- [GridFile](rsimpy/docs/gridfile.md) - Grid property file operations
- [DatReader](rsimpy/docs/datreader/overview.md) - Input file processing
- [OutReader](rsimpy/docs/outreader.md) - Output file parsing
- [TemplateProcessor](rsimpy/docs/template.md) - Template-based generation

### Installation

```bash
# Clone the repository
git clone https://github.com/TiagoCAAmorim/simpython.git
cd simpython

# Install in development mode
pip install -e .
```

See [Installation Guide](rsimpy/docs/installation.md) for detailed instructions.

### Examples

#### Sr3Reader

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3_file_path = "./model.sr3"
sr3 = Sr3Reader(sr3_file_path)

# Get available elements
well_ names = sr3.elements.get("well").keys()
group_names = sr3.elements.get("group").keys()
is_2phi2k = "FRACTURE" in sr3.elements.get("grid").keys()

# Get available time-series
well_timeseries_names = sr3.properties.get("well").keys()
grid_properties_names = sr3.properties.get("grid").keys()

# Get time-series unit
qo_unit_str = sr3.properties.unit("OILRATSC")

# Get hierarchy
group_parent = sr3.elements.get_parent("group","PLAT1-PRO")
p13_group = sr3.elements.get_parent("well","P13")
producers = sr3.elements.get_children("well","PLAT1-PRO")

# Get grid sizes
ni, nj, nk = sr3.grid.get_size("nijk")

# Get time-series
well_data = sr3.data.get("well", ["BHP","QO"], ["P11","P13"])
p11_bhp = well_data["BHP"].sel(element="P11").values

elapsed_data = sr3.data.get("special", "ELAPSED", days=[30., 1085., 2162.])
elapsed_values = elapsed_data["ELAPSED"].sel(element="").values

# Get grid data
grid_data = sr3.data.get("grid", ["SO","PRES","VISO","Z(CO2)"], "MATRIX", days=10.)
grid_so = file_read["SO"].sel(day=10.).values

# Get relative permeability tables
krel = sr3.krel.get(table_number=2)
sw = krel['sw'].values
krow = krel['sw'].values

# Save data to csv
grid_data.to_csv('./grid_data.csv')
sr3.data.to_csv("well", ["QO","BHP","NP"], ["P11","P13"], './wells.csv')
krel.to_csv('krel.csv')

# Plot layer 50 K- faces
all_layers = sr3.grid.coordinates.get(cells=np.arange(1,ni*nj*nk+1), face='K-')
all_layers_act = sr3.data.to_active(all_layers)

layer = 50
active_index = sr3.grid.complete2active(np.arange(1,ni*nj*nk+1))
layer_index = active_index.reshape((nk,nj,ni))[layer-1,:,:]
layer_index = layer_index[layer_index>0]

axes = sr3.grid.coordinates.plot_planes(all_layers_act[layer_index], marker='')
```

#### GridFile

```python
from rsimpy.cmg.gridfile import GridFile

inc_file_path = Path('./grid/POR.inc')
g_file = GridFile(inc_file_path)

n_values = g_file.get_number_values()
keyword_str = g_file.get_keyword().strip()
comments = g_file.get_comments().split('\n')

ni, nj, nk = 12, 23, 33
g_file.set_shape([ni,nj,nk])
sub_grid = ((1,12),(1,12),(29,33))
new_file_path = './grid/POR_sub.inc'
g_file.write(file_path=new_file_path, coord_range=sub_grid)
```