# Quick Examples

This page contains practical examples demonstrating common rsimpy workflows.

## Table of Contents

- [SR3 File Analysis](#sr3-file-analysis)
- [Grid File Operations](#grid-file-operations)
- [DAT File Processing](#dat-file-processing)
- [Template-Based Generation](#template-based-generation)
- [PVT Interpolation](#pvt-interpolation)
- [Visualization](#visualization)

## SR3 File Analysis

### Extract Well Production History

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

# Open SR3 file
sr3 = Sr3Reader("simulation.sr3")

# Get all producer wells
producers = [w for w in sr3.elements.get("well").keys()
             if not w.startswith("I")]

# Extract production data
data = sr3.data.get(
    element_type="well",
    properties=["OILRATSC", "WATRATSC", "GASRATSC", "BHP"],
    elements=producers[:5]  # First 5 producers
)

# Plot oil rates
plt.figure(figsize=(12, 6))
for well in producers[:5]:
    oil_rate = data["OILRATSC"].sel(element=well)
    plt.plot(oil_rate.day, oil_rate.values, label=well)

plt.xlabel("Time (days)")
plt.ylabel("Oil Rate (m³/day)")
plt.legend()
plt.title("Oil Production History")
plt.grid(True)
plt.savefig("oil_production.png")
```

### Calculate EUR (Estimated Ultimate Recovery)

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get cumulative production at last timestep
last_day = sr3.dates.get_days("well")[-1]

eur_data = sr3.data.get(
    element_type="well",
    properties=["NP", "WP", "GP"],
    days=[last_day]
)

# Calculate field totals
field_oil = eur_data["NP"].sel(day=last_day).sum().values
field_water = eur_data["WP"].sel(day=last_day).sum().values
field_gas = eur_data["GP"].sel(day=last_day).sum().values

print(f"Field EUR:")
print(f"  Oil: {field_oil:,.0f} m³")
print(f"  Water: {field_water:,.0f} m³")
print(f"  Gas: {field_gas:,.0f} m³")

# Export per-well EUR
eur_df = eur_data.sel(day=last_day).to_dataframe()
eur_df.to_csv("well_eur.csv")
```

### Monitor Reservoir Pressure Decline

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get average pressure over time
days = sr3.dates.get_days("grid")

avg_pressure = []
for day in days:
    grid_data = sr3.data.get(
        element_type="grid",
        properties=["PRES"],
        elements="MATRIX",
        days=day,
        active_only=True
    )
    avg_pressure.append(grid_data["PRES"].sel(day=day).mean().values)

# Plot pressure decline
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(days, avg_pressure)
plt.xlabel("Time (days)")
plt.ylabel("Average Pressure (kgf/cm²)")
plt.title("Reservoir Pressure Decline")
plt.grid(True)
plt.savefig("pressure_decline.png")
```

### Compare Simulation vs Historical Data

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Read simulation results
sr3 = Sr3Reader("history_match.sr3")

# Read historical data
historical = pd.read_csv("historical_data.csv", parse_dates=['date'])
historical.set_index('date', inplace=True)

# Extract simulation data for matching period
well_name = "PROD-01"
sim_data = sr3.data.get(
    element_type="well",
    properties=["OILRATSC", "WATRATSC"],
    elements=[well_name]
)

# Convert simulation days to dates
sim_dates = [sr3.dates.day2date(d) for d in sim_data.day.values]
sim_oil = sim_data["OILRATSC"].sel(element=well_name).values
sim_water = sim_data["WATRATSC"].sel(element=well_name).values

# Plot comparison
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Oil rate
ax1.plot(sim_dates, sim_oil, 'b-', label='Simulation')
ax1.plot(historical.index, historical['oil_rate'], 'ro', label='Historical')
ax1.set_ylabel("Oil Rate (m³/day)")
ax1.set_title(f"{well_name} - Oil Rate")
ax1.legend()
ax1.grid(True)

# Water rate
ax2.plot(sim_dates, sim_water, 'b-', label='Simulation')
ax2.plot(historical.index, historical['water_rate'], 'ro', label='Historical')
ax2.set_ylabel("Water Rate (m³/day)")
ax2.set_xlabel("Date")
ax2.set_title(f"{well_name} - Water Rate")
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig("history_match_comparison.png")
```

## Grid File Operations

### Modify Permeability Field

```python
from rsimpy.cmg.gridfile import GridFile
import numpy as np

# Read permeability
perm = GridFile("grid/PERMI.inc")
ni, nj, nk = 100, 50, 30
perm.set_shape([ni, nj, nk])

# Get values and apply transformation
values = perm.get_values()

# Apply trend: increase permeability with depth
for k in range(nk):
    start_idx = k * ni * nj
    end_idx = (k + 1) * ni * nj
    multiplier = 1.0 + 0.1 * k / nk  # 0-10% increase
    values[start_idx:end_idx] *= multiplier

# Write modified field
# Note: You'd need to modify internal data structure
# This is a conceptual example
```

### Create Permeability Anisotropy

```python
from rsimpy.cmg.gridfile import GridFile

# Read I-direction permeability
permi = GridFile("grid/PERMI.inc")
ni, nj, nk = 100, 50, 30
permi.set_shape([ni, nj, nk])

# Create J and K permeability with anisotropy
values_i = permi.get_values()
values_j = values_i * 0.8  # 80% of I-direction
values_k = values_i * 0.1  # 10% of I-direction

# Write anisotropic fields
# (Implementation would require creating new GridFile objects)
```

### Extract Subgrid for Local Refinement

```python
from rsimpy.cmg.gridfile import GridFile

# Read full grid properties
properties = ["PERMI", "PERMJ", "PERMK", "PORO", "RTYPE"]

for prop in properties:
    grid = GridFile(f"grid/{prop}.inc")
    grid.set_shape([100, 50, 30])

    # Extract region around well
    well_region = ((40, 60), (20, 30), (10, 25))

    grid.write(
        file_path=f"refined_grid/{prop}_refined.inc",
        coord_range=well_region
    )

print("Extracted refined grid region")
```

## DAT File Processing

### Extract Well Definitions

```python
from rsimpy.cmg.datreader import dat_parser, dat_run

# Parse DAT file
parser = dat_parser.DatParser(
    ignore=['GRID_keys', 'VFP_keys', 'FLUID_keys']
)
parser.process("simulation.dat")
data = parser.get()

# Get well information
wells = dat_run.get_wells(data, keep_only_first=True, verbose=True)

# Print well summary
print(f"Found {len(wells)} wells:")
for date, well_name, *well_data in wells:
    print(f"  {well_name} starting on {date}")
```

### Extract and Modify Schedule Dates

```python
from rsimpy.cmg.datreader import dat_dates, sch_to_daily

# Read dates from DAT file
dates = dat_dates.get_from_dat("simulation.dat")

print(f"Original schedule: {len(dates)} dates")
print(f"First date: {dat_dates.to_str(dates[0])}")
print(f"Last date: {dat_dates.to_str(dates[-1])}")

# Convert to daily timesteps
sch_to_daily.process(
    input_file_path="schedule.dat",
    output_file_path="schedule_daily.dat",
    delta_days=1,
    encoding='utf-8'
)

# Verify new schedule
new_dates = dat_dates.get_from_dat("schedule_daily.dat")
print(f"Daily schedule: {len(new_dates)} dates")
```

### Check Simulation Progress

```python
from rsimpy.cmg.datreader import dat_dates

# Get planned dates from DAT file
planned_dates = dat_dates.get_from_dat("simulation.dat")

# Get actual progress from log file
actual_dates = dat_dates.get_from_log("simulation.out")

# Calculate progress
if len(actual_dates) > 0:
    progress = dat_dates.get_progress(planned_dates, actual_dates[-1])
    print(f"Simulation progress: {progress*100:.1f}%")
    print(f"Completed: {dat_dates.to_str(actual_dates[-1])}")
    print(f"Target: {dat_dates.to_str(planned_dates[-1])}")
```

## Template-Based Generation

### Generate Ensemble for Uncertainty Analysis

```python
from rsimpy.common.template import TemplateProcessor

# Template with uncertain parameters
template = """
** Uncertainty Analysis Case

** Permeability uncertainty
PERMI <\var>kx[float,100,(lognormal,4.6,0.5)]<var>
PERMJ <\var>ky[float,100,(lognormal,4.6,0.5)]<var>
PERMK <\var>kz[float,10,(lognormal,2.3,0.5)]<var>

** Porosity uncertainty
PORO <\var>phi[float,0.25,(truncnormal,0.25,0.05,0.1,0.4)]<var>

** Aquifer uncertainty
AQUIFER_SIZE <\var>aq_size[float,1e6,(uniform,5e5,2e6)]<var>

** Well constraint uncertainty
PROD_RATE <\var>max_rate[float,5000,(normal,5000,500)]<var>
MIN_BHP <\var>min_bhp[float,2000,(uniform,1500,2500)]<var>
"""

# Save template
with open("uncertainty_template.dat", "w") as f:
    f.write(template)

# Generate ensemble
n_realizations = 100
processor = TemplateProcessor(
    template_path="uncertainty_template.dat",
    output_file_path="ensemble/case.dat",
    n_samples=n_realizations,
    verbose=True
)

print(f"Generated {n_realizations} realizations")

# Analyze parameter distributions
samples = processor.experiments_table
print("\nParameter Statistics:")
print(samples.describe())

# Save samples for reference
samples.to_csv("ensemble_parameters.csv", index=False)
```

### Design of Experiments (DoE)

```python
from rsimpy.common.template import TemplateProcessor
import pandas as pd
import itertools

# Define parameter levels for factorial design
parameters = {
    'permeability': [50, 100, 200],
    'porosity': [0.15, 0.25, 0.35],
    'thickness': [30, 50, 70]
}

# Generate full factorial design
combinations = list(itertools.product(*parameters.values()))
doe_df = pd.DataFrame(combinations, columns=parameters.keys())

print(f"Full factorial design: {len(doe_df)} cases")

# Template for DoE
template = """
PERMEABILITY <\var>permeability<var>
POROSITY <\var>porosity<var>
THICKNESS <\var>thickness<var>
"""

# Generate cases
processor = TemplateProcessor(
    template_path="doe_template.dat",
    variables_table=doe_df,
    output_file_path="doe/case.dat",
    n_samples=len(doe_df)
)
```

## PVT Interpolation

### Interpolate PVT Properties

```python
from rsimpy.cmg.datreader import dat_pvt
import numpy as np

# Read PVT table from DAT file
pvt_tables = dat_pvt.get_from_dat("simulation.dat", verbose=False)
pvt = pvt_tables[0]  # First PVT table

# Define conditions to interpolate
rs = np.array([100, 150, 200, 250])
pres = np.array([200, 250, 300, 350])

# Combine into data array
data = np.column_stack([rs, pres])

# Interpolate properties
properties = dat_pvt.get_pvt_values(pvt, data, check_limits=True)

# Display results
import pandas as pd
results_df = pd.DataFrame({
    'Rs': rs,
    'Pressure': pres,
    'Bo': properties['BO'],
    'Bg': properties['BG'],
    'Viscosity_oil': properties['UO'],
    'Viscosity_gas': properties['UG']
})

print(results_df)
```

### Compare PVT Interpolation with Simulation

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from rsimpy.cmg.datreader import dat_pvt
import numpy as np
import matplotlib.pyplot as plt

# Read PVT from DAT file
pvt_tables = dat_pvt.get_from_dat("simulation.dat")
pvt = pvt_tables[0]

# Read results from SR3
sr3 = Sr3Reader("simulation.sr3")
last_day = sr3.dates.get_days("grid")[-1]

grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES", "RS", "BO", "VISO"],
    elements="MATRIX",
    days=last_day
)

# Extract values
pres = grid_data["PRES"].sel(day=last_day).values.flatten()
rs = grid_data["RS"].sel(day=last_day).values.flatten()
bo_sim = grid_data["BO"].sel(day=last_day).values.flatten()

# Interpolate using PVT table
data = np.column_stack([rs, pres])
properties = dat_pvt.get_pvt_values(pvt, data)
bo_interp = properties['BO']

# Compare
plt.figure(figsize=(10, 6))
plt.scatter(bo_sim, bo_interp, alpha=0.5, s=1)
plt.plot([bo_sim.min(), bo_sim.max()], [bo_sim.min(), bo_sim.max()],
         'r--', label='1:1 line')
plt.xlabel("Bo from simulation")
plt.ylabel("Bo from interpolation")
plt.title("PVT Interpolation Validation")
plt.legend()
plt.grid(True)
plt.savefig("pvt_validation.png")

# Calculate correlation
corr = np.corrcoef(bo_sim, bo_interp)[0, 1]
print(f"Correlation: {corr:.6f}")
```

## Visualization

### Interactive Grid Property Map

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.plotting import show, output_file

# Open SR3 file
sr3 = Sr3Reader("simulation.sr3")

# Get available days
days = sr3.dates.get_days("grid")

# Create interactive plot
panel = sr3.plot.plot_map(
    element="matrix",
    property_name="PRES",
    days=[days[0], days[len(days)//2], days[-1]],  # Initial, mid, final
    layers=[50, 60, 70],  # Three layers
    width=1200,
    height=800,
    palette='Viridis',
    log_scale=False,
    add_connections=True,
    contour_step=50
)

# Save to HTML file
output_file("pressure_maps.html")
show(panel)
```

### Animation of Saturation Changes

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get grid dimensions
ni, nj, nk = sr3.grid.get_size("nijk")
layer = 50  # Focus on one layer

# Get saturation data over time
days = sr3.dates.get_days("grid")[::10]  # Every 10th timestep

fig, ax = plt.subplots(figsize=(10, 8))

def update(frame):
    ax.clear()

    data = sr3.data.get(
        element_type="grid",
        properties=["SO"],
        elements="MATRIX",
        days=days[frame],
        active_only=True
    )

    so = data["SO"].sel(day=days[frame]).values

    # Reshape to grid (simplified - may need active cell handling)
    ax.set_title(f"Oil Saturation - Day {days[frame]:.0f}")
    ax.set_xlabel("I")
    ax.set_ylabel("J")

    return ax,

ani = animation.FuncAnimation(fig, update, frames=len(days),
                             interval=200, blit=True)
ani.save("saturation_animation.gif", writer='pillow')
```

## Related Documentation

- [Getting Started](getting_started.md)
- [SR3Reader Overview](sr3reader/overview.md)
- [GridFile Module](gridfile.md)
- [TemplateProcessor](template.md)
