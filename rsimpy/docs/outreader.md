# OutReader Module

The OutReader module provides tools for extracting data from CMG .out output files, including well index data and connection information.

## Overview

The OutReader module can:

- Detect simulator type (IMEX, GEM, STARS)
- Extract well index (WI) data from output files
- Parse connection information
- Support both IMEX and GEM formats

## Modules

### utils - Utility Functions

#### get_file_type(file_path)

Detect the type of CMG simulator from output file:

```python
from rsimpy.cmg.outreader import utils

file_type = utils.get_file_type("simulation.out")
print(f"Simulator type: {file_type}")
# Returns: 'GEM', 'IMEX', or 'STARS'
```

**Parameters:**
- **file_path** (`str` or `Path`): Path to .out file

**Returns:** `str` - Simulator type ('GEM', 'IMEX', 'STARS')

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file format is not recognized

**Example:**

```python
from rsimpy.cmg.outreader import utils

try:
    file_type = utils.get_file_type("test.out")

    if file_type == 'GEM':
        print("Compositional simulation")
    elif file_type == 'IMEX':
        print("Black oil simulation")
    elif file_type == 'STARS':
        print("Thermal simulation")

except FileNotFoundError:
    print("Output file not found")
except ValueError:
    print("Unrecognized file format")
```

### wi - Well Index Extraction

#### Class: OutWI

Extract well index data from output files.

**Constructor:**

```python
from rsimpy.cmg.outreader import wi

out_wi = wi.OutWI(
    verbose=False,
    wi_only=True,
    encoding='utf-8'
)
```

**Parameters:**
- **verbose** (`bool`, optional): Print progress messages (default: False)
- **wi_only** (`bool`, optional): Extract only well index data (default: True)
- **encoding** (`str`, optional): File encoding (default: 'utf-8')

#### Methods

**process(file_path, prune=True)**

Process output file to extract WI data:

```python
out_wi.process("simulation.out", prune=False)
```

**Parameters:**
- **file_path** (`str` or `Path`): Path to output file
- **prune** (`bool`, optional): Keep only last timestep (default: True)

**get()**

Retrieve extracted well index data:

```python
wi_data = out_wi.get()
# Returns: dict with structure {(date, days): {well_name: {'con_data': [...]}}}
```

**get_table()**

Get well index data as pandas DataFrame:

```python
df = out_wi.get_table()
# Returns: DataFrame with columns for well, date, connection data, etc.
```

**prune()**

Keep only the last timestep data:

```python
out_wi.prune()
```

## Examples

### Example 1: Detect Simulator Type

```python
from rsimpy.cmg.outreader import utils

# Check multiple output files
files = [
    "gem_simulation.out",
    "imex_simulation.out",
    "stars_simulation.out"
]

for file in files:
    try:
        sim_type = utils.get_file_type(file)
        print(f"{file}: {sim_type}")
    except Exception as e:
        print(f"{file}: Error - {e}")
```

### Example 2: Extract Well Index from GEM Output

```python
from rsimpy.cmg.outreader import wi

# Create WI extractor
out_wi = wi.OutWI(verbose=True, wi_only=True, encoding='utf-8')

# Process GEM output file
out_wi.process("gem_simulation.out", prune=False)

# Get data
wi_data = out_wi.get()

print(f"Found {len(wi_data)} timesteps")

# Access specific timestep
for (date, days), wells in wi_data.items():
    print(f"\nTimestep: {date} (day {days})")
    for well_name, well_data in wells.items():
        n_connections = len(well_data['con_data'])
        print(f"  {well_name}: {n_connections} connections")
    break  # Just show first timestep

# Prune to keep only last timestep
out_wi.prune()
print(f"After pruning: {len(out_wi.get())} timesteps")
```

### Example 3: Extract and Analyze WI Data

```python
from rsimpy.cmg.outreader import wi
import pandas as pd
import matplotlib.pyplot as plt

# Extract WI data
out_wi = wi.OutWI(verbose=False, wi_only=True)
out_wi.process("imex_simulation.out", prune=False)

# Get as DataFrame
df = out_wi.get_table()

print("Well Index Data Summary:")
print(f"  Total records: {len(df)}")
print(f"  Wells: {df['well'].nunique()}")
print(f"  Unique wells: {df['well'].unique()}")

# Analyze by well
well_summary = df.groupby('well').size()
print("\nConnections per well:")
print(well_summary)

# Plot connection count evolution (if multiple timesteps)
if 'date' in df.columns or 'days' in df.columns:
    time_col = 'days' if 'days' in df.columns else 'date'
    conn_evolution = df.groupby([time_col, 'well']).size().reset_index(name='count')

    fig, ax = plt.subplots(figsize=(12, 6))
    for well in conn_evolution['well'].unique()[:5]:  # First 5 wells
        well_data = conn_evolution[conn_evolution['well'] == well]
        ax.plot(well_data[time_col], well_data['count'], marker='o', label=well)

    ax.set_xlabel('Time')
    ax.set_ylabel('Number of Connections')
    ax.set_title('Connection Count Evolution')
    ax.legend()
    ax.grid(True)
    plt.savefig('wi_evolution.png')
```

### Example 4: Compare WI Between Cases

```python
from rsimpy.cmg.outreader import wi

# Extract from multiple cases
cases = {
    'Base': 'base_case.out',
    'Optimized': 'optimized_case.out',
    'Sensitivity': 'sensitivity_case.out'
}

wi_comparison = {}

for case_name, file_path in cases.items():
    out_wi = wi.OutWI(verbose=False, wi_only=True)
    out_wi.process(file_path, prune=True)  # Keep only last timestep
    wi_comparison[case_name] = out_wi.get_table()

# Compare connection counts
for case_name, df in wi_comparison.items():
    print(f"\n{case_name}:")
    print(f"  Total connections: {len(df)}")
    print(f"  Wells: {df['well'].nunique()}")

    # Wells with most connections
    top_wells = df['well'].value_counts().head(5)
    print(f"  Top 5 wells by connections:")
    for well, count in top_wells.items():
        print(f"    {well}: {count}")
```

### Example 5: Export WI Data

```python
from rsimpy.cmg.outreader import wi
import pandas as pd

# Extract WI data
out_wi = wi.OutWI(verbose=True)
out_wi.process("simulation.out", prune=False)

# Get as DataFrame
df = out_wi.get_table()

# Export to CSV
df.to_csv("well_index_data.csv", index=False)
print("Exported WI data to CSV")

# Export summary statistics
summary = df.groupby('well').agg({
    'well': 'count'  # Connection count
}).rename(columns={'well': 'connection_count'})

summary.to_csv("wi_summary.csv")
print("Exported summary to CSV")

# If you have connection detail columns, you can analyze them
if 'con_data' in df.columns:
    # Process connection data
    # (actual structure depends on what OutWI extracts)
    pass
```

### Example 6: Monitor Well Index Changes

```python
from rsimpy.cmg.outreader import wi
from pathlib import Path
import time

def monitor_simulation(out_file, interval=60):
    """Monitor simulation progress by checking WI in output file"""

    out_wi = wi.OutWI(verbose=False, wi_only=True)
    last_size = 0

    while True:
        out_path = Path(out_file)

        if not out_path.exists():
            print(f"Waiting for {out_file}...")
            time.sleep(interval)
            continue

        current_size = out_path.stat().st_size

        if current_size > last_size:
            try:
                out_wi.process(out_file, prune=True)
                wi_data = out_wi.get()

                if wi_data:
                    latest = list(wi_data.keys())[-1]
                    date, days = latest
                    n_wells = len(wi_data[latest])

                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                          f"Day {days:.1f} ({date}): {n_wells} wells")

                last_size = current_size

            except Exception as e:
                print(f"Error processing file: {e}")

        time.sleep(interval)

# Usage (run in separate script or background)
# monitor_simulation("simulation.out", interval=30)
```

## Data Structure

The well index data returned by `get()` has the following structure:

```python
{
    (date_str, days_float): {
        'WELL-01': {
            'con_data': [
                # Connection data list
                # Structure depends on simulator type
            ]
        },
        'WELL-02': {...},
        ...
    },
    ...
}
```

The DataFrame returned by `get_table()` typically includes:

- `well`: Well name
- `date`: Date string (if available)
- `days`: Simulation days (if available)
- Additional columns depend on simulator type and connection data

## Performance Considerations

- Large output files can take time to process
- Use `prune=True` if you only need the final timestep
- The `wi_only` option focuses on well index data, making processing faster
- Consider processing in chunks for very large files

## Limitations

- Focused primarily on well index extraction
- Support for IMEX and GEM formats (STARS support may be limited)
- Output file must be well-formed and follow CMG format conventions

## Related Documentation

- [Getting Started](../getting_started.md)
- [DatReader Module](datreader/overview.md) - For input files
- [SR3Reader Module](sr3reader/overview.md) - For results files
- [Quick Examples](../quick_examples.md)
