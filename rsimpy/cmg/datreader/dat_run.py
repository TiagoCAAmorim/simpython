"""Module to process RUN keywords in CMG data files."""

import re
from datetime import datetime, timedelta
from collections import Counter

try:
    from rsimpy.cmg.datreader.dat_parser import DatParser
    from rsimpy.cmg.datreader import dat_dates, common
except ImportError:
    from dat_parser import DatParser
    import dat_dates
    import common


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
            if len(dates) > 0:
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


if __name__ == '__main__':
    # Example usage
    parser = DatParser(ignore=['GRID_keys', 'VFP_keys', 'FLUID_keys'])
    parser.process('tests/_no_sync/ex/dat/base_case_bo.dat')
    data_ = parser.get()

    wells_ = get_wells(data_, keep_only_first=True, verbose=True)
    for date, w in wells_:
        print(f'Well: {w}, Date: {date}')
