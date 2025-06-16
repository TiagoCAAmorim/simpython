"""
Module to PVT tables from CMG dat files.

Keywords processed: PVT, BOT, VOT, DENSITY OIL, DENSITY GAS
and GRAVITY GAS.
Water density is not saved in PVT table.
It is assumed all undersaturated data is from the saturation
pressure to the max pressure in the satured table.

Functions
---------
get_from_dat(file_path, abs_path=None, encoding='utf-8', verbose=False):
    Get PVT tables from a CMG dat file.
get_from_dat_data(data, verbose=False):
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
    from rsimpy.cmg.datreader.dat_common import get_section
    from rsimpy.common import interp
except ImportError:
    # If running as a script, import from parent directory
    import sys
    from pathlib import Path
    print(Path(__file__).resolve().parent.parent.parent)
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from cmg.datreader.dat_common import get_section
    from cmg.datreader.dat_parser import DatParser
    from common import interp


COLS = ['PRES', 'RS', 'BO', 'EG', 'UO', 'UG']
INTERP_PTS = 1000

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
    data : output of DatParser.get()
        Processed data from a CMG dat file.
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
    tables = _read_data(data, verbose=verbose)
    if len(tables) == 0:
        if verbose:
            print('No PVT tables found.')
        return []
    return [_build_subsat_interp(table) for table in tables]


def _read_data(data, verbose=False):
    """
    Read PVT tables from a CMG dat file processed data.
    Data is read from the PVT, BOT and VOT keywords.

    Returns
    -------
    list of dicts
        List of dictionaries with the PVT tables.
        Each dictionary has the following keys:
        - 'PVT': PVT keyword data.
        - 'BOT': list of BOT keyword data.
        - 'VOT': list of VOT keyword data.
        - 'DENOIL': oil density.
        - 'DENGAS': gas density.
    """
    alpha, t_delta = _read_units(data)
    data = get_section(data, 'GRID')

    t_res = None
    tables = []
    table = {}
    for line in data:
        if line[0] == 'TRES':
            t_res = float(line[1]) + t_delta
        elif line[0] == 'PVT':
            if len(table) != 0:
                tables.append(
                    _process_pvt_lines(table, len(tables), alpha / t_res, verbose=verbose)
                )
            table = {'PVT': line, 'BOT':[], 'VOT': [], 'DENOIL': -999.99, 'DENGAS': -999.99}
        elif line[0] == 'DENSITY':
            table[f'DEN{line[1]}'] = float(line[2])
        elif line[0] == 'GRAVITY':
            if line[1] == 'GAS':
                table['DENGAS'] = float(line[2]) * 1.2222
            else:
                print(f"Unknown gravity option: {line[1]}. Expected 'GAS'.")
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
    data = get_section(data, 'TITLE1')

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
        'sat': pvt,
        'bot': bot,
        'uot': uot,
        'denoil': table['DENOIL'],
        'dengas': table['DENGAS'],
    }

    return table


def _build_subsat_interp(pvt_table):
    """Build subsaturated Bo and Uo interpolators."""
    rs_bo, bo = _build_interpolation(pvt_table['bot'], pvt_table['sat'], 'BO')
    rs_uo, uo = _build_interpolation(pvt_table['uot'], pvt_table['sat'], 'UO')

    table = {
        'sat': pd.DataFrame(pvt_table['sat']),
        'rs_bo': rs_bo,
        'bo': bo,
        'rs_uo': rs_uo,
        'uo': uo,
        'denoil': pvt_table['denoil'],
        'dengas': pvt_table['dengas'],
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
        p_max = np.max(pvt['PRES'])
        p_norm = (values[:, 0] - values[0, 0]) / (p_max - values[0, 0])

        output[interpolated_rs] = {
            'PRES': values[:, 0],
            'PRES_NORM': p_norm,
            'val': values[:, 1],
            }

    return output


def _get_compressibility(tables, p_norm):
    """Build compressibility table, and interpolator."""
    rs = np.sort(np.array(list(tables)))
    comp = []
    for rsi in rs:
        pres = tables[rsi]['PRES']
        val = tables[rsi]['val']

        pres_ = np.linspace(pres[0], pres[-1], num=INTERP_PTS)
        val_ = 1/np.interp(pres_, pres, 1/val)

        comp_ = (val_[1:] - val_[:-1]) / (pres_[1:] - pres_[:-1]) / val_[:-1]
        comp.append(np.concatenate([comp_, comp_[-1:]]))
    interp_comp = RegularGridInterpolator((rs, p_norm), np.array(comp))
    return rs, comp, interp_comp


def _build_interpolation(table, pvt, col_name):
    """Build interpolation table."""
    p_norm = np.linspace(0, 1, num=INTERP_PTS)
    rs_undersat, comp, interp_comp = _get_compressibility(table, p_norm)

    rs = np.concatenate([rs_undersat, pvt['RS']])
    rs = np.sort(np.unique(rs))

    p_max = np.max(pvt['PRES'])

    vals = []
    for rsi in rs:
        if rsi in table:
            vals.append(1/np.interp(p_norm, table[rsi]['PRES_NORM'], 1/table[rsi]['val']))
        else:
            if rsi < rs_undersat[0]:
                comp_ = comp[0]
            elif rsi > rs_undersat[-1]:
                comp_ = comp[-1]
            else:
                rs_vector = np.repeat([rsi], p_norm.shape[0])
                comp_ = interp_comp(np.stack([rs_vector, p_norm], axis=1))
            vals_ = [1/np.interp(rsi, pvt['RS'], 1/pvt[col_name])]
            psat = np.interp(rsi, pvt['RS'], pvt['PRES'])
            pres = psat + (p_max - psat) * p_norm
            for i in range(1, INTERP_PTS):
                vals_.append(vals_[i-1] * (1 + comp_[i-1] * (pres[i] - pres[i-1])))
            vals.append(vals_)

    return np.array(rs), np.array(vals)


# MARK: Get
def get_eg(table, p):
    """
    Get gas expansion factor for a given pressure.

    This function linearly interpolates the inverse of
    gas formation volume factor with pressure: 1/Bg = Eg = f(p),
    except for the values below the lowest pressure
    where it is assumed a linear extrapolation of the inverse function:
    Eg = f(1/p)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'rs_bo': Solubility ratio for undersaturated Bo table.
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'rs_uo': Solubility ratio for undersaturated Uo table.
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
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
    return interp.alt_interp1d(
        x=sat['PRES'],
        y=sat['EG'],
        x_new=p,
        x_inversion=sat['PRES'].min(),
        extrap=True,
        inverse_smaller=True,
        )


def get_ug(table, p):
    """
    Get gas viscosity for a given pressure.

    This function linearly interpolates gas viscosity
    with pressure: Ug = f(p),
    except for the values below the lowest pressure
    where it is assumed a linear extrapolation of the inverse function:
    Ug = f(1/p)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'rs_bo': Solubility ratio for undersaturated Bo table.
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'rs_uo': Solubility ratio for undersaturated Uo table.
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
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
    return interp.alt_interp1d(
        x=sat['PRES'],
        y=sat['UG'],
        x_new=p,
        x_inversion=sat['PRES'].min(),
        extrap=True,
        inverse_smaller=True,
        )


def get_psat(table, rs):
    """
    Get saturation pressure for a given solubility ratio.

    Saturation pressure is linearly interpolated with solubility ratio:
    Psat = f(Rs),
    except for the values below the lowest solubility ratio
    where it is assumed a linear extrapolation of the inverse function:
    Psat = f(1/Rs),

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'rs_bo': Solubility ratio for undersaturated Bo table.
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'rs_uo': Solubility ratio for undersaturated Uo table.
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
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
    return interp.alt_interp1d(
        x=sat['RS'],
        y=sat['PRES'],
        x_new=rs,
        x_inversion=sat['RS'].min(),
        extrap=True,
        inverse_smaller=True,
        )


def get_rs(table, psat):
    """
    Get solubility ratio for a given saturation pressure.

    Solubility ratio is linearly interpolated with saturation pressure:
    Rs = f(Psat),
    except for the values below the lowest saturation pressure
    where it is assumed a linear extrapolation of the inverse function:
    Rs = f(1/Psat)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'rs_bo': Solubility ratio for undersaturated Bo table.
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'rs_uo': Solubility ratio for undersaturated Uo table.
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    psat : np.array
        Saturation pressure.

    Returns
    -------
    float
        Saturation pressure.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return interp.alt_interp1d(
        x=sat['PRES'],
        y=sat['RS'],
        x_new=psat,
        x_inversion=sat['PRES'].min(),
        extrap=True,
        inverse_smaller=True,
        )


def _get_p_norm(p, psat, sat):
    """Get normalized undersat pressure."""
    p_max = sat['PRES'].max()
    p_norm = np.where((p_max - psat) <= 0, 0, (p - psat) / (p_max - psat))
    return p_norm


def _get_bo_uo(table, p, rs, col_name, psat=None):
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    if f'rs_{col_name.lower()}' not in table:
        raise ValueError(f"Missing undersaturated {col_name.title()} data in PVT table.")
    if col_name.lower() not in table:
        raise ValueError(f"Missing undersaturated {col_name.title()} data in PVT table.")

    rs_table = table[f'rs_{col_name.lower()}']
    vals = table[col_name.lower()]
    pres_norm = np.linspace(0, 1, num=vals.shape[1])

    interpolator = RegularGridInterpolator(
        (rs_table, pres_norm), vals,
        bounds_error=False,
        fill_value=None,
    )
    sat = table['sat']
    if psat is None:
        psat = get_psat(table, rs)
    p_norm = _get_p_norm(p, psat, sat)
    return interpolator(np.stack([rs, p_norm], axis=1))


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
        - 'rs_bo': Solubility ratio for undersaturated Bo table.
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'rs_uo': Solubility ratio for undersaturated Uo table.
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
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
    return _get_bo_uo(table, p, rs, 'BO', psat)


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
        - 'rs_bo': Solubility ratio for undersaturated Bo table.
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'rs_uo': Solubility ratio for undersaturated Uo table.
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
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
    return _get_bo_uo(table, p, rs, 'UO', psat)


def get_rhoo(table, p, rs, bo=None, psat=None):
    """
    Get oil density for a given pressure and solubility ratio.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'rs_bo': Solubility ratio for undersaturated Bo table.
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'rs_uo': Solubility ratio for undersaturated Uo table.
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    p : np.array
        Pressure.
    rs : np.array
        Solubility ratio.
    bo : np.array, optional
        Oil formation volume factor. If not provided, it will be
        calculated from undersaturated data.
    psat : np.array, optional
        Saturation pressure. If not provided, it will be calculated
        from saturated data.

    Returns
    -------
    float
        Oil density.
    """
    if bo is None:
        if psat is None:
            psat = get_psat(table, rs)
        bo = get_bo(table, p, rs, psat)
    return (rs * table['dengas'] + table['denoil']) / bo


def get_rhog(table, p, eg=None):
    """
    Get gas density for a given pressure.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'rs_bo': Solubility ratio for undersaturated Bo table.
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'rs_uo': Solubility ratio for undersaturated Uo table.
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    p : np.array
        Pressure.
    eg : np.array, optional
        Gas expansion factor. If not provided, it will be
        calculated from saturated data.

    Returns
    -------
    float
        Gas density.
    """
    if eg is None:
        eg = get_eg(table, p)
    return table['dengas'] * eg


def get_pvt_values(table, data, check_limits=False):
    """
    Get PVT values for a given RS and Pressure.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'rs_bo': Solubility ratio for undersaturated Bo table.
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'rs_uo': Solubility ratio for undersaturated Uo table.
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    data : np.array
        Array of (np_points, 2) with the first column being
        solution gas-oil ratio (Rs) and the second
        column being pressure.
    check_limits : bool
        If True, check if Rs and pressure values are within the
        table limits. Checks if the given pressure is greater than
        the saturation pressure for the given Rs.
        If False, if the given pressure is smaller than the saturation
        pressure, assumes the pressure is the saturation pressure.
        Default: False.

    Returns
    -------
    dict
        Dictionary with the following keys:
        - 'PSAT': Saturation pressure.
        - 'BO': Oil formation volume factor.
        - 'EG': Gas expansion factor.
        - 'BG': Gas formation volume factor (1/EG).
        - 'UO': Oil viscosity.
        - 'UG': Gas viscosity.
        - 'DENO': Oil density.
        - 'DENG': Gas density.
    """
    rs = data[:, 0]
    p = data[:, 1]

    psat = get_psat(table, rs)
    if check_limits:
        if np.any(p < psat):
            p = np.where(p < psat, psat, p)
        _check_pvt_limits(rs, p, table['sat'])

    eg = get_eg(table, p)
    ug = get_ug(table, p)
    bo = get_bo(table, p, rs, psat)
    uo = get_uo(table, p, rs, psat)
    rhoo = get_rhoo(table, p, rs, bo, psat)
    rhog = get_rhog(table, p)

    return {
        'RS': rs,
        'PRES': p,
        'PSAT': psat,
        'BO': bo,
        'EG': eg,
        'BG': 1/eg,
        'UO': uo,
        'UG': ug,
        'DENO': rhoo,
        'DENG': rhog,
    }


def _check_pvt_limits(rs, p, sat_table):
    if rs.min() < sat_table['RS'].min() or rs.max() > sat_table['RS'].max():
        range_rs = f"[{rs.min()}, {rs.max()}]"
        range_ = f"[{sat_table['RS'].min()}, {sat_table['RS'].max()}]"
        raise ValueError(f"RS values ({range_rs}) is out of range ({range_}).")

    if p.min() < sat_table['PRES'].min() or p.max() > sat_table['PRES'].max():
        range_p = f"[{p.min()}, {p.max()}]"
        range_ = f"[{sat_table['PRES'].min()}, {sat_table['PRES'].max()}]"
        raise ValueError(f"Pressure values ({range_p}) is out of range ({range_}).")


if __name__ == "__main__":
    print(__doc__)
