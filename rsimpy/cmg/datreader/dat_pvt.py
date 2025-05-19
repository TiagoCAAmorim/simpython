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
from scipy.interpolate import RegularGridInterpolator

try:
    from rsimpy.cmg.datreader.dat_parser import DatParser
    from rsimpy.cmg.datreader import common
except ImportError:
    from dat_parser import DatParser
    import common


COLS = ['PRES', 'RS', 'BO', 'EG', 'UO', 'UG']
EPS = 1e-4


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
    if len(table) != 0:
        tables.append(
            _process_pvt_lines(table, len(tables), alpha / t_res, verbose=verbose)
        )

    if len(tables) == 0:
        if verbose:
            print('No PVT keywords found.')

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


def _process_pvt_lines(table, num_tables, z_transform, verbose=False):
    """Process PVT data from lines in dat file."""
    pvt = _process_pvt(table['PVT'], num_tables, z_transform, verbose)
    bot = _process_bot_vot(table['BOT'], pvt)
    vot = _process_bot_vot(table['VOT'], pvt)

    bot = _build_inv_bo_interpolation(bot, pvt)
    vot = _build_inv_bo_uo_interpolation(vot, bot, pvt)

    table = {
        'sat': pd.DataFrame(pvt),
        'usat_bo': bot,
        'usat_vo': vot,
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


def _build_inv_bo_interpolation(bot, pvt):
    """Build 1/Bo interpolation table."""
    rs_, p_norm, comp, interp_comp = _get_compressibility(bot)

    rs = np.concatenate([rs_, pvt['RS']])
    rs = np.unique(rs)
    rs = np.sort(rs)

    p_max = np.max(pvt['PRES']) + EPS
    bo_inv = []
    for rsi in rs:
        if rsi in bot:
            bo_inv.append(np.interp(p_norm, bot[rsi]['PRES_NORM'], 1/bot[rsi]['val']))
        else:
            if rsi < rs_[0]:
                comp_ = comp[0]
            elif rsi > rs_[-1]:
                comp_ = comp[-1]
            else:
                rs_vector = np.repeat([rsi], p_norm.shape[0])
                comp_ = interp_comp(np.stack([rs_vector, p_norm], axis=1))
            bo_sat = 1/np.interp(rsi, pvt['RS'], 1/pvt['BO'])
            bo = [bo_sat]
            psat = np.interp(rsi, pvt['RS'], pvt['PRES'])
            pres = psat + (p_max - psat) * p_norm
            for i in range(1, p_norm.shape[0]):
                bo.append(bo[i-1] + comp_[i-1] * (pres[i] - pres[i-1]) * bo[i-1])
            bo_inv.append(1/np.array(bo))

    bo_inv = np.array(bo_inv)

    return {
        'RS': rs,
        'PRES_NORM': p_norm,
        '1/BO': bo_inv,
    }


def _build_inv_bo_uo_interpolation(vot, inv_bo_interp, pvt):
    """Build 1/BoUo interpolation table."""
    rs_, p_norm, comp, interp_comp = _get_compressibility(vot)

    rs = np.concatenate([rs_, pvt['RS']])
    rs = np.unique(rs)
    rs = np.sort(rs)

    p_max = np.max(pvt['PRES']) + EPS
    uo_inv = []
    for rsi in rs:
        if rsi in vot:
            uo_inv.append(1/np.interp(p_norm, vot[rsi]['PRES_NORM'], vot[rsi]['val']))
        else:
            if rsi < rs_[0]:
                comp_ = comp[0]
            elif rsi > rs_[-1]:
                comp_ = comp[-1]
            else:
                rs_vector = np.repeat([rsi], p_norm.shape[0])
                comp_ = interp_comp(np.stack([rs_vector, p_norm], axis=1))
            bo_sat = 1/np.interp(rsi, pvt['RS'], 1/pvt['BO'])
            bouo_sat = 1/np.interp(rsi, pvt['RS'], 1/pvt['UO']/pvt['BO'])
            uo = [bouo_sat / bo_sat]
            psat = np.interp(rsi, pvt['RS'], pvt['PRES'])
            pres = psat + (p_max - psat) * p_norm
            for i in range(1, p_norm.shape[0]):
                uo.append(uo[i-1] + comp_[i-1] * (pres[i] - pres[i-1]) * uo[i-1])
            uo_inv.append(1/np.array(uo))


    interp_inv_bo = RegularGridInterpolator(
        (inv_bo_interp['RS'], inv_bo_interp['PRES_NORM']),
        inv_bo_interp['1/BO'],
        bounds_error=False,
        fill_value=None,
    )

    bovo_inv = []
    for rsi, uo_inv_ in zip(rs, uo_inv):
        rs_vector = np.repeat([rsi], p_norm.shape[0])
        bo_inv = interp_inv_bo(np.stack([rs_vector, p_norm], axis=1))
        bovo_inv.append(bo_inv * uo_inv_)
    bovo_inv = np.array(bovo_inv)

    return {
        'RS': rs,
        'PRES_NORM': p_norm,
        '1/BOUO': bovo_inv,
    }


def get_pvt_values(table, data, check_psat=True):
    """
    Get PVT values for a given RS and Pressure.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'usat_bo': Undersaturated table for BO (Pres > Psat).
        - 'usat_vo': Undersaturated  table for UO (Pres > Psat).
    data : np.array
        Array of (np_points, 2) with the first column being
        solution gas-oil ratio (Rs) and the second
        column being pressure.
    check_psat : bool
        If True, check if Psat is smaller or equal to the pressure.
        Default: True.
    """
    if len(table) != 3:
        raise ValueError(f"Expected 3 items in PVT table. Found {len(table)}.")

    for key in ['sat', 'usat_bo', 'usat_vo']:
        if key not in table:
            raise ValueError(f"Missing {key} in PVT table.")

    rs = data[:, 0]
    p = data[:, 1]
    sat = table['sat']
    psat = np.interp(rs, sat['RS'], sat['PRES'])
    _check_pvt_limits(rs, p, sat, psat, check_psat)

    eg = np.interp(p, sat['PRES'], sat['EG'])
    ug = eg/np.interp(p, sat['PRES'], 1/sat['UG']*sat['EG'])

    inv_bo = table['usat_bo']
    inv_bovo = table['usat_vo']

    interp_bo = RegularGridInterpolator(
        (inv_bo['RS'], inv_bo['PRES_NORM']),
        inv_bo['1/BO'],
        bounds_error=False,
        fill_value=None,
    )
    interp_bovo = RegularGridInterpolator(
        (inv_bovo['RS'], inv_bovo['PRES_NORM']),
        inv_bovo['1/BOUO'],
        bounds_error=False,
        fill_value=None,
    )

    p_norm = (p - psat) / (sat['PRES'].max() + EPS - psat)
    bo = 1/interp_bo(np.stack([rs, p_norm], axis=1))
    uo = 1/bo/interp_bovo(np.stack([rs, p_norm], axis=1))

    return {
        'RS': rs,
        'PRES': p,
        'PSAT': psat,
        'PNORM': p_norm,
        'BO': bo,
        'EG': eg,
        'BG': 1/eg,
        'UO': uo,
        'UG': ug,
    }


def _check_pvt_limits(rs, p, sat, psat, check_psat):
    if rs.min() < sat['RS'].min() or rs.max() > sat['RS'].max():
        range_rs = f"[{rs.min()}, {rs.max()}]"
        range_ = f"[{sat['RS'].min()}, {sat['RS'].max()}]"
        raise ValueError(f"RS values ({range_rs}) is out of range ({range_}).")

    if p.min() < sat['PRES'].min() or p.max() > sat['PRES'].max():
        range_p = f"[{p.min()}, {p.max()}]"
        range_ = f"[{sat['PRES'].min()}, {sat['PRES'].max()}]"
        raise ValueError(f"Pressure values ({range_p}) is out of range ({range_}).")

    if check_psat and np.any(p < psat):
        raise ValueError(f"{np.sum(p < psat)} pressure values less than associated Psat.")


if __name__ == "__main__":
    print(__doc__)
