# Installation Guide

## Requirements

### Python Version
- Python 3.7 or higher

### Dependencies

rsimpy requires the following Python packages:

**Core dependencies:**
- `numpy` - Numerical computing
- `pandas` - Data manipulation and analysis
- `xarray` - Multi-dimensional labeled arrays
- `scipy` - Scientific computing and optimization

**Visualization:**
- `matplotlib` - Static plotting
- `bokeh` - Interactive visualizations

**Optional:**
- `h5py` - For HDF5 file support (if needed)
- `netcdf4` - For NetCDF export (if needed)

## Installation Methods

### Method 1: From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/TiagoCAAmorim/simpython.git
cd simpython

# Install in editable mode
pip install -e .
```

This method is recommended if you plan to:
- Modify the source code
- Contribute to development
- Stay updated with latest changes

### Method 2: From Source (Standard)

```bash
# Clone the repository
git clone https://github.com/TiagoCAAmorim/simpython.git
cd simpython

# Install
pip install .
```

### Method 3: Direct from GitHub

```bash
pip install git+https://github.com/TiagoCAAmorim/simpython.git
```

## Verifying Installation

After installation, verify that rsimpy is correctly installed:

```python
# Test import
import rsimpy
print(f"rsimpy imported successfully")

# Check modules
from rsimpy.cmg.sr3reader import Sr3Reader
from rsimpy.cmg.gridfile import GridFile
from rsimpy.common.template import TemplateProcessor
print("All core modules imported successfully")
```

## Virtual Environments

It's recommended to use a virtual environment to avoid conflicts with other packages.

### Using venv (Built-in)

```bash
# Create virtual environment
python -m venv rsimpy_env

# Activate (Linux/Mac)
source rsimpy_env/bin/activate

# Activate (Windows)
rsimpy_env\Scripts\activate

# Install rsimpy
pip install -e /path/to/simpython
```

### Using conda

```bash
# Create conda environment
conda create -n rsimpy python=3.9

# Activate
conda activate rsimpy

# Install dependencies
conda install numpy pandas scipy matplotlib bokeh xarray

# Install rsimpy
pip install -e /path/to/simpython
```

## Troubleshooting

### Import Errors

If you encounter import errors:

```python
ImportError: No module named 'rsimpy'
```

**Solutions:**
1. Ensure rsimpy is installed: `pip list | grep rsimpy`
2. Check your Python path: `import sys; print(sys.path)`
3. Reinstall: `pip install --force-reinstall -e .`

### Dependency Issues

If you have issues with dependencies:

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies manually
pip install numpy pandas scipy matplotlib bokeh xarray

# Then install rsimpy
pip install -e .
```

### Bokeh Plotting Issues

If interactive plotting doesn't work:

```bash
# Ensure bokeh is installed
pip install bokeh

# For Jupyter notebooks
pip install jupyter
```

### SR3 File Reading Issues

If you can't read SR3 files:

**Check file permissions:**
```bash
ls -l simulation.sr3
```

**Verify file format:**
```python
from pathlib import Path

file_path = Path("simulation.sr3")
if file_path.exists():
    print(f"File size: {file_path.stat().st_size} bytes")
else:
    print("File not found")
```

## Platform-Specific Notes

### Windows

- Use forward slashes in file paths or raw strings: `r"C:\path\to\file"`
- Some CMG files may have encoding issues. Try `encoding='latin-1'` if UTF-8 fails

### Linux/Mac

- File paths are case-sensitive
- Ensure proper permissions on CMG files: `chmod +r simulation.sr3`

### Jupyter Notebooks

For use in Jupyter notebooks:

```bash
# Install jupyter
pip install jupyter

# Install ipywidgets for interactive features
pip install ipywidgets

# Enable bokeh extension
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

Example notebook usage:

```python
from rsimpy.cmg.sr3reader import Sr3Reader
from bokeh.io import output_notebook, show

# Enable bokeh in notebook
output_notebook()

# Use rsimpy
sr3 = Sr3Reader("simulation.sr3")
data = sr3.data.get("well", "OILRATSC", "PROD-01")
```

## Updating rsimpy

### If installed with `-e` flag:

```bash
cd /path/to/simpython
git pull origin main
```

Changes are immediately available (no reinstall needed).

### If installed without `-e` flag:

```bash
cd /path/to/simpython
git pull origin main
pip install --upgrade .
```

## Development Setup

For contributing to rsimpy:

```bash
# Clone repository
git clone https://github.com/TiagoCAAmorim/simpython.git
cd simpython

# Create development environment
python -m venv dev_env
source dev_env/bin/activate  # or dev_env\Scripts\activate on Windows

# Install in development mode with dev dependencies
pip install -e .

# Install testing tools
pip install pytest pytest-cov

# Run tests
python -m pytest tests/
```

## Uninstalling

To remove rsimpy:

```bash
pip uninstall rsimpy
```

If installed with `-e`, also remove the repository directory.

## Getting Help

If you encounter issues:

1. Check the [documentation](index.md)
2. Review [examples](quick_examples.md)
3. Check existing issues on GitHub
4. Create a new issue with:
   - Python version: `python --version`
   - rsimpy version: `pip show rsimpy`
   - Error message and traceback
   - Minimal reproducible example

## Next Steps

After successful installation:

1. Read the [Getting Started Guide](getting_started.md)
2. Try [Quick Examples](quick_examples.md)
3. Explore [Module Documentation](index.md#modules-overview)
