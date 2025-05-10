"""
Module to PVT tables from CMG dat files.

Functions
---------
get_from_dat(file_path, abs_path=None, encoding='utf-8', verbose=False):
    Get PVT tables from a CMG dat file.
get_pvt_from_dat_data(data, verbose=False):
    Get PVTtables from a CMG dat file processed data.
"""
import numpy as np
import pandas as pd

try:
    from rsimpy.cmg.datreader.dat_parser import DatParser
    from rsimpy.cmg.datreader import common
except ImportError:
    from dat_parser import DatParser
    import common


COLS = ['PSAT', 'PRES', 'RS', 'BO', 'EG', 'UO', 'UG']


def get_from_dat(file_path, abs_path=None, encoding='utf-8', verbose=False, _debug=False):
    """
    Get PVT tables from a CMG dat file.

    It is assumed that the PVT tables are in the IMEX format, and that
    gas-oil interfacial tension (srftn) and oil compressibility (co) are
    not included in the PVT tables.
    Data is read from the PVT, BOT and VOT keywords.

    Parameters
    ----------
    file_path : str
        Path to the dat file.
    abs_path : dict
        Dictionary with changes to absolute pathes. Keys are the
        strings to be searched in the start of the include path,
        and values are the strings to replace any positive search.
        If None, no search is performed. Default: None.
    encoding : str
        File encoding. Default: 'utf-8'.
    verbose : bool
        Print messages. Default: False.

    Returns
    -------
    list of dicts
        List of dictionaries with the PVT tables.
        Each dictionary has the following keys:
        - 'Psat': Saturation pressure.
        - 'Pres': Pressure.
        - 'Rs': Solution gas-oil.
        - 'Bo': Oil formation volume factor.
        - 'Eg': Gas expansion factor.
        - 'Uo': Oil viscosity.
        - 'Ug': Gas viscosity.
    """
    parser = DatParser(
        abs_path=abs_path,
        encoding=encoding,
        ignore=['TITLE1','ROCKFLUID','INITIAL','NUMERICAL','RUN','GRID_keys'],
        verbose=verbose,
        _debug=_debug)
    parser.process(file_path=file_path)

    return get_from_dat_data(parser.get(), verbose=verbose)


def get_from_dat_data(data, verbose=False): # pylint: disable=too-many-branches
    """
    Get PVT tables from a CMG dat file processed data.

    It is assumed that the PVT tables are in the IMEX format, and that
    gas-oil interfacial tension (srftn) and oil compressibility (co) are
    not included in the PVT tables.
    Data is read from the PVT, BOT and VOT keywords.

    Parameters
    ----------
    file_path : str
        Path to the dat file.
    abs_path : dict
        Dictionary with changes to absolute pathes. Keys are the
        strings to be searched in the start of the include path,
        and values are the strings to replace any positive search.
        If None, no search is performed. Default: None.
    encoding : str
        File encoding. Default: 'utf-8'.
    verbose : bool
        Print messages. Default: False.

    Returns
    -------
    list of dicts
        List of dictionaries with the PVT tables.
        Each dictionary has the following keys:
        - 'Psat': Saturation pressure.
        - 'Pres': Pressure.
        - 'Rs': Solution gas-oil.
        - 'Bo': Oil formation volume factor.
        - 'Eg': Gas expansion factor.
        - 'Uo': Oil viscosity.
        - 'Ug': Gas viscosity.
    """
    data = common.get_section(data, 'GRID')

    tables = []
    table = {}
    for line in data:
        if line[0] == 'PVT':
            if len(table) != 0:
                tables.append(_process_table(table, len(tables), verbose=verbose))
            table = {'PVT': line, 'BOT':[], 'VOT': []}
        elif line[0] == 'BOT':
            if len(table) == 0:
                raise ValueError("BOT keyword found before PVT keyword.")
            table['BOT'].append(line)
        elif line[0] == 'VOT':
            if len(table) == 0:
                raise ValueError("VOT keyword found before PVT keyword.")
            table['VOT'].append(line)
    if len(table) != 0:
        tables.append(_process_table(table, len(tables), verbose=verbose))

    if len(tables) == 0:
        if verbose:
            print('No PVT keywords found.')

    return tables


def _process_table(table, num_tables, verbose=False):
    """Process a PVT table."""
    pvt = _process_pvt(table['PVT'], num_tables, verbose)
    bot = _process_bot_vot(table['BOT'], pvt, 'BO')
    vot = _process_bot_vot(table['VOT'], pvt, 'UO')

    for col in COLS:
        pvt[col] = np.concatenate((pvt[col], bot[col], vot[col]))

    table = pd.DataFrame(pvt)

    # TODO: Interpolate missing values: 1/Bo and 1/BoUo

    return table


def _process_bot_vot(tables, pvt, col_name):
    """Process BOT or VOT tables."""
    if col_name not in ['BO', 'UO']:
        raise ValueError(f"Invalid column name: {col_name}. Expected 'BO' or 'UO'.")

    output = {k: np.array([]) for k in COLS}
    for table in tables:
        values = np.array(table[1:], dtype=float).reshape(-1, 2)
        if len(values) == 0:
            raise ValueError("No values found in BOT keyword.")

        psat_values = pvt['PSAT']
        rs_values = pvt['RS']
        interpolated_rs = np.interp(values[0, 0], psat_values, rs_values, left=np.nan, right=np.nan)

        data = {
            'PSAT': np.full(values.shape[0], values[0, 0]),
            'PRES': values[:, 0],
            'RS': np.full(values.shape[0], interpolated_rs),
            col_name: values[:, 1],
            'EG': np.interp(values[:, 0], pvt['PRES'], pvt['EG'], left=np.nan, right=np.nan),
            'UG': np.interp(values[:, 0], pvt['PRES'], pvt['UG'], left=np.nan, right=np.nan),
            'NAN': np.full(values.shape[0], np.nan),
        }

        for col in COLS:
            if col not in data:
                output[col] = np.concatenate((output[col], data['NAN']))
            else:
                output[col] = np.concatenate((output[col], data[col]))
    return output


def _process_pvt(table, num_tables, verbose):
    gas_col = 'EG'
    i0 = 1
    try:
        table_number = int(table[i0])
    except ValueError:
        gas_col = table[1]
        i0 = 2

        try:
            table_number = int(table[i0])
        except ValueError:
            table_number = 1
            i0 = 1

    if verbose:
        print(f"Found Table: {gas_col} {table_number}")
    if table_number != num_tables+1:
        msg = f"Table number {table_number} does not match expected {num_tables+1}."
        raise ValueError(msg)

    if gas_col == 'ZG':
        raise ValueError("Gas compressibility factor (ZG) is not supported yet.")

    values = table[i0+1:]
    values = np.array(values, dtype=float).reshape(-1, 6)

    if gas_col == 'BG':
        values[:, 3] = 1/values[:, 3]

    output = {'PSAT': values[:,0]}
    cols = ['PRES', 'RS', 'BO', 'EG', 'UO', 'UG']
    for i, col in enumerate(cols):
        output[col] = values[:, i]
    return output


# TODO: functions to get intermediate values from Rs and Pres


def main():
    """Test"""
    path = 'tests/_no_sync/ex/dat/base_case_bo.dat'
    data = get_from_dat(path, verbose=True)
    for d in data:
        print(d)
        d.to_csv('test.csv', index=False)


if __name__ == "__main__":
    print(__doc__)
    main()
