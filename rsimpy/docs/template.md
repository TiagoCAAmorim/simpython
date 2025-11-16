# TemplateProcessor Module

The `TemplateProcessor` class enables template-based file generation with parameter sampling for uncertainty quantification and sensitivity analysis.

## Overview

TemplateProcessor allows you to:

- Define variables with statistical distributions
- Generate multiple realizations for Monte Carlo simulations
- Import variable values from tables
- Create parametric studies with sampling
- Support various probability distributions

This is particularly useful for:
- Uncertainty quantification workflows
- Sensitivity analysis
- Parameter optimization setups
- Ensemble simulation generation

## Class: TemplateProcessor

### Constructor

```python
from rsimpy.common.template import TemplateProcessor

processor = TemplateProcessor(
    template_path="template.dat",
    variables_table=None,
    output_file_path="output.dat",
    all_uniform=False,
    n_samples=100,
    verbose=False
)
```

**Parameters:**
- **template_path** (`str` or `Path`): Path to template file with variable definitions
- **variables_table** (`str`, `Path`, or `DataFrame`, optional): CSV file or DataFrame with variable values
- **output_file_path** (`str` or `Path`, optional): Output file path for generated files
- **all_uniform** (`bool`, optional): Force all distributions to uniform (default: False)
- **n_samples** (`int`, optional): Number of samples to generate (default: 0, no generation)
- **verbose** (`bool`, optional): Print progress messages (default: False)

**Attributes:**
- `variables`: Dictionary of parsed variables with their specifications
- `experiments_table`: DataFrame containing generated samples

## Variable Definition Syntax

Variables are defined in the template file using the following syntax:

```
<\var>variable_name[type,default_value,(distribution,param1,param2,...)]<var>
```

**Components:**
- **variable_name**: Unique identifier for the variable
- **type** (optional): `int`, `float`, or `str` (inferred if omitted)
- **default_value**: Default value used if no sampling occurs
- **distribution** (optional): Statistical distribution specification

### Supported Distributions

#### 1. Constant
Fixed value, no variation:
```
<\var>var1[float,10.5,(constant,10.5)]<var>
```

#### 2. Uniform
Uniformly distributed between min and max:
```
<\var>var2[int,50,(uniform,10,100)]<var>      # Discrete: 10, 11, ..., 100
<\var>var3[float,0.5,(uniform,0,1)]<var>      # Continuous: [0, 1]
```

**Parameters:** `(uniform, min, max)`

#### 3. Normal (Gaussian)
Normally distributed with mean and standard deviation:
```
<\var>var4[float,100,(normal,100,15)]<var>
```

**Parameters:** `(normal, mean, std_dev)`
**Note:** Unbounded distribution

#### 4. Truncated Normal
Normal distribution bounded by limits:
```
<\var>var5[float,0.25,(truncnormal,0.25,0.05,0.1,0.4)]<var>
```

**Parameters:** `(truncnormal, mean, std_dev, min, max)`

#### 5. Lognormal
Log-normally distributed:
```
<\var>var6[float,1000,(lognormal,7,0.5)]<var>
```

**Parameters:** `(lognormal, log_mean, log_std_dev)`
**Note:** Always positive values

#### 6. Triangular
Triangular distribution with mode:
```
<\var>var7[float,150,(triangular,100,200,150)]<var>
```

**Parameters:** `(triangular, min, max, mode)`

#### 7. Categorical
Discrete values with specified probabilities:
```
<\var>var8[int,2,(categorical,{1,2,3,4},{0.1,0.2,0.3,0.4})]<var>
<\var>var9[str,'type1',(categorical,{type1,type2,type3},{0.5,0.3,0.2})]<var>
```

**Parameters:** `(categorical, {values}, {probabilities})`
**Note:** Probabilities must sum to 1.0

#### 8. Table
Values imported from external table:
```
<\var>var10[float,100,(table)]<var>
```

**Note:** Requires `variables_table` parameter in constructor

### Simplified Syntax

You can omit optional components:

```
<\var>var1<var>                              # Inferred type, requires table
<\var>var2[150]<var>                         # Type inferred, constant value
<\var>var3[(uniform,10,100)]<var>           # Type inferred from distribution
<\var>var4[float,0.25,(normal,0.25,0.05)]<var>  # Full specification
```

## Methods

### generate_experiments()

Generate sample realizations based on variable distributions:

```python
processor.generate_experiments(n_samples=100)
```

**Parameters:**
- **n_samples** (`int`): Number of realizations to generate

**Returns:** None (stores samples in `experiments_table` attribute)

### Accessing Generated Samples

```python
# Access as DataFrame
samples = processor.experiments_table

# Iterate through samples
for idx, row in samples.iterrows():
    perm = row['permeability']
    poro = row['porosity']
    # ... use values
```

### Automatic File Generation

If `output_file_path` and `n_samples` are provided during initialization, files are automatically generated:

```python
processor = TemplateProcessor(
    template_path="template.dat",
    output_file_path="simulation.dat",
    n_samples=50
)
# Creates: simulation_0.dat, simulation_1.dat, ..., simulation_49.dat
```

## Examples

### Example 1: Basic Template with Uniform Sampling

Template file (`template.dat`):
```
** Reservoir Properties
PERMEABILITY <\var>perm[float,100,(uniform,50,500)]<var> md
POROSITY <\var>por[float,0.25,(uniform,0.15,0.35)]<var>
THICKNESS <\var>h[float,50,(normal,50,10)]<var> m
```

Python code:
```python
from rsimpy.common.template import TemplateProcessor

processor = TemplateProcessor(
    template_path="template.dat",
    output_file_path="reservoir.dat",
    n_samples=100,
    verbose=True
)

# Access generated samples
samples = processor.experiments_table
print(f"Generated {len(samples)} realizations")
print(samples.describe())
```

### Example 2: Using External Variable Table

Create variable table (`variables.csv`):
```csv
well_name,rate,pressure
PROD-01,5000,3000
PROD-02,4500,3200
PROD-03,5500,2800
PROD-04,4800,3100
```

Template file:
```
WELL <\var>well_name<var>
  PRODUCER <\var>well_name<var>
  OPERATE MAX STG <\var>rate<var>
  OPERATE BHP <\var>pressure<var>
END
```

Python code:
```python
from rsimpy.common.template import TemplateProcessor
import pandas as pd

# Load variable table
variables = pd.read_csv("variables.csv")

processor = TemplateProcessor(
    template_path="well_template.dat",
    variables_table=variables,
    output_file_path="wells.dat",
    n_samples=len(variables)
)

# Creates wells_0.dat, wells_1.dat, wells_2.dat, wells_3.dat
```

### Example 3: Mixed Distributions

```python
template_text = """
** Uncertainty Analysis Template

** Permeability - Lognormal (typically log-distributed)
PERMI <\var>kx[float,100,(lognormal,4.6,0.5)]<var>
PERMJ <\var>ky[float,100,(lognormal,4.6,0.5)]<var>
PERMK <\var>kz[float,10,(lognormal,2.3,0.5)]<var>

** Porosity - Truncated Normal (physical bounds)
PORO <\var>phi[float,0.25,(truncnormal,0.25,0.05,0.1,0.4)]<var>

** Rock type - Categorical
RTYPE <\var>rock_type[int,1,(categorical,{1,2,3},{0.5,0.3,0.2})]<var>

** Well locations - Uniform integer
WELL_I <\var>well_i[int,50,(uniform,30,70)]<var>
WELL_J <\var>well_j[int,50,(uniform,30,70)]<var>

** Aquifer strength - Triangular (expert judgment)
AQUIFER_STRENGTH <\var>aq_str[float,1e6,(triangular,5e5,2e6,1e6)]<var>
"""

# Write template
with open("uncertainty_template.dat", "w") as f:
    f.write(template_text)

# Generate samples
processor = TemplateProcessor(
    template_path="uncertainty_template.dat",
    output_file_path="case.dat",
    n_samples=500
)

# Analyze samples
import matplotlib.pyplot as plt

samples = processor.experiments_table

fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

for i, col in enumerate(samples.columns):
    if i < len(axes):
        axes[i].hist(samples[col], bins=30, alpha=0.7, edgecolor='black')
        axes[i].set_title(col)
        axes[i].set_xlabel('Value')
        axes[i].set_ylabel('Frequency')

plt.tight_layout()
plt.savefig("sample_distributions.png")
```

### Example 4: Sensitivity Analysis

```python
# Create template for one-at-a-time sensitivity
template = """
PERMEABILITY <\var>perm[float,100]<var>
POROSITY <\var>poro[float,0.25]<var>
THICKNESS <\var>thick[float,50]<var>
"""

# Base case values
base = {'perm': 100, 'poro': 0.25, 'thick': 50}
variations = [-20, -10, 0, 10, 20]  # Percent variations

import pandas as pd

# Generate sensitivity cases
cases = []
for param in base.keys():
    for var in variations:
        case = base.copy()
        case[param] = base[param] * (1 + var/100)
        case['varied_param'] = param
        case['variation_pct'] = var
        cases.append(case)

sensitivity_df = pd.DataFrame(cases)

# Generate files
processor = TemplateProcessor(
    template_path="template.dat",
    variables_table=sensitivity_df,
    output_file_path="sensitivity.dat",
    n_samples=len(sensitivity_df)
)
```

### Example 5: Latin Hypercube Sampling

For more efficient sampling with better coverage:

```python
from scipy.stats import qmc  # SciPy Quasi-Monte Carlo
import numpy as np

# Define ranges
n_samples = 100
n_vars = 3

# Generate LHS samples [0,1]
sampler = qmc.LatinHypercube(d=n_vars, seed=42)
lhs_samples = sampler.random(n=n_samples)

# Transform to desired distributions
import pandas as pd

# Permeability: lognormal
kx = np.exp(qmc.scale(lhs_samples[:, 0], 3, 6))  # ln(kx) ~ [3, 6]

# Porosity: uniform
phi = qmc.scale(lhs_samples[:, 1], 0.15, 0.35)

# Thickness: normal (using quantile function)
from scipy.stats import norm
h = norm.ppf(lhs_samples[:, 2], loc=50, scale=10)

# Create DataFrame
lhs_df = pd.DataFrame({
    'permeability': kx,
    'porosity': phi,
    'thickness': h
})

# Use with template
processor = TemplateProcessor(
    template_path="template.dat",
    variables_table=lhs_df,
    output_file_path="lhs_case.dat",
    n_samples=n_samples
)
```

## Statistical Properties

The generated samples maintain statistical properties of the specified distributions:

```python
import numpy as np

samples = processor.experiments_table

# Verify mean and std dev
for col in samples.columns:
    mean = samples[col].mean()
    std = samples[col].std()
    print(f"{col}: mean={mean:.3f}, std={std:.3f}")

# Check correlations
correlation_matrix = samples.corr()
print(correlation_matrix)

# Goodness of fit tests can be applied as needed
```

## Error Handling

Common errors and their solutions:

```python
try:
    processor = TemplateProcessor("template.dat")
except FileNotFoundError:
    print("Template file not found")

try:
    # Invalid distribution specification
    template = "<\var>var[(invalid,0,1)]<var>"
except ValueError as e:
    print(f"Invalid distribution: {e}")

try:
    # Type mismatch
    template = "<\var>var[str,1.5,(normal,0,1)]<var>"
except ValueError as e:
    print(f"Type inconsistency: {e}")
```

## Best Practices

1. **Variable Naming**: Use descriptive names that match your simulation inputs
2. **Distribution Choice**:
   - Use lognormal for permeability (always positive, typically log-distributed)
   - Use truncated normal for porosity (bounded physically)
   - Use uniform when you have no information
   - Use categorical for discrete choices
3. **Sample Size**:
   - Monte Carlo: 100-1000+ samples for good statistics
   - Sensitivity: 5-10 points per variable
   - Latin Hypercube: Can achieve good coverage with fewer samples
4. **Validation**: Always verify generated samples have expected distributions
5. **Documentation**: Include comments in templates explaining variable choices

## Performance Considerations

- Template parsing is fast even for large templates
- File generation scales linearly with number of samples
- Memory usage depends on number of variables and samples
- Consider batch processing for very large ensembles (>10,000 cases)

## Related Documentation

- [Getting Started](getting_started.md)
- [Quick Examples](quick_examples.md)
- [Interpolation Utilities](interpolation.md)
