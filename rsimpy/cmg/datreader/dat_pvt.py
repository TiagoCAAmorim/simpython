"""
Module to PVT tables from CMG dat files.

Functions
---------
get_from_dat(file_path, abs_path=None, encoding='utf-8', verbose=False):
    Get PVT tables from a CMG dat file.
get_pvt_from_dat_data(data, verbose=False):
    Get PVTtables from a CMG dat file processed data.
get_eg(table, p):
    Get gas expansion factor for a given pressure.
get_ug(table, p, eg=None):
    Get gas viscosity for a given pressure.
get_psat(table, rs):
    Get saturation pressure for a given solubility ratio.
get_bo(table, p, rs, psat=None):
    Get oil formation volume factor for a given pressure and solubility ratio.
get_uo(table, p, rs, psat=None, bo=None):
    Get oil viscosity for a given pressure and solubility ratio.
get_pvt_values(table, data, check_psat=True)
    Get PVT values for a given RS and Pressure.
"""
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

try:
    from rsimpy.cmg.datreader.dat_parser import DatParser
    from rsimpy.cmg.datreader import common
except ImportError:
    from dat_parser import DatParser
    import common


COLS = ['PRES', 'RS', 'BO', 'EG', 'UO', 'UG']
EPS = 1e-4

# MARK: Read
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
        ignore=['ROCKFLUID','INITIAL','NUMERICAL','RUN','GRID_keys'],
        verbose=verbose,
        _debug=_debug)
    parser.process(file_path=file_path)

    return get_from_dat_data(parser.get(), verbose=verbose)


def get_from_dat_data(data, verbose=False):
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
    alpha, t_delta = _read_units(data)
    data = common.get_section(data, 'GRID')

    t_res = None
    tables = []
    table = {}
    for line in data:
        if line[0] == 'TRES':
            t_res = float(line[1]) + t_delta
        if line[0] == 'PVT':
            if len(table) != 0:
                tables.append(
                    _process_pvt_lines(table, len(tables), alpha / t_res, verbose=verbose)
                )
            table = {'PVT': line, 'BOT':[], 'VOT': []}
        elif line[0] == 'BOT':
            if len(table) == 0:
                raise ValueError("BOT keyword found before PVT keyword.")
            table['BOT'].append(line)
        elif line[0] == 'VOT':
            if len(table) == 0:
                raise ValueError("VOT keyword found before PVT keyword.")
            table['VOT'].append(line)
    if len(table) == 0:
        if verbose:
            print('No PVT keywords found.')
        return []
    tables.append(
        _process_pvt_lines(table, len(tables), alpha / t_res, verbose=verbose)
    )

    return tables


def _read_units(data):
    """Read units from the data and definte t_std/p_std."""
    data = common.get_section(data, 'TITLE1')

    t_delta = 273.15
    p_std = 101.325
    t_std = 15.56 + t_delta
    for line in data:
        if line[0] == 'INUNIT':
            if line[1] == 'SI':
                break
            if line[1] == 'MODSI':
                p_std = 1.03
            elif line[1] == 'FIELD':
                #include scf/bbl => m3/m3, IMEX manual: 0.17801529
                p_std = 14.7 * 0.1801175
                t_delta = 459.67
                t_std = 60 + t_delta
            else:
                raise ValueError(f"Unknown pressure unit: {line[1]}")
            break
    return t_std / p_std, t_delta


# MARK: Process
def _process_pvt_lines(table, num_tables, z_transform, verbose=False):
    """Process PVT data from lines in dat file."""
    pvt = _process_pvt(table['PVT'], num_tables, z_transform, verbose)
    bot = _process_bot_vot(table['BOT'], pvt)
    uot = _process_bot_vot(table['VOT'], pvt)

    table = {
        'sat': pd.DataFrame(pvt),
        'usat_bo': _build_bo_interpolation(bot, pvt),
        'usat_uo': _build_uo_interpolation(uot, pvt),
    }

    return table


def _process_pvt(table, num_tables, z_transform, verbose):
    """Process PVT keyword from lines in dat file."""
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

    if gas_col not in ['EG', 'BG', 'ZG']:
        msg = f"Invalid gas column: {gas_col}. Expected 'EG', 'BG' or 'ZG'."
        raise ValueError(msg)

    if verbose:
        print(f"Found Table: {gas_col} {table_number}")
    if table_number != num_tables+1:
        msg = f"Table number {table_number} does not match expected {num_tables+1}."
        raise ValueError(msg)

    values = np.array(table[i0+1:], dtype=float).reshape(-1, 6)
    if gas_col == 'BG':
        values[:, 3] = 1/values[:, 3]
    elif gas_col == 'ZG':
        values[:, 3] = values[:, 0] / values[:, 3] * z_transform

    output = {}
    for i, col in enumerate(COLS):
        output[col] = values[:, i]
    return output


def _process_bot_vot(tables, pvt):
    """Process BOT or VOT keywords from lines in a dat file."""
    output = {}
    for table in tables:
        values = np.array(table[1:], dtype=float).reshape(-1, 2)
        if len(values) == 0:
            raise ValueError("No values found in keyword table.")

        psat_values = pvt['PRES']
        rs_values = pvt['RS']
        interpolated_rs = np.interp(values[0, 0], psat_values, rs_values)
        p_max = np.max(pvt['PRES']) + EPS
        p_norm = (values[:, 0] - values[0, 0]) / (p_max - values[0, 0])

        output[interpolated_rs] = {
            'PRES': values[:, 0],
            'PRES_NORM': p_norm,
            'val': values[:, 1],
            }

    return output


def _get_compressibility(tables):
    """Build compressibility table, and interpolator."""
    p_norm = np.array([])
    for rs in tables:
        p_norm = np.append(p_norm, tables[rs]['PRES_NORM'])
    p_norm = np.unique(p_norm)
    p_norm = np.sort(p_norm)

    rs = np.array(list(tables))
    comp = []
    for rsi in rs:
        p_norm_ = tables[rsi]['PRES_NORM']
        pres_ = tables[rsi]['PRES']
        val_ = tables[rsi]['val']
        comp_ = (val_[1:] - val_[:-1]) / (pres_[1:] - pres_[:-1]) / val_[:-1]
        comp.append(np.interp(p_norm, p_norm_[:-1], comp_))
    comp = np.array(comp)
    interp_comp = RegularGridInterpolator((rs, p_norm), comp)
    return rs, p_norm, comp, interp_comp


def _build_bo_interpolation(bot, pvt):
    """Build Bo interpolation table."""
    rs_, p_norm, comp, interp_comp = _get_compressibility(bot)

    rs = np.concatenate([rs_, pvt['RS']])
    rs = np.unique(rs)
    rs = np.sort(rs)

    p_max = np.max(pvt['PRES']) + EPS
    bo = []
    for rsi in rs:
        if rsi in bot:
            bo.append(np.interp(p_norm, bot[rsi]['PRES_NORM'], bot[rsi]['val']))
        else:
            if rsi < rs_[0]:
                comp_ = comp[0]
            elif rsi > rs_[-1]:
                comp_ = comp[-1]
            else:
                rs_vector = np.repeat([rsi], p_norm.shape[0])
                comp_ = interp_comp(np.stack([rs_vector, p_norm], axis=1))
            bo_sat = np.interp(rsi, pvt['RS'], pvt['BO'])
            bo_ = [bo_sat]
            psat = np.interp(rsi, pvt['RS'], pvt['PRES'])
            pres = psat + (p_max - psat) * p_norm
            for i in range(1, p_norm.shape[0]):
                bo_.append(bo_[i-1] + comp_[i-1] * (pres[i] - pres[i-1]) * bo_[i-1])
            bo.append(bo_)

    return {
        'RS': rs,
        'PRES_NORM': p_norm,
        'BO': np.array(bo),
    }


def _build_uo_interpolation(uot, pvt):
    """Build Uo interpolation table."""
    rs_, p_norm, comp, interp_comp = _get_compressibility(uot)

    rs = np.concatenate([rs_, pvt['RS']])
    rs = np.unique(rs)
    rs = np.sort(rs)

    p_max = np.max(pvt['PRES']) + EPS
    uo = []
    for rsi in rs:
        if rsi in uot:
            uo.append(np.interp(p_norm, uot[rsi]['PRES_NORM'], uot[rsi]['val']))
        else:
            if rsi < rs_[0]:
                comp_ = comp[0]
            elif rsi > rs_[-1]:
                comp_ = comp[-1]
            else:
                rs_vector = np.repeat([rsi], p_norm.shape[0])
                comp_ = interp_comp(np.stack([rs_vector, p_norm], axis=1))
            uo_sat = np.interp(rsi, pvt['RS'], pvt['UO'])
            uo_ = [uo_sat]
            psat = np.interp(rsi, pvt['RS'], pvt['PRES'])
            pres = psat + (p_max - psat) * p_norm
            for i in range(1, p_norm.shape[0]):
                uo_.append(uo_[i-1] + comp_[i-1] * (pres[i] - pres[i-1]) * uo_[i-1])
            uo.append(uo_)

    return {
        'RS': rs,
        'PRES_NORM': p_norm,
        'UO': np.array(uo),
    }


# MARK: Get
def get_eg(table, p):
    """
    Get gas expansion factor for a given pressure.

    This function linearly interpolates the inverse of
    gas formation volume factor with pressure: 1/Bg = Eg = f(p)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'usat_bo': Undersaturated table for BO (Pres > Psat).
        - 'usat_uo': Undersaturated  table for UO (Pres > Psat).
    p : np.array
        Pressure.

    Returns
    -------
    float
        Gas expansion factor (Eg=1/Bg).
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return np.interp(p, sat['PRES'], sat['EG'])


def get_ug(table, p):
    """
    Get gas viscosity for a given pressure.

    This function linearly interpolates gas viscosity
    with pressure: Ug = f(p)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'usat_bo': Undersaturated table for BO (Pres > Psat).
        - 'usat_uo': Undersaturated  table for UO (Pres > Psat).
    p : np.array
        Pressure.

    Returns
    -------
    float
        Gas viscosity.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return np.interp(p, sat['PRES'], sat['UG'])


def get_psat(table, rs):
    """
    Get saturation pressure for a given solubility ratio.

    Saturation pressure is linearly interpolated with solubility ratio:
    Psat = f(rs)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'usat_bo': Undersaturated table for BO (Pres > Psat).
        - 'usat_uo': Undersaturated  table for UO (Pres > Psat).
    rs : np.array
        Solubility ratio.

    Returns
    -------
    float
        Saturation pressure.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return np.interp(rs, sat['RS'], sat['PRES'])


def get_bo(table, p, rs, psat=None):
    """
    Get oil formation volume factor for a given pressure and solubility ratio.

    This function linearly interpolates oil formation volume factor
    with solubility ration and normalized pressure above
    saturation pressure: 1/Bo = f(rs, (p-psat)/(pmax-psat))

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'usat_bo': Undersaturated table for BO (Pres > Psat).
        - 'usat_uo': Undersaturated  table for UO (Pres > Psat).
    p : np.array
        Pressure.
    rs : np.array
        Solubility ratio.
    psat : np.array, optional
        Saturation pressure. If not provided, it will be calculated
        from saturated data.

    Returns
    -------
    float
        Oil formation volume factor.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    if 'usat_bo' not in table:
        raise ValueError("Missing undersaturated Bo data in PVT table.")

    bo = table['usat_bo']

    interp_bo = RegularGridInterpolator(
        (bo['RS'], bo['PRES_NORM']),
        bo['BO'],
        bounds_error=False,
        fill_value=None,
    )
    sat = table['sat']
    if psat is None:
        psat = get_psat(table, rs)
    p_norm = (p - psat) / (sat['PRES'].max() + EPS - psat)
    return interp_bo(np.stack([rs, p_norm], axis=1))


def get_uo(table, p, rs, psat=None):
    """
    Get oil viscosity for a given pressure and solubility ratio.

    This function linearly interpolates oil viscosity with
    solubility ration and normalized pressure above
    saturation pressure: Uo = f(rs, (p-psat)/(pmax-psat))

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'usat_bo': Undersaturated table for BO (Pres > Psat).
        - 'usat_uo': Undersaturated  table for UO (Pres > Psat).
    p : np.array
        Pressure.
    rs : np.array
        Solubility ratio.
    psat : np.array, optional
        Saturation pressure. If not provided, it will be calculated
        from saturated data.

    Returns
    -------
    float
        Oil viscosity.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    if 'usat_uo' not in table:
        raise ValueError("Missing undersaturated Uo data in PVT table.")

    uo = table['usat_uo']
    interp_uo = RegularGridInterpolator(
        (uo['RS'], uo['PRES_NORM']),
        uo['UO'],
        bounds_error=False,
        fill_value=None,
    )

    sat = table['sat']
    if psat is None:
        psat = get_psat(table, rs)
    p_norm = (p - psat) / (sat['PRES'].max() + EPS - psat)
    return interp_uo(np.stack([rs, p_norm], axis=1))


def get_pvt_values(table, data, check_psat=True):
    """
    Get PVT values for a given RS and Pressure.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'usat_bo': Undersaturated table for BO (Pres > Psat).
        - 'usat_uo': Undersaturated  table for UO (Pres > Psat).
    data : np.array
        Array of (np_points, 2) with the first column being
        solution gas-oil ratio (Rs) and the second
        column being pressure.
    check_psat : bool
        If True, check if Psat is smaller or equal to the pressure.
        If False, will set pressure to Psat if it is smaller.
        Default: True.
    """
    if len(table) != 3:
        raise ValueError(f"Expected 3 items in PVT table. Found {len(table)}.")

    for key in ['sat', 'usat_bo', 'usat_uo']:
        if key not in table:
            raise ValueError(f"Missing {key} in PVT table.")

    rs = data[:, 0]
    p = data[:, 1]

    psat = get_psat(table, rs)
    p = _check_pvt_limits(rs, p, table['sat'], psat, check_psat)

    eg = get_eg(table, p)
    ug = get_ug(table, p)
    bo = get_bo(table, p, rs, psat)
    uo = get_uo(table, p, rs, psat)

    return {
        'PSAT': psat,
        'BO': bo,
        'EG': eg,
        'BG': 1/eg,
        'UO': uo,
        'UG': ug,
    }


def _check_pvt_limits(rs, p, sat_table, psat, check_psat):
    if rs.min() < sat_table['RS'].min() or rs.max() > sat_table['RS'].max():
        range_rs = f"[{rs.min()}, {rs.max()}]"
        range_ = f"[{sat_table['RS'].min()}, {sat_table['RS'].max()}]"
        raise ValueError(f"RS values ({range_rs}) is out of range ({range_}).")

    if p.min() < sat_table['PRES'].min() or p.max() > sat_table['PRES'].max():
        range_p = f"[{p.min()}, {p.max()}]"
        range_ = f"[{sat_table['PRES'].min()}, {sat_table['PRES'].max()}]"
        raise ValueError(f"Pressure values ({range_p}) is out of range ({range_}).")

    if check_psat and np.any(p < psat):
        raise ValueError(f"{np.sum(p < psat)} pressure values less than associated Psat.")
    return np.where(p < psat, psat, p)


if __name__ == "__main__":
    print(__doc__)
