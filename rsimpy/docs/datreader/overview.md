# DatReader Module Overview

The DatReader module provides tools for parsing and processing CMG .dat input files. It can extract keywords, dates, well definitions, PVT tables, and other input data.

## Overview

The DatReader module consists of several submodules:

- **dat_parser**: Main parser for DAT file keywords
- **dat_dates**: Date/schedule extraction and manipulation
- **dat_run**: Well and operational data extraction
- **dat_pvt**: PVT table reading and interpolation
- **sch_to_daily**: Schedule modification utilities

## Modules

### dat_parser - Keyword Parser

Parse DAT files and extract keyword data.

#### Class: DatParser

```python
from rsimpy.cmg.datreader import dat_parser

parser = dat_parser.DatParser(
    encoding='utf-8',
    ignore=['TITLE1', 'GRID'],
    verbose=False,
    _debug=False
)
```

**Parameters:**
- **encoding** (`str`, optional): File encoding (default: 'utf-8')
- **ignore** (`list`, optional): List of keywords to skip
- **verbose** (`bool`, optional): Print progress (default: False)
- **_debug** (`bool`, optional): Enable debug output (default: False)

#### Methods

**process(file_path)**
Parse a DAT file:
```python
parser.process("simulation.dat")
results = parser.get()
```

**save(file_path)** / **load(file_path)**
Save/load parsed data:
```python
parser.save("parsed_data.json")

parser2 = dat_parser.DatParser()
parser2.load("parsed_data.json")
```

**get()**
Retrieve parsed data dictionary:
```python
data = parser.get()
# Returns: {'GRID': [...], 'RUN': [...], ...}
```

#### Example

```python
from rsimpy.cmg.datreader import dat_parser

# Parse DAT file
parser = dat_parser.DatParser(
    encoding='utf-8',
    ignore=['TITLE1', 'GRID', 'VFP_keys', 'GRID_keys',
            'FLUID_keys', 'TRIGGER_keys', 'KREL_keys', 'WELL_keys'],
    verbose=False
)

parser.process("base_case.dat")
results = parser.get()

# Check what was found
print("Sections found:", results.keys())

# Access RUN section
if 'RUN' in results:
    run_keys = [item[0] for item in results['RUN']]
    print("RUN keywords:", run_keys)

# Save for later use
parser.save("base_case_parsed.json")
```

### dat_dates - Date Management

Extract and manipulate simulation dates.

#### Functions

**get_from_dat(file_path)**
Extract dates from DAT file:
```python
from rsimpy.cmg.datreader import dat_dates

dates = dat_dates.get_from_dat("simulation.dat")
print(f"Found {len(dates)} dates")
print(f"First: {dat_dates.to_str(dates[0])}")
print(f"Last: {dat_dates.to_str(dates[-1])}")
```

**get_from_log(file_path)**
Extract dates from output log:
```python
dates = dat_dates.get_from_log("simulation.out")
```

**to_str(date)**
Convert date object to string:
```python
date_str = dat_dates.to_str(dates[0])
# Returns: "2018 09 02"
```

**get_progress(planned_dates, current_date)**
Calculate simulation progress:
```python
from rsimpy.cmg.datreader import dat_dates

planned = dat_dates.get_from_dat("simulation.dat")
actual = dat_dates.get_from_log("simulation.out")

if len(actual) > 0:
    progress = dat_dates.get_progress(planned, actual[-1])
    print(f"Progress: {progress*100:.1f}%")
```

#### Example

```python
from rsimpy.cmg.datreader import dat_dates

# Read schedule from DAT
dates = dat_dates.get_from_dat("simulation.dat")

# Print date range
print(f"Simulation period:")
print(f"  Start: {dat_dates.to_str(dates[0])}")
print(f"  End: {dat_dates.to_str(dates[-1])}")
print(f"  Total dates: {len(dates)}")

# Check progress
log_dates = dat_dates.get_from_log("simulation.out")
if log_dates:
    progress = dat_dates.get_progress(dates, log_dates[-1])
    print(f"\nSimulation {progress*100:.1f}% complete")
    print(f"Current date: {dat_dates.to_str(log_dates[-1])}")
```

### dat_run - Well and Operations

Extract well definitions and operational constraints.

#### Functions

**get_wells(data, keep_only_first=True, verbose=False)**
Extract well definitions:
```python
from rsimpy.cmg.datreader import dat_parser, dat_run

# First parse the file
parser = dat_parser.DatParser(ignore=['GRID_keys', 'VFP_keys', 'FLUID_keys'])
parser.process("simulation.dat")
data = parser.get()

# Get well information
wells = dat_run.get_wells(data, keep_only_first=True, verbose=True)

# Process well data
for date, well_name, *well_data in wells:
    print(f"{well_name} defined on {date}")
```

**get_well_key(data, keyword='BHPDEPTH', verbose=False)**
Extract specific well keyword data:
```python
bhp_depths = dat_run.get_well_key(data, keyword='BHPDEPTH', verbose=True)

for date, well_name, value in bhp_depths:
    print(f"{well_name}: BHP depth = {value} m")
```

#### Example

```python
from rsimpy.cmg.datreader import dat_parser, dat_run

# Parse DAT file
parser = dat_parser.DatParser(ignore=['GRID_keys', 'VFP_keys', 'FLUID_keys'])
parser.process("simulation.dat")
data = parser.get()

# Get all wells
wells = dat_run.get_wells(data, keep_only_first=True)
print(f"\nFound {len(wells)} wells:")

producer_count = 0
injector_count = 0

for date, well_name, *_ in wells:
    if well_name.startswith('P'):
        producer_count += 1
    elif well_name.startswith('I'):
        injector_count += 1

print(f"  Producers: {producer_count}")
print(f"  Injectors: {injector_count}")

# Get BHP reference depths
bhp_data = dat_run.get_well_key(data, keyword='BHPDEPTH')
print(f"\nBHP depth specifications: {len(bhp_data)}")
```

### dat_pvt - PVT Tables

Read and interpolate PVT (Pressure-Volume-Temperature) data.

#### Functions

**get_from_dat(file_path, verbose=False)**
Extract PVT tables:
```python
from rsimpy.cmg.datreader import dat_pvt

pvt_tables = dat_pvt.get_from_dat("simulation.dat", verbose=False)
print(f"Found {len(pvt_tables)} PVT tables")
```

**get_pvt_values(pvt, data, check_limits=True)**
Interpolate PVT properties:
```python
import numpy as np

# Define conditions (Rs, Pressure)
rs = np.array([100, 150, 200])
pres = np.array([250, 300, 350])
data = np.column_stack([rs, pres])

# Interpolate
properties = dat_pvt.get_pvt_values(pvt_tables[0], data, check_limits=True)

# Access interpolated values
bo = properties['BO']  # Oil formation volume factor
uo = properties['UO']  # Oil viscosity
bg = properties['BG']  # Gas formation volume factor
ug = properties['UG']  # Gas viscosity
```

**Inverse interpolation functions:**
- **get_bo_inv(pvt, bo, rs)**: Find pressure given Bo and Rs
- **get_uo_inv(pvt, uo, rs)**: Find pressure given viscosity and Rs
- **get_eg_inv(pvt, eg)**: Find pressure given gas expansion
- **get_ug_inv(pvt, ug)**: Find pressure given gas viscosity

**Water and rock properties:**
- **get_bw(pvt, pres)**: Water formation volume factor
- **get_uw(pvt, pres)**: Water viscosity
- **get_rhow(pvt, pres, bw)**: Water density
- **get_por_mod(pvt, pres)**: Porosity modification factor

**Equilibrium calculations:**
- **find_equilibrium(pvt, vo_std, vg_std, vw_std, vpor_ref, ...)**: Find equilibrium pressure

#### Example

```python
from rsimpy.cmg.datreader import dat_pvt
import numpy as np
import matplotlib.pyplot as plt

# Read PVT table
pvt_tables = dat_pvt.get_from_dat("simulation.dat")
pvt = pvt_tables[0]

# Create pressure-Rs grid
rs_range = np.linspace(0, 300, 50)
pres_range = np.linspace(100, 500, 50)

rs_grid, pres_grid = np.meshgrid(rs_range, pres_range)
data = np.column_stack([rs_grid.flatten(), pres_grid.flatten()])

# Interpolate Bo
properties = dat_pvt.get_pvt_values(pvt, data, check_limits=False)
bo = properties['BO'].reshape(rs_grid.shape)

# Plot Bo surface
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(rs_grid, pres_grid, bo, cmap='viridis')
ax.set_xlabel('Rs (m³/m³)')
ax.set_ylabel('Pressure (kgf/cm²)')
ax.set_zlabel('Bo (m³/m³)')
ax.set_title('Oil Formation Volume Factor')
plt.savefig('pvt_bo_surface.png')

# Validate with saturated values
plt.figure(figsize=(10, 6))
plt.plot(pvt['sat']['PRES'], pvt['sat']['BO'], 'o-', label='Saturated')
plt.xlabel('Pressure (kgf/cm²)')
plt.ylabel('Bo (m³/m³)')
plt.title('Saturated Oil Formation Volume Factor')
plt.legend()
plt.grid(True)
plt.savefig('pvt_bo_saturated.png')
```

### sch_to_daily - Schedule Modification

Convert schedule to daily timesteps.

#### Function

**process(file_path, output_path, delta_days=1, encoding='utf-8')**
Add daily dates between existing schedule dates:

```python
from rsimpy.cmg.datreader import sch_to_daily

sch_to_daily.process(
    file_path="schedule.dat",
    output_path="schedule_daily.dat",
    delta_days=1,
    encoding='utf-8'
)
```

**Parameters:**
- **file_path**: Input schedule file
- **output_path**: Output file with added dates
- **delta_days**: Interval for new dates (default: 1)
- **encoding**: File encoding (default: 'utf-8')

#### Example

```python
from rsimpy.cmg.datreader import sch_to_daily, dat_dates

# Original schedule
orig_dates = dat_dates.get_from_dat("schedule.dat")
print(f"Original: {len(orig_dates)} dates")

# Convert to daily
sch_to_daily.process(
    file_path="schedule.dat",
    output_path="schedule_daily.dat",
    delta_days=1
)

# Check result
daily_dates = dat_dates.get_from_dat("schedule_daily.dat")
print(f"Daily: {len(daily_dates)} dates")

# Run again (should be idempotent)
sch_to_daily.process(
    file_path="schedule_daily.dat",
    output_path="schedule_daily2.dat",
    delta_days=1
)

verify_dates = dat_dates.get_from_dat("schedule_daily2.dat")
assert len(daily_dates) == len(verify_dates), "Should not add more dates"
```

## Common Workflows

### Extract Complete Input Summary

```python
from rsimpy.cmg.datreader import dat_parser, dat_dates, dat_run, dat_pvt

# Parse DAT file
parser = dat_parser.DatParser(ignore=['GRID_keys'])
parser.process("simulation.dat")
data = parser.get()

# Get dates
dates = dat_dates.get_from_dat("simulation.dat")

# Get wells
wells = dat_run.get_wells(data, keep_only_first=True)

# Get PVT
pvt_tables = dat_pvt.get_from_dat("simulation.dat")

# Print summary
print("="*60)
print("INPUT FILE SUMMARY")
print("="*60)
print(f"\nSimulation Period:")
print(f"  Start: {dat_dates.to_str(dates[0])}")
print(f"  End: {dat_dates.to_str(dates[-1])}")
print(f"  Total dates: {len(dates)}")

print(f"\nWells: {len(wells)}")
for date, well_name, *_ in wells[:10]:  # First 10
    print(f"  {well_name}")
if len(wells) > 10:
    print(f"  ... and {len(wells)-10} more")

print(f"\nPVT Tables: {len(pvt_tables)}")
```

### Create Modified Input Deck

```python
from rsimpy.cmg.datreader import dat_parser

# Parse original
parser = dat_parser.DatParser()
parser.process("base_case.dat")
data = parser.get()

# Modify data (example conceptual - actual modification depends on data structure)
# data['RUN'] = modify_run_section(data['RUN'])

# Save modified version
parser.save("modified_case.json")

# Can be loaded later for further processing
```

## Related Documentation

- [Getting Started](../getting_started.md)
- [Quick Examples](../quick_examples.md)
- [PVT Interpolation Examples](../quick_examples.md#pvt-interpolation)
