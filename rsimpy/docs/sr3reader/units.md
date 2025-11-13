# Unit Management

The Units component handles unit conversions, unit queries, and custom unit definitions for simulation properties.

## Overview

The units manager provides:
- Query units for any property
- Convert values between unit systems
- Set custom units for properties
- Support for CMG standard units
- Field, Metric, and SI unit systems

## Querying Property Units

### get_unit(property_name)

Get the current unit for a property.

```python
# Query units for properties
pres_unit = sr3.units.get_unit("PRES")
rate_unit = sr3.units.get_unit("OILRATE")
cum_unit = sr3.units.get_unit("CUMPROD")

print(f"Pressure unit: {pres_unit}")
print(f"Rate unit: {rate_unit}")
print(f"Cumulative unit: {cum_unit}")
```

**Parameters:**
- **property_name** (`str`): Property name (as used in data.get())

**Returns:** `str` - Unit string

**Common Properties and Units:**

Pressure:
- `PRES` - kPa, psia, bar

Rates:
- `OILRATE`, `GASRATE`, `WATERRATE` - m³/day, bbl/day, stb/day

Cumulative:
- `CUMPROD`, `CUMINJECTED` - m³, bbl, stb

Saturations:
- `SO`, `SG`, `SW` - fraction (dimensionless)

Grid Properties:
- `BLOCKPVOL` - m³, bbl
- `POR` - fraction (dimensionless)
- `PERMI`, `PERMJ`, `PERMK` - md (millidarcy)

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Query units for common properties
properties = [
    "PRES", "TEMP",
    "OILRATE", "GASRATE", "WATERRATE",
    "CUMPROD", "CUMINJECTED",
    "SO", "SG", "SW",
    "PERMI", "POR", "BLOCKPVOL"
]

print("Property Units:")
for prop in properties:
    try:
        unit = sr3.units.get_unit(prop)
        print(f"  {prop:15s}: {unit}")
    except:
        print(f"  {prop:15s}: Not available")
```

## Unit Systems

CMG simulators support different unit systems:

### Metric Units (SI)
- Pressure: kPa
- Rate: m³/day
- Volume: m³
- Temperature: °C
- Permeability: md

### Field Units
- Pressure: psia
- Rate: stb/day (stock tank barrels)
- Volume: stb
- Temperature: °F
- Permeability: md

### Lab Units
- Pressure: atm, bar
- Rate: cm³/s
- Volume: cm³
- Temperature: °C, K

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Check current unit system
print("Current Unit System:")
print(f"  Pressure: {sr3.units.get_unit('PRES')}")
print(f"  Oil Rate: {sr3.units.get_unit('OILRATE')}")
print(f"  Gas Rate: {sr3.units.get_unit('GASRATE')}")
print(f"  Temperature: {sr3.units.get_unit('TEMP')}")

# Determine unit system
pres_unit = sr3.units.get_unit("PRES")
if pres_unit == "kPa":
    print("\nUsing METRIC units")
elif pres_unit == "psia":
    print("\nUsing FIELD units")
elif pres_unit in ["atm", "bar"]:
    print("\nUsing LAB units")
```

## Unit Conversions

### Manual Conversions

Common conversion factors:

```python
# Pressure
kPa_to_psia = 0.145038
psia_to_kPa = 6.89476
kPa_to_bar = 0.01
bar_to_kPa = 100

# Volume
m3_to_bbl = 6.28981
bbl_to_m3 = 0.158987

# Temperature
def celsius_to_fahrenheit(c):
    return c * 9/5 + 32

def fahrenheit_to_celsius(f):
    return (f - 32) * 5/9

# Permeability (already in md)
# Porosity (dimensionless fraction)
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get pressure data
well_data = sr3.data.get(
    element_type="well",
    properties=["PRES"],
    elements="PROD-1",
    days=365
)

pres_kPa = well_data["PRES"].sel(day=365).values[0]

# Convert to other units
pres_psia = pres_kPa * 0.145038
pres_bar = pres_kPa * 0.01
pres_atm = pres_kPa * 0.00986923

print(f"Bottom-hole Pressure at Day 365:")
print(f"  {pres_kPa:.1f} kPa")
print(f"  {pres_psia:.1f} psia")
print(f"  {pres_bar:.1f} bar")
print(f"  {pres_atm:.2f} atm")
```

### Volume Conversions

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get cumulative production
well_data = sr3.data.get(
    element_type="well",
    properties=["CUMPROD"],
    elements="PROD-1"
)

cum_m3 = well_data["CUMPROD"].values[-1]

# Convert to other units
cum_bbl = cum_m3 * 6.28981
cum_MMbbl = cum_bbl / 1e6

print(f"Cumulative Oil Production:")
print(f"  {cum_m3:,.0f} m³")
print(f"  {cum_bbl:,.0f} bbl")
print(f"  {cum_MMbbl:.2f} MMbbl")
```

## Setting Custom Units

### set_unit(property_name, unit)

Change the unit for a property (affects subsequent data retrieval).

```python
# Change pressure unit to psia
sr3.units.set_unit("PRES", "psia")

# Change rate units to bbl/day
sr3.units.set_unit("OILRATE", "bbl/day")
sr3.units.set_unit("GASRATE", "bbl/day")
```

**Parameters:**
- **property_name** (`str`): Property name
- **unit** (`str`): New unit string

**Note:**
- This affects how data is read from the SR3 file
- Conversions are applied automatically
- Changes persist for the SR3Reader instance

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get data in original units
print(f"Original pressure unit: {sr3.units.get_unit('PRES')}")
well_data = sr3.data.get(
    element_type="well",
    properties=["PRES"],
    elements="PROD-1",
    days=365
)
pres_original = well_data["PRES"].sel(day=365).values[0]
print(f"Pressure: {pres_original:.1f} {sr3.units.get_unit('PRES')}")

# Change to psia
sr3.units.set_unit("PRES", "psia")
print(f"\nNew pressure unit: {sr3.units.get_unit('PRES')}")

# Get data again (now in psia)
well_data = sr3.data.get(
    element_type="well",
    properties=["PRES"],
    elements="PROD-1",
    days=365
)
pres_psia = well_data["PRES"].sel(day=365).values[0]
print(f"Pressure: {pres_psia:.1f} {sr3.units.get_unit('PRES')}")
```

## Practical Examples

### Example 1: Create Unit Conversion Report

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get final day
last_day = sr3.dates.get_days("well")[-1]

# Get production data
wells = sr3.elements.get("well")[:5]  # First 5 wells
well_data = sr3.data.get(
    element_type="well",
    properties=["CUMPROD"],
    elements=wells,
    days=last_day
)

print(f"Cumulative Production at Day {last_day:.0f}:\n")
print(f"{'Well':<15} {'m³':>12} {'bbl':>12} {'MMbbl':>10}")
print("-" * 52)

for well in wells:
    cum_m3 = well_data["CUMPROD"].sel(element=well, day=last_day).values
    cum_bbl = cum_m3 * 6.28981
    cum_MMbbl = cum_bbl / 1e6

    print(f"{well:<15} {cum_m3:>12,.0f} {cum_bbl:>12,.0f} {cum_MMbbl:>10.2f}")

# Total
total_m3 = well_data["CUMPROD"].sel(day=last_day).sum().values
total_bbl = total_m3 * 6.28981
total_MMbbl = total_bbl / 1e6

print("-" * 52)
print(f"{'TOTAL':<15} {total_m3:>12,.0f} {total_bbl:>12,.0f} {total_MMbbl:>10.2f}")
```

### Example 2: Multi-Unit Rate Comparison

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get rate data
well_days = sr3.dates.get_days("well")
well_data = sr3.data.get(
    element_type="well",
    properties=["OILRATE"],
    elements="PROD-1"
)

# Get rates in original units
rate_m3d = well_data["OILRATE"].values

# Convert to other units
rate_bpd = rate_m3d * 6.28981
rate_stbd = rate_bpd  # Assuming stock tank conditions

# Plot
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

axes[0].plot(well_days, rate_m3d)
axes[0].set_ylabel('Rate (m³/day)')
axes[0].set_title('PROD-1 Oil Rate')
axes[0].grid(True)

axes[1].plot(well_days, rate_bpd)
axes[1].set_ylabel('Rate (bbl/day)')
axes[1].grid(True)

axes[2].plot(well_days, rate_stbd)
axes[2].set_ylabel('Rate (stb/day)')
axes[2].set_xlabel('Simulation Day')
axes[2].grid(True)

plt.tight_layout()
plt.savefig('multi_unit_rates.png')
```

### Example 3: Pressure Conversion Chart

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get pressure range from grid
last_day = sr3.dates.get_days("grid")[-1]
grid_data = sr3.data.get(
    element_type="grid",
    properties=["PRES"],
    elements="MATRIX",
    days=last_day,
    active_only=True
)

pres_kPa = grid_data["PRES"].sel(day=last_day).values

# Convert to different units
pres_psia = pres_kPa * 0.145038
pres_bar = pres_kPa * 0.01
pres_atm = pres_kPa * 0.00986923

# Create comparison plot
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

axes[0, 0].hist(pres_kPa, bins=50)
axes[0, 0].set_xlabel('Pressure (kPa)')
axes[0, 0].set_title('kPa Distribution')
axes[0, 0].grid(True)

axes[0, 1].hist(pres_psia, bins=50)
axes[0, 1].set_xlabel('Pressure (psia)')
axes[0, 1].set_title('psia Distribution')
axes[0, 1].grid(True)

axes[1, 0].hist(pres_bar, bins=50)
axes[1, 0].set_xlabel('Pressure (bar)')
axes[1, 0].set_title('bar Distribution')
axes[1, 0].grid(True)

axes[1, 1].hist(pres_atm, bins=50)
axes[1, 1].set_xlabel('Pressure (atm)')
axes[1, 1].set_title('atm Distribution')
axes[1, 1].grid(True)

plt.tight_layout()
plt.savefig('pressure_units.png')

# Statistics
print("Pressure Statistics:")
print(f"\n  kPa:  {np.mean(pres_kPa):.1f} ± {np.std(pres_kPa):.1f}")
print(f"  psia: {np.mean(pres_psia):.1f} ± {np.std(pres_psia):.1f}")
print(f"  bar:  {np.mean(pres_bar):.1f} ± {np.std(pres_bar):.1f}")
print(f"  atm:  {np.mean(pres_atm):.1f} ± {np.std(pres_atm):.1f}")
```

### Example 4: Export with Unit Labels

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import pandas as pd

sr3 = Sr3Reader("simulation.sr3")

# Get well data
wells = sr3.elements.get("well")
well_days = sr3.dates.get_days("well")

well_data = sr3.data.get(
    element_type="well",
    properties=["OILRATE", "GASRATE", "WATERRATE", "CUMPROD"],
    elements=wells[:5]
)

# Get units
oil_rate_unit = sr3.units.get_unit("OILRATE")
gas_rate_unit = sr3.units.get_unit("GASRATE")
water_rate_unit = sr3.units.get_unit("WATERRATE")
cum_unit = sr3.units.get_unit("CUMPROD")

# Create DataFrame for last day
last_day = well_days[-1]
data_list = []

for well in wells[:5]:
    data_list.append({
        'Well': well,
        f'Oil Rate ({oil_rate_unit})': well_data["OILRATE"].sel(element=well, day=last_day).values,
        f'Gas Rate ({gas_rate_unit})': well_data["GASRATE"].sel(element=well, day=last_day).values,
        f'Water Rate ({water_rate_unit})': well_data["WATERRATE"].sel(element=well, day=last_day).values,
        f'Cumulative ({cum_unit})': well_data["CUMPROD"].sel(element=well, day=last_day).values,
    })

df = pd.DataFrame(data_list)

# Export to CSV with units in column names
df.to_csv("well_production_with_units.csv", index=False)

print(f"Production Summary at Day {last_day:.0f}:")
print(df.to_string(index=False))
```

### Example 5: Temperature Conversion

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get temperature data
last_day = sr3.dates.get_days("grid")[-1]
grid_data = sr3.data.get(
    element_type="grid",
    properties=["TEMP"],
    elements="MATRIX",
    days=last_day,
    active_only=True
)

temp_c = grid_data["TEMP"].sel(day=last_day).values

# Convert to Fahrenheit and Kelvin
temp_f = temp_c * 9/5 + 32
temp_k = temp_c + 273.15

print("Temperature Statistics:")
print(f"\n  Celsius:")
print(f"    Mean: {np.mean(temp_c):.1f} °C")
print(f"    Range: {np.min(temp_c):.1f} to {np.max(temp_c):.1f} °C")

print(f"\n  Fahrenheit:")
print(f"    Mean: {np.mean(temp_f):.1f} °F")
print(f"    Range: {np.min(temp_f):.1f} to {np.max(temp_f):.1f} °F")

print(f"\n  Kelvin:")
print(f"    Mean: {np.mean(temp_k):.1f} K")
print(f"    Range: {np.min(temp_k):.1f} to {np.max(temp_k):.1f} K")
```

## Unit Conversion Reference

### Pressure

```python
# From kPa
kPa_to_psia = 0.145038
kPa_to_bar = 0.01
kPa_to_atm = 0.00986923
kPa_to_MPa = 0.001

# From psia
psia_to_kPa = 6.89476
psia_to_bar = 0.0689476
psia_to_atm = 0.068046

# From bar
bar_to_kPa = 100
bar_to_psia = 14.5038
bar_to_atm = 0.986923
```

### Volume

```python
# Oil/Liquid
m3_to_bbl = 6.28981
bbl_to_m3 = 0.158987
m3_to_ft3 = 35.3147
ft3_to_m3 = 0.0283168

# Gas
m3_to_scf = 35.3147  # Standard cubic feet
scf_to_m3 = 0.0283168
m3_to_Mscf = 0.0353147  # Thousand scf
```

### Rate

```python
# Oil rate
m3d_to_bpd = 6.28981
bpd_to_m3d = 0.158987

# Gas rate
m3d_to_scfd = 35.3147
scfd_to_m3d = 0.0283168
m3d_to_Mscfd = 0.0353147
```

### Temperature

```python
def celsius_to_fahrenheit(c):
    return c * 9/5 + 32

def fahrenheit_to_celsius(f):
    return (f - 32) * 5/9

def celsius_to_kelvin(c):
    return c + 273.15

def kelvin_to_celsius(k):
    return k - 273.15
```

### Permeability

Typically already in millidarcy (md):
```python
# md to Darcy
md_to_d = 0.001
d_to_md = 1000

# md to m²
md_to_m2 = 9.869233e-16
m2_to_md = 1.01325e15
```

## Common Unit Queries

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get all relevant units
units_dict = {
    "Pressure": sr3.units.get_unit("PRES"),
    "Temperature": sr3.units.get_unit("TEMP"),
    "Oil Rate": sr3.units.get_unit("OILRATE"),
    "Gas Rate": sr3.units.get_unit("GASRATE"),
    "Water Rate": sr3.units.get_unit("WATERRATE"),
    "Cumulative Oil": sr3.units.get_unit("CUMPROD"),
    "Grid Volume": sr3.units.get_unit("BLOCKPVOL"),
    "Porosity": "fraction",
    "Permeability": "md",
    "Saturation": "fraction",
}

print("Simulation Units:")
for prop, unit in units_dict.items():
    print(f"  {prop:<20}: {unit}")
```

## Related Documentation

- [Properties & Data Access](properties.md)
- [Grid Operations](grid.md)
- [Dates & Time Management](dates.md)
- [SR3Reader Overview](overview.md)
