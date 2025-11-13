# Date & Time Management

The Dates component handles simulation time information, timesteps, date conversions, and time-based data filtering.

## Overview

The dates manager provides:
- Timestep queries for each element type
- Date-to-day and day-to-date conversions
- Relative time calculations
- Time-based data filtering
- Support for different element type timesteps (well, grid, sector)

## Getting Timesteps

### get_days(element_type)

Get all available simulation days for an element type.

```python
# Get timesteps for different element types
well_days = sr3.dates.get_days("well")
grid_days = sr3.dates.get_days("grid")
sector_days = sr3.dates.get_days("sector")
```

**Parameters:**
- **element_type** (`str`): Element type to get timesteps for

**Valid Element Types:**
- `"well"` - Well timesteps (typically most frequent)
- `"group"` - Group timesteps (same as wells)
- `"sector"` - Sector timesteps
- `"grid"` - Grid timesteps (typically less frequent than wells)
- `"layer"` - Layer timesteps (same as grid)

**Returns:** `numpy.ndarray` - Array of simulation days (float)

**Note:**
- Different element types may have different timestep frequencies
- Grid timesteps are typically less frequent due to larger output size
- Time is cumulative from simulation start (day 0)

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get timesteps for each element type
well_days = sr3.dates.get_days("well")
grid_days = sr3.dates.get_days("grid")

print(f"Well timesteps: {len(well_days)}")
print(f"  Range: {well_days[0]:.1f} to {well_days[-1]:.1f} days")
print(f"  First 5: {well_days[:5]}")

print(f"\nGrid timesteps: {len(grid_days)}")
print(f"  Range: {grid_days[0]:.1f} to {grid_days[-1]:.1f} days")
print(f"  First 5: {grid_days[:5]}")

# Check timestep frequency
if len(well_days) > 1:
    well_dt = well_days[1:] - well_days[:-1]
    print(f"\nWell timestep stats:")
    print(f"  Average: {well_dt.mean():.2f} days")
    print(f"  Min: {well_dt.min():.2f} days")
    print(f"  Max: {well_dt.max():.2f} days")
```

### get_dates(element_type, date_format)

Get timesteps as formatted date strings.

```python
# Get dates in various formats
dates = sr3.dates.get_dates("well", date_format="%Y-%m-%d")
dates_long = sr3.dates.get_dates("well", date_format="%B %d, %Y")
```

**Parameters:**
- **element_type** (`str`): Element type to get dates for
- **date_format** (`str`, optional): Python strftime format string. Default: `"%Y-%m-%d"`

**Common Date Formats:**
- `"%Y-%m-%d"` - 2020-01-15
- `"%m/%d/%Y"` - 01/15/2020
- `"%d-%b-%Y"` - 15-Jan-2020
- `"%Y-%m-%d %H:%M"` - 2020-01-15 14:30
- `"%B %d, %Y"` - January 15, 2020

**Returns:** `list` of `str` - Formatted date strings

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get dates in different formats
well_days = sr3.dates.get_days("well")
dates_iso = sr3.dates.get_dates("well", "%Y-%m-%d")
dates_us = sr3.dates.get_dates("well", "%m/%d/%Y")
dates_long = sr3.dates.get_dates("well", "%B %d, %Y")

print("First 5 timesteps:")
for day, iso, us, long in zip(well_days[:5], dates_iso[:5], dates_us[:5], dates_long[:5]):
    print(f"  Day {day:6.1f}: {iso} | {us} | {long}")
```

## Date-Time Conversions

### day_to_date(days, date_format)

Convert simulation days to calendar dates.

```python
# Single day
date_str = sr3.dates.day_to_date(365, "%Y-%m-%d")

# Multiple days
days = [0, 30, 90, 365]
dates = sr3.dates.day_to_date(days, "%Y-%m-%d")
```

**Parameters:**
- **days** (`float` or `list`): Simulation day(s) to convert
- **date_format** (`str`, optional): Python strftime format. Default: `"%Y-%m-%d"`

**Returns:** `str` or `list` of `str` - Formatted date string(s)

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Key simulation milestones
milestones = {
    "Start": 0,
    "1 Month": 30,
    "1 Quarter": 90,
    "6 Months": 180,
    "1 Year": 365,
    "2 Years": 730,
}

print("Simulation Milestones:")
for name, day in milestones.items():
    date_str = sr3.dates.day_to_date(day, "%Y-%m-%d")
    print(f"  {name:10s}: Day {day:4.0f} = {date_str}")
```

### date_to_day(date_str, date_format)

Convert calendar dates to simulation days.

```python
# Single date
day = sr3.dates.date_to_day("2020-12-31", "%Y-%m-%d")

# Multiple dates
dates = ["2020-01-01", "2020-06-30", "2020-12-31"]
days = sr3.dates.date_to_day(dates, "%Y-%m-%d")
```

**Parameters:**
- **date_str** (`str` or `list`): Date string(s) to convert
- **date_format** (`str`, optional): Python strftime format. Default: `"%Y-%m-%d"`

**Returns:** `float` or `list` of `float` - Simulation day(s)

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Convert reporting dates to simulation days
reporting_dates = [
    "2020-03-31",  # Q1
    "2020-06-30",  # Q2
    "2020-09-30",  # Q3
    "2020-12-31",  # Q4
]

days = sr3.dates.date_to_day(reporting_dates, "%Y-%m-%d")

print("Quarterly Reporting Days:")
for date, day in zip(reporting_dates, days):
    print(f"  {date}: Day {day:.1f}")

# Use these days to extract data
well_data = sr3.data.get(
    element_type="well",
    properties=["OILRATE", "CUMPROD"],
    days=days
)
```

## Getting Simulation Start Date

### get_start_date(date_format)

Get the simulation start date (corresponds to day 0).

```python
start_date = sr3.dates.get_start_date("%Y-%m-%d")
```

**Parameters:**
- **date_format** (`str`, optional): Python strftime format. Default: `"%Y-%m-%d"`

**Returns:** `str` - Formatted start date

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Get simulation period
start_date = sr3.dates.get_start_date("%Y-%m-%d")
well_days = sr3.dates.get_days("well")
end_day = well_days[-1]
end_date = sr3.dates.day_to_date(end_day, "%Y-%m-%d")

print(f"Simulation Period:")
print(f"  Start: {start_date} (Day 0)")
print(f"  End: {end_date} (Day {end_day:.0f})")
print(f"  Duration: {end_day:.0f} days ({end_day/365:.1f} years)")
```

## Time-Based Data Filtering

### Filtering by Specific Days

```python
# Get data at specific days
well_data = sr3.data.get(
    element_type="well",
    properties=["OILRATE"],
    days=[0, 30, 90, 365]
)

# Extract specific day
rate_day_365 = well_data["OILRATE"].sel(day=365)
```

### Filtering by Date Range

```python
# Get all available days
all_days = sr3.dates.get_days("well")

# Filter by date range
start_day = sr3.dates.date_to_day("2020-01-01", "%Y-%m-%d")
end_day = sr3.dates.date_to_day("2020-06-30", "%Y-%m-%d")

days_in_range = all_days[(all_days >= start_day) & (all_days <= end_day)]

# Get data for date range
well_data = sr3.data.get(
    element_type="well",
    properties=["OILRATE"],
    days=days_in_range.tolist()
)
```

**Example:**

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Define date ranges for quarterly analysis
quarters = [
    ("Q1", "2020-01-01", "2020-03-31"),
    ("Q2", "2020-04-01", "2020-06-30"),
    ("Q3", "2020-07-01", "2020-09-30"),
    ("Q4", "2020-10-01", "2020-12-31"),
]

all_days = sr3.dates.get_days("well")

print("Quarterly Production Analysis:")
for q_name, start_date, end_date in quarters:
    # Convert dates to days
    start_day = sr3.dates.date_to_day(start_date, "%Y-%m-%d")
    end_day = sr3.dates.date_to_day(end_date, "%Y-%m-%d")

    # Filter days in range
    q_days = all_days[(all_days >= start_day) & (all_days <= end_day)]

    if len(q_days) == 0:
        continue

    # Get data
    data = sr3.data.get(
        element_type="well",
        properties=["OILRATE"],
        days=q_days.tolist()
    )

    # Calculate average rate
    rates = data["OILRATE"].values
    avg_rate = np.mean(rates)

    print(f"  {q_name} ({start_date} to {end_date}):")
    print(f"    Timesteps: {len(q_days)}")
    print(f"    Avg rate: {avg_rate:.1f} m³/day")
```

## Practical Examples

### Example 1: Production Timeline Analysis

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import matplotlib.pyplot as plt

sr3 = Sr3Reader("simulation.sr3")

# Get well timesteps
well_days = sr3.dates.get_days("well")
well_dates = sr3.dates.get_dates("well", "%Y-%m-%d")

# Get production data
wells = sr3.elements.get("well")
well_data = sr3.data.get(
    element_type="well",
    properties=["OILRATE", "WATERRATE"],
    elements=wells[:3]  # First 3 wells
)

# Plot production timeline
fig, axes = plt.subplots(len(wells[:3]), 1, figsize=(12, 8))

for i, well in enumerate(wells[:3]):
    oil = well_data["OILRATE"].sel(element=well).values
    water = well_data["WATERRATE"].sel(element=well).values

    axes[i].plot(well_days, oil, label='Oil', linewidth=2)
    axes[i].plot(well_days, water, label='Water', linewidth=2)
    axes[i].set_ylabel('Rate (m³/day)')
    axes[i].set_title(well)
    axes[i].grid(True)
    axes[i].legend()

axes[-1].set_xlabel('Simulation Day')
plt.tight_layout()
plt.savefig('production_timeline.png')
```

### Example 2: Monthly Aggregation

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np
import pandas as pd

sr3 = Sr3Reader("simulation.sr3")

# Get all timesteps
well_days = sr3.dates.get_days("well")

# Get production data
well_data = sr3.data.get(
    element_type="well",
    properties=["OILRATE", "CUMPROD"],
    elements="PROD-1"
)

# Create monthly bins
months = np.arange(0, well_days[-1], 30)
monthly_prod = []

for i in range(len(months) - 1):
    # Days in this month
    month_start = months[i]
    month_end = months[i + 1]

    # Find timesteps in month
    mask = (well_days >= month_start) & (well_days < month_end)
    month_days = well_days[mask]

    if len(month_days) == 0:
        continue

    # Get rates
    rates = well_data["OILRATE"].sel(day=month_days.tolist()).values

    # Calculate average rate for month
    avg_rate = np.mean(rates)

    # Estimate monthly production
    days_in_month = month_end - month_start
    monthly_vol = avg_rate * days_in_month

    monthly_prod.append({
        'month': i + 1,
        'start_day': month_start,
        'end_day': month_end,
        'avg_rate': avg_rate,
        'production': monthly_vol
    })

# Create DataFrame
df = pd.DataFrame(monthly_prod)
print("\nMonthly Production Summary:")
print(df.to_string(index=False))
print(f"\nTotal: {df['production'].sum():,.0f} m³")
```

### Example 3: Compare Timestep Frequencies

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get timesteps for different element types
element_types = ["well", "grid", "sector"]

print("Timestep Analysis:")
for elem_type in element_types:
    try:
        days = sr3.dates.get_days(elem_type)

        if len(days) > 1:
            dt = days[1:] - days[:-1]

            print(f"\n{elem_type.upper()}:")
            print(f"  Number of timesteps: {len(days)}")
            print(f"  Time range: {days[0]:.1f} to {days[-1]:.1f} days")
            print(f"  Average Δt: {dt.mean():.2f} days")
            print(f"  Min Δt: {dt.min():.2f} days")
            print(f"  Max Δt: {dt.max():.2f} days")
            print(f"  Std Δt: {dt.std():.2f} days")

            # Identify timestep changes
            dt_changes = np.where(np.diff(dt) != 0)[0]
            if len(dt_changes) > 0:
                print(f"  Timestep changes: {len(dt_changes)}")
    except:
        print(f"\n{elem_type.upper()}: Not available")
```

### Example 4: Extract Specific Date Data

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3 = Sr3Reader("simulation.sr3")

# Define target dates
target_dates = [
    "2020-12-31",  # End of year 1
    "2021-12-31",  # End of year 2
    "2022-12-31",  # End of year 3
]

# Convert to simulation days
target_days = sr3.dates.date_to_day(target_dates, "%Y-%m-%d")

# Get available days
all_days = sr3.dates.get_days("well")

# Find nearest available days
nearest_days = []
for target_day in target_days:
    # Find nearest day in data
    idx = np.argmin(np.abs(all_days - target_day))
    nearest_day = all_days[idx]
    nearest_days.append(nearest_day)

    # Convert back to date
    actual_date = sr3.dates.day_to_date(nearest_day, "%Y-%m-%d")

    print(f"Target: {sr3.dates.day_to_date(target_day, '%Y-%m-%d')} (Day {target_day:.0f})")
    print(f"  Nearest: {actual_date} (Day {nearest_day:.0f})")
    print(f"  Difference: {abs(nearest_day - target_day):.1f} days")

# Extract data at nearest days
well_data = sr3.data.get(
    element_type="well",
    properties=["CUMPROD"],
    days=nearest_days
)

wells = sr3.elements.get("well")
print("\nYear-End Cumulative Production:")
for day, date in zip(nearest_days, target_dates):
    print(f"\n{date} (Day {day:.0f}):")
    for well in wells[:5]:  # First 5 wells
        cum = well_data["CUMPROD"].sel(element=well, day=day).values
        print(f"  {well}: {cum:,.0f} m³")
```

### Example 5: Calculate Time Periods

```python
from rsimpy.cmg.sr3reader import Sr3Reader
import numpy as np

sr3 = Sr3Reader("simulation.sr3")

# Get timesteps
well_days = sr3.dates.get_days("well")

# Define analysis periods
periods = [
    ("Ramp-up", 0, 90),
    ("Early Production", 90, 365),
    ("First Year", 365, 730),
    ("Second Year", 730, 1095),
    ("Mature", 1095, well_days[-1]),
]

print("Production Period Analysis:")

for period_name, start_day, end_day in periods:
    # Filter days in period
    mask = (well_days >= start_day) & (well_days <= end_day)
    period_days = well_days[mask]

    if len(period_days) == 0:
        continue

    # Get data
    data = sr3.data.get(
        element_type="well",
        properties=["OILRATE"],
        days=period_days.tolist()
    )

    # Calculate statistics
    rates = data["OILRATE"].values

    print(f"\n{period_name} ({start_day:.0f} to {end_day:.0f} days):")
    print(f"  Duration: {end_day - start_day:.0f} days")
    print(f"  Timesteps: {len(period_days)}")
    print(f"  Avg rate: {np.mean(rates):,.1f} m³/day")
    print(f"  Max rate: {np.max(rates):,.1f} m³/day")
    print(f"  Min rate: {np.min(rates):,.1f} m³/day")
```

## Common Patterns

### Get Latest Timestep

```python
last_day = sr3.dates.get_days("well")[-1]
```

### Get First Timestep (Initial Conditions)

```python
first_day = sr3.dates.get_days("well")[0]  # Usually 0
```

### Get Every Nth Timestep

```python
all_days = sr3.dates.get_days("well")
every_10th = all_days[::10]  # Every 10th timestep
```

### Find Nearest Day to Target

```python
import numpy as np

all_days = sr3.dates.get_days("well")
target_day = 365
nearest_idx = np.argmin(np.abs(all_days - target_day))
nearest_day = all_days[nearest_idx]
```

## Related Documentation

- [Properties & Data Access](properties.md)
- [Elements & Hierarchy](elements.md)
- [Plotting & Visualization](plotting.md)
- [SR3Reader Overview](overview.md)
