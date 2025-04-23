# OutReader

Code to read data from CMG output files (.out).

## Class OutWI

Class with code to read well index data in a .out CMG simulation file.

Data is internally stored as a dict with the following structure:

```python
{
    ('date', days): {
        'well_name': {
             # List of values per well
            'number': 1,
            ...
             # List of values per well connection
            'wi': [
                {
                    'wi': 10.0,
                    'ff': 1.0,
                    'cell i': 25,
                    ...
                },
                ...
            ]
        }
    },
    ...
}
```

Actual data stored in dependant on the simulation type. IMEX and GEM simulation output files are currently supported. Well data read in IMEX is the one generated with the command `WPRN WELL LAYER` (in the **TITLE** section) and in GEM with `WELPRN '*' WI` (in the **RUN** section).

### Methods

* process():
  * Process out file.
* get():
  * Return dict with well index data.
* process_and_get():
  * Process file and return well index data.
* get_wells()
  * Return dict of wells and associated dates.
* get_well_dates(self, well_name):
  * Return list of dates associated to the well.
* get_table():
  * Return WI data as a pandas.DataFrame.
* plot_well(well_name):
  * Return matplotlib plot with well WI.