# Relative Permeability Tables

The Krel component provides access to relative permeability tables and interpolation functions for calculating kr values at any saturation.

## Overview

The krel manager provides:
- Access to relative permeability tables
- Interpolation for oil, water, and gas kr
- Support for multiple kr sets
- Three-phase behavior (oil, water, gas)
- Integration with grid saturation data

## Getting Kr Tables

### get(kr_set)

Retrieve a relative permeability table.

```python
# Get kr table for set 1
kr_table = sr3.krel.get(1)

# Get kr table for set 2
kr_table = sr3.krel.get(2)
```

**Parameters:**
- **kr_set** (`int`): Kr set number (typically 1, 2, 3, etc.)

**Returns:** `pandas.DataFrame` with columns:
- `sw` - Water saturation
- `krw` - Water relative permeability
- `krow` - Oil rel perm (oil-water system)
- `sl` - Liquid saturation (oil + water)
- `krg` - Gas relative permeability
- `krog` - Oil rel perm (oil-gas system)

**Note:**
- Tables are defined in the CMG input DAT file
- Each rock type can have different kr tables
- Grid property `KRSETN` identifies which kr set each cell uses

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get kr table
kr_table = sr3.krel.get(1)

print("Kr Table 1:")
print(kr_table.head(10))

# Plot kr curves
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Water-oil system
axes[0].plot(kr_table['sw'], kr_table['krw'], label='Krw', marker='o')
axes[0].plot(kr_table['sw'], kr_table['krow'], label='Krow', marker='s')
axes[0].set_xlabel('Water Saturation')
axes[0].set_ylabel('Relative Permeability')
axes[0].set_title('Water-Oil System')
axes[0].legend()
axes[0].grid(True)

# Gas-liquid system
axes[1].plot(1 - kr_table['sl'], kr_table['krg'], label='Krg', marker='o')
axes[1].plot(1 - kr_table['sl'], kr_table['krog'], label='Krog', marker='s')
axes[1].set_xlabel('Gas Saturation')
axes[1].set_ylabel('Relative Permeability')
axes[1].set_title('Gas-Liquid System')
axes[1].legend()
axes[1].grid(True)

plt.tight_layout()
plt.savefig('kr_curves.png')
```

## Interpolating Kr Values

### get_krw(kr_set, sw)

Calculate water relative permeability at given saturations.

```python
# Single saturation
krw = sr3.krel.get_krw(1, 0.35)

# Multiple saturations
sw_values = [0.20, 0.30, 0.40, 0.50]
krw_values = sr3.krel.get_krw(1, sw_values)
```

**Parameters:**
- **kr_set** (`int`): Kr set number
- **sw** (`float` or `array-like`): Water saturation(s)

**Returns:** `float` or `numpy.ndarray` - Interpolated krw value(s)

**Note:**
- Uses linear interpolation between table points
- Extrapolation returns endpoint values
- Handles values outside table range gracefully

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get kr table
kr_table = sr3.krel.get(1)

# Create fine saturation grid
sw_fine = np.linspace(0.15, 0.70, 100)

# Interpolate krw
krw_interp = sr3.krel.get_krw(1, sw_fine)

# Plot original table and interpolation
plt.figure(figsize=(10, 6))
plt.plot(kr_table['sw'], kr_table['krw'], 'o', label='Table', markersize=8)
plt.plot(sw_fine, krw_interp, '-', label='Interpolated', linewidth=2)
plt.xlabel('Water Saturation')
plt.ylabel('Krw')
plt.title('Water Relative Permeability - Interpolation')
plt.legend()
plt.grid(True)
plt.savefig('krw_interpolation.png')
```

### get_krg(kr_set, sg)

Calculate gas relative permeability at given saturations.

```python
# Single saturation
krg = sr3.krel.get_krg(1, 0.25)

# Multiple saturations
sg_values = [0.10, 0.20, 0.30, 0.40]
krg_values = sr3.krel.get_krg(1, sg_values)
```

**Parameters:**
- **kr_set** (`int`): Kr set number
- **sg** (`float` or `array-like`): Gas saturation(s)

**Returns:** `float` or `numpy.ndarray` - Interpolated krg value(s)

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Test gas saturations
sg_test = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])

# Get krg
krg = sr3.krel.get_krg(1, sg_test)

print("Gas Relative Permeability:")
print(f"{'Sg':<8} {'Krg':<10}")
print("-" * 18)
for s, k in zip(sg_test, krg):
    print(f"{s:<8.2f} {k:<10.4f}")
```

### get_kro(kr_set, sw, sg)

Calculate oil relative permeability at given water and gas saturations.

```python
# Single point
kro = sr3.krel.get_kro(1, sw=0.30, sg=0.10)

# Multiple points
sw_values = [0.25, 0.30, 0.35, 0.40]
sg_values = [0.05, 0.10, 0.15, 0.20]
kro_values = sr3.krel.get_kro(1, sw_values, sg_values)
```

**Parameters:**
- **kr_set** (`int`): Kr set number
- **sw** (`float` or `array-like`): Water saturation(s)
- **sg** (`float` or `array-like`): Gas saturation(s)

**Returns:** `float` or `numpy.ndarray` - Interpolated kro value(s)

**Note:**
- Uses Stone's method for three-phase behavior
- Combines krow (from sw) and krog (from sg)
- Oil saturation: so = 1 - sw - sg

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Create saturation grid
sw_range = np.linspace(0.18, 0.60, 20)
sg_range = np.linspace(0.00, 0.40, 20)

# Calculate kro for all combinations
kro_grid = np.zeros((len(sg_range), len(sw_range)))

for i, sg in enumerate(sg_range):
    for j, sw in enumerate(sw_range):
        # Check valid saturations
        if sw + sg < 1.0:
            kro_grid[i, j] = sr3.krel.get_kro(1, sw, sg)
        else:
            kro_grid[i, j] = np.nan

# Plot as contour
plt.figure(figsize=(10, 8))
CS = plt.contourf(sw_range, sg_range, kro_grid, levels=20, cmap='viridis')
plt.colorbar(CS, label='Kro')
plt.xlabel('Water Saturation')
plt.ylabel('Gas Saturation')
plt.title('Oil Relative Permeability')
plt.savefig('kro_surface.png')
```

## Validating Kr Calculations

Compare calculated kr with simulator output:

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get final state
last_day = sr3.dates.get_days("grid")[-1]

# Get saturations and kr from simulator
grid_data = sr3.data.get(
    element_type="grid",
    properties=["KRSETN", "KRO", "KRW", "KRG", "SW", "SG", "SO"],
    elements="MATRIX",
    days=last_day,
    active_only=True
)

# Extract values for kr set 1
kr_setn = grid_data["KRSETN"].sel(day=last_day).values
mask = kr_setn == 1

kro_sim = grid_data["KRO"].sel(day=last_day).values[mask]
krw_sim = grid_data["KRW"].sel(day=last_day).values[mask]
krg_sim = grid_data["KRG"].sel(day=last_day).values[mask]
sw = grid_data["SW"].sel(day=last_day).values[mask]
sg = grid_data["SG"].sel(day=last_day).values[mask]

# Calculate using interpolation
kro_calc = sr3.krel.get_kro(1, sw, sg)
krw_calc = sr3.krel.get_krw(1, sw)
krg_calc = sr3.krel.get_krg(1, sg)

# Compare
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Kro
axes[0].scatter(kro_sim, kro_calc, s=1, alpha=0.5)
axes[0].plot([0, 1], [0, 1], 'r--')
axes[0].set_xlabel('Simulator Kro')
axes[0].set_ylabel('Calculated Kro')
axes[0].set_title(f'Kro (R² = {np.corrcoef(kro_sim, kro_calc)[0,1]**2:.4f})')
axes[0].grid(True)

# Krw
axes[1].scatter(krw_sim, krw_calc, s=1, alpha=0.5)
axes[1].plot([0, 1], [0, 1], 'r--')
axes[1].set_xlabel('Simulator Krw')
axes[1].set_ylabel('Calculated Krw')
axes[1].set_title(f'Krw (R² = {np.corrcoef(krw_sim, krw_calc)[0,1]**2:.4f})')
axes[1].grid(True)

# Krg
axes[2].scatter(krg_sim, krg_calc, s=1, alpha=0.5)
axes[2].plot([0, 1], [0, 1], 'r--')
axes[2].set_xlabel('Simulator Krg')
axes[2].set_ylabel('Calculated Krg')
axes[2].set_title(f'Krg (R² = {np.corrcoef(krg_sim, krg_calc)[0,1]**2:.4f})')
axes[2].grid(True)

plt.tight_layout()
plt.savefig('kr_validation.png')

# Print statistics
print("Validation Results:")
print(f"  Kro R²: {np.corrcoef(kro_sim, kro_calc)[0,1]**2:.6f}")
print(f"  Krw R²: {np.corrcoef(krw_sim, krw_calc)[0,1]**2:.6f}")
print(f"  Krg R²: {np.corrcoef(krg_sim, krg_calc)[0,1]**2:.6f}")
```

## Practical Examples

### Example 1: Compare Multiple Kr Sets

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get multiple kr sets
kr_sets = [1, 2, 3]

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

for kr_set in kr_sets:
    try:
        kr_table = sr3.krel.get(kr_set)

        # Krw vs Sw
        axes[0, 0].plot(kr_table['sw'], kr_table['krw'],
                       label=f'Set {kr_set}', marker='o')

        # Krow vs Sw
        axes[0, 1].plot(kr_table['sw'], kr_table['krow'],
                       label=f'Set {kr_set}', marker='s')

        # Krg vs Sg
        axes[1, 0].plot(1 - kr_table['sl'], kr_table['krg'],
                       label=f'Set {kr_set}', marker='^')

        # Krog vs Sg
        axes[1, 1].plot(1 - kr_table['sl'], kr_table['krog'],
                       label=f'Set {kr_set}', marker='d')
    except:
        print(f"Kr set {kr_set} not available")

axes[0, 0].set_xlabel('Sw')
axes[0, 0].set_ylabel('Krw')
axes[0, 0].set_title('Water Relative Permeability')
axes[0, 0].legend()
axes[0, 0].grid(True)

axes[0, 1].set_xlabel('Sw')
axes[0, 1].set_ylabel('Krow')
axes[0, 1].set_title('Oil Rel Perm (vs Water)')
axes[0, 1].legend()
axes[0, 1].grid(True)

axes[1, 0].set_xlabel('Sg')
axes[1, 0].set_ylabel('Krg')
axes[1, 0].set_title('Gas Relative Permeability')
axes[1, 0].legend()
axes[1, 0].grid(True)

axes[1, 1].set_xlabel('Sg')
axes[1, 1].set_ylabel('Krog')
axes[1, 1].set_title('Oil Rel Perm (vs Gas)')
axes[1, 1].legend()
axes[1, 1].grid(True)

plt.tight_layout()
plt.savefig('kr_sets_comparison.png')
```

### Example 2: Calculate Endpoint Saturations

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get kr table
kr_table = sr3.krel.get(1)

# Water endpoints
swc = kr_table['sw'].min()  # Connate water
sorw = 1 - kr_table['sw'].max()  # Residual oil to water
krw_max = kr_table['krw'].max()

# Find krw at sorw
krw_at_sorw = sr3.krel.get_krw(1, 1 - sorw)

# Gas endpoints
sgc = (1 - kr_table['sl']).min()  # Critical gas
sorg = kr_table['sl'].min()  # Residual oil to gas
krg_max = kr_table['krg'].max()

# Find krg at sorg
krg_at_sorg = sr3.krel.get_krg(1, 1 - sorg)

print("Kr Endpoints:")
print(f"\nWater-Oil System:")
print(f"  Connate water (Swc): {swc:.3f}")
print(f"  Residual oil to water (Sorw): {sorw:.3f}")
print(f"  Krw at (1-Sorw): {krw_at_sorw:.4f}")
print(f"  Krw max: {krw_max:.4f}")

print(f"\nGas-Oil System:")
print(f"  Critical gas (Sgc): {sgc:.3f}")
print(f"  Residual oil to gas (Sorg): {sorg:.3f}")
print(f"  Krg at (1-Sorg): {krg_at_sorg:.4f}")
print(f"  Krg max: {krg_max:.4f}")

# Calculate mobile oil saturation ranges
print(f"\nMobile Oil Ranges:")
print(f"  In water-oil: {swc + sorw:.3f} to {1 - swc:.3f}")
print(f"  In gas-oil: {sorg:.3f} to {1 - sgc:.3f}")
```

### Example 3: Export Kr Tables

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get all available kr sets
kr_sets = [1, 2, 3]

for kr_set in kr_sets:
    try:
        kr_table = sr3.krel.get(kr_set)

        # Export to CSV
        filename = f'kr_table_set{kr_set}.csv'
        kr_table.to_csv(filename, index=False)

        print(f"Exported {filename}")
        print(f"  Rows: {len(kr_table)}")
        print(f"  Columns: {', '.join(kr_table.columns)}")
    except:
        print(f"Kr set {kr_set} not available")
```

### Example 4: Calculate Fractional Flow

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Viscosity assumptions
mu_w = 0.5  # cp
mu_o = 2.0  # cp

# Saturation range
sw_range = np.linspace(0.20, 0.80, 100)

# Get kr values
krw = sr3.krel.get_krw(1, sw_range)
kro = sr3.krel.get_kro(1, sw_range, np.zeros_like(sw_range))  # No gas

# Calculate mobilities
lambda_w = krw / mu_w
lambda_o = kro / mu_o
lambda_t = lambda_w + lambda_o

# Fractional flow
fw = lambda_w / lambda_t

# Plot
fig, axes = plt.subplots(2, 1, figsize=(10, 10))

# Kr curves
axes[0].plot(sw_range, krw, label='Krw')
axes[0].plot(sw_range, kro, label='Kro')
axes[0].set_xlabel('Water Saturation')
axes[0].set_ylabel('Relative Permeability')
axes[0].set_title('Relative Permeability Curves')
axes[0].legend()
axes[0].grid(True)

# Fractional flow
axes[1].plot(sw_range, fw)
axes[1].set_xlabel('Water Saturation')
axes[1].set_ylabel('Water Fractional Flow')
axes[1].set_title(f'Fractional Flow (μw={mu_w} cp, μo={mu_o} cp)')
axes[1].grid(True)

# Find shock front saturation (tangent from Swc)
kr_table = sr3.krel.get(1)
swc = kr_table['sw'].min()

# Calculate derivative
dfw_dsw = np.gradient(fw, sw_range)

# Tangent from Swc
fw_swc = np.interp(swc, sw_range, fw)
tangent_slope = (fw - fw_swc) / (sw_range - swc)

# Find intersection
shock_idx = np.argmax(tangent_slope > dfw_dsw[:-1])
sw_shock = sw_range[shock_idx]
fw_shock = fw[shock_idx]

axes[1].plot([swc, sw_shock], [fw_swc, fw_shock], 'r--',
             label=f'Shock (Sw={sw_shock:.3f})')
axes[1].legend()

plt.tight_layout()
plt.savefig('fractional_flow.png')

print(f"\nBuckley-Leverett Analysis:")
print(f"  Connate water: {swc:.3f}")
print(f"  Shock saturation: {sw_shock:.3f}")
print(f"  Shock fw: {fw_shock:.3f}")
```

### Example 5: Analyze Kr by Rock Type

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get rock types
last_day = sr3.dates.get_days("grid")[-1]

grid_data = sr3.data.get(
    element_type="grid",
    properties=["KRSETN", "PERMI", "POR"],
    elements="MATRIX",
    days=last_day,
    active_only=True
)

kr_setn = grid_data["KRSETN"].sel(day=last_day).values
permi = grid_data["PERMI"].sel(day=last_day).values
por = grid_data["POR"].sel(day=last_day).values

# Analyze each kr set
unique_sets = np.unique(kr_setn).astype(int)

print("Rock Type Analysis:")
for kr_set in unique_sets:
    mask = kr_setn == kr_set
    n_cells = np.sum(mask)

    if n_cells == 0:
        continue

    # Statistics
    avg_perm = np.mean(permi[mask])
    avg_por = np.mean(por[mask])

    # Get kr table
    try:
        kr_table = sr3.krel.get(kr_set)
        swc = kr_table['sw'].min()
        sorw = 1 - kr_table['sw'].max()

        print(f"\nKr Set {kr_set}:")
        print(f"  Cells: {n_cells} ({n_cells/len(kr_setn)*100:.1f}%)")
        print(f"  Avg Permeability: {avg_perm:.2f} md")
        print(f"  Avg Porosity: {avg_por:.3f}")
        print(f"  Swc: {swc:.3f}")
        print(f"  Sorw: {sorw:.3f}")
    except:
        print(f"\nKr Set {kr_set}:")
        print(f"  Cells: {n_cells} ({n_cells/len(kr_setn)*100:.1f}%)")
        print(f"  Table not available")
```

## Common Patterns

### Get All Available Kr Sets

```python
# Try to load kr sets 1-10
available_sets = []
for i in range(1, 11):
    try:
        sr3.krel.get(i)
        available_sets.append(i)
    except:
        pass

print(f"Available Kr sets: {available_sets}")
```

### Calculate Kr at Cell Saturations

```python
# Get saturations from grid
grid_data = sr3.data.get(
    element_type="grid",
    properties=["KRSETN", "SW", "SG"],
    elements="MATRIX",
    days=last_day,
    active_only=True
)

kr_setn = grid_data["KRSETN"].sel(day=last_day).values
sw = grid_data["SW"].sel(day=last_day).values
sg = grid_data["SG"].sel(day=last_day).values

# Calculate kr for each cell using its kr set
kro_calc = np.zeros_like(sw)

for kr_set in np.unique(kr_setn):
    mask = kr_setn == kr_set
    kro_calc[mask] = sr3.krel.get_kro(int(kr_set), sw[mask], sg[mask])
```

## Related Documentation

- [Properties & Data Access](properties.md)
- [Grid Operations](grid.md)
- [SR3Reader Overview](overview.md)
