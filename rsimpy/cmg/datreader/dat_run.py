"""
Module to process RUN keywords in CMG data files.

Functions:
---------
get_wells(data, keep_only_first=False, verbose=False):
    Get list of wells and associated dates from a CMG dat file processed data.
get_well_key(data, keyword, verbose=False):
    Get list of values associated to wells from a CMG dat file processed data.
"""

try:
    from rsimpy.cmg.datreader import dat_dates, common
except ImportError:
    import dat_dates
    import common
import fnmatch


def get_wells(data, keep_only_first=False, verbose=False): # pylint: disable=too-many-branches
    """
    Get list of wells and associated dates from a CMG dat file processed data.

    Parameters
    ----------
    data : dict of lists
        Dictionary with the processed data from the dat file.
        This is the output of the DatParser.get() method.
    keep_only_first : bool
        If True, keep only the first date for each well. Default: False.
    verbose : bool
        Print messages. Default: False.

    Returns
    -------
    list of (datetime, str)
        List of tuples with well names and associated dates.
    """
    dates = []
    wells = []
    for line in common.get_section(data,'RUN'):
        if not dat_dates.solve_dates(dates, line):
            solve_wells(wells, dates, line, keep_only_first)

    if len(wells) == 0:
        if verbose:
            print('No WELL keywords found.')

    return wells


def solve_wells(wells, dates, line, keep_only_first=False):
    """Solve WELL keywords from the line."""
    if line[0] == 'WELL':
        well = line[1][1:-1]
        if len(dates) == 0:
            raise ValueError("No DATE found before WELL. Invalid data.")
        if keep_only_first:
            if well in [w[1] for w in wells]:
                return True
        wells.append((dates[-1], well))
        return True
    return False


def get_well_key(data, keyword, verbose=False): # pylint: disable=too-many-branches
    """
    Get list of values associated to wells from a CMG dat file processed data.

    The keyword should have the format:
       KEYWORD 'WELL_NAME1' 'WELL_NAME2' ... 'WELL_NAME_N'
       VALUE1 VALUE2 ... VALUE_N

    WELL_NAME can use * as wildcard.
    If only one value is found, it is assumed the same for all wells.

    Parameters
    ----------
    data : dict of lists
        Dictionary with the processed data from the dat file.
        This is the output of the DatParser.get() method.
    keyword : str
        Keyword to search for.
    keep_only_first : bool
        If True, keep only the first date for each well. Default: False.
    verbose : bool
        Print messages. Default: False.

    Returns
    -------
    list of (datetime, str, float)
        List of tuples with well names and associated dates and values.
    """
    dates = []
    wells = []
    key_data = []
    for line in common.get_section(data,'RUN'):
        if not dat_dates.solve_dates(dates, line):
            if not solve_wells(wells, dates, line):
                solve_well_key(key_data, wells, dates, keyword, line, verbose)

    if len(key_data) == 0:
        if verbose:
            print(f'No {keyword} keywords found.')

    return key_data


def solve_well_key(key_data, wells, dates, keyword, line, verbose=False):
    """Solve WELL keywords from the line."""
    if line[0] == keyword:
        if len(dates) == 0:
            raise ValueError(f"No DATE found before {keyword}. Invalid data.")
        if len(wells) == 0:
            raise ValueError(f"No WELL found before {keyword}. Invalid data.")
        if len(line) < 2:
            raise ValueError(f"Keyword {keyword} has no values. Invalid data.")

        wells_key = [w[1:-1] for w in line[1:] if w[0] == "'" and w[-1] == "'"]
        if len(wells_key) == 0:
            raise ValueError(f"Keyword {keyword} has no wells. Invalid data.")
        values = [float(v) for v in line[1:] if "'" not in v]
        if len(values) == 0:
            raise ValueError(f"Keyword {keyword} has no values. Invalid data.")
        if len(values) + len(wells_key) != len(line) - 1:
            msg = f"Error reading {keyword}. "
            msg += f"Read {len(line) - 1} options, "
            msg += f"but found {len(values)} values and {len(wells_key)} wells."
            raise ValueError(msg)
        if len(values) == 1:
            values = [values[0]] * len(wells_key)


        def _add_well(date, well, value):
            for i, (d,w,_) in enumerate(key_data):
                if d == date and w == well:
                    key_data[i] = (date, well, value)
                    return
            key_data.append((date, well, value))

        wells = list({w[1] for w in wells})
        wells.sort()
        for well, value in zip(wells_key, values):
            if '*' in well:
                for w in [s for s in wells if fnmatch.fnmatch(s, well)]:
                    _add_well(dates[-1], w, value)
            else:
                if well not in wells:
                    if verbose:
                        msg = f"Well {well} not found."
                        raise ValueError(msg)
                    continue
                _add_well(dates[-1], well, value)
        return True
    return False


if __name__ == '__main__':
    print(__doc__)
