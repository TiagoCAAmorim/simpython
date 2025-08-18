"""
Module to PVT tables from CMG dat files.

Keywords processed: PVT, BOT, VOT, DENSITY, GRAVITY GAS,
CPOR, PRPOR, DCPOR, REFPW, BWI, CW, VWI, CVW.


Functions
---------
get_from_dat(file_path, abs_path=None, encoding='utf-8', verbose=False)
    Get PVT tables from a CMG dat file.
get_from_dat_data(data, verbose=False)
    Get PVTtables from a CMG dat file processed data.

get_eg(table, p)
    Get gas expansion factor for a given pressure.
get_ug(table, p, eg=None)
    Get gas viscosity for a given pressure.
get_eg_inv(table, eg)
    Get pressure for a given gas expansion factor.
get_ug_inv(table, ug)
    Get pressure for a given gas viscosity.
get_rhog(table, p, eg=None)
    Get gas density for a given pressure.

get_psat(table, rs)
    Get saturation pressure for a given solubility ratio.
get_rs(table, psat)
    Get solubility ratio for a given saturation pressure.

get_bo_sat(table, psat)
    Get oil formation volume factor at saturation for a given saturation pressure.
get_bo_sat_inv(table, bo)
    Get saturation pressure for a given oil formation volume factor.
get_uo_sat(table, psat)
    Get oil viscosity at saturation for a given saturation pressure.
get_uo_sat_inv(table, uo)
    Get saturation pressure for a given oil viscosity.
get_bo(table, p, rs, psat=None)
    Get oil formation volume factor for a given pressure and solubility ratio.
get_bo_inv(table, bo, rs, psat=None)
    Get pressure for a given oil formation volume factor and solubility ratio.
get_uo(table, p, rs, psat=None, bo=None)
    Get oil viscosity for a given pressure and solubility ratio.
get_uo_inv(table, uo, rs, psat=None)
    Get pressure for a given oil viscosity and solubility ratio.
get_rhoo(table, p, rs, bo=None, psat=None)
    Get oil density for a given pressure and solubility ratio.

get_pvt_values(table, data, check_psat=True)
    Get PVT values for a given RS and Pressure.

get_por_mod(table, p)
    Get porosity modifier for a given pressure.
get_bw(table, p)
    Get water formation volume factor for a given pressure.
get_bw_inv(table, bw)
    Get pressure for a given water formation volume factor.
get_uw(table, p)
    Get water viscosity for a given pressure.
get_uw_inv(table, uw)
    Get pressure for a given water viscosity.
get_rhow(table, p, bw=None)
    Get water density for a given pressure.

find_equilibrium(pvt, vo_std, vg_std, vw_std, vpor_ref, max_iter=10, tol=1e-6)
    Find the equilibrium pressure using the secant method.
"""

import numpy as np
import pandas as pd
from scipy.stats import linregress

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
EPS = 1e-20


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
        - 'DENWAT': gas density.

        - 'CPOR': Pressure dependence of formation porosity
        - 'PRPOR': Reference pressure for rock compressibility
        - 'DCPOR': Pressure dependence of rock compressibility
            por(p) = por_input [ 1 + cpor (p - prpor) + dcpor (p - prpor)^2]

        - 'REFPW': Reference pressure for water compressibility
        - 'BWI': Water formation volume factor at reference pressure
        - 'CW': Water compressibility
            bw = bwi [ 1 - cw (p - prw) ]

        - 'VWI': Water viscosity at the reference pressure
        - 'CVW': Pressure dependence of water viscosity
            vw = vwi + cvw • (p - prw)
    """
    alpha, t_delta = _read_units(data)
    data = get_section(data, 'GRID')

    t_res = None
    tables = []
    defaults = {
        'PVT': -1,
        'BOT':[],
        'VOT': [],
        'DENOIL': -999.99,
        'DENGAS': -999.99,
        'DENWAT': 999.014,
        'CPOR': 0.0,
        'PRPOR': 1.0,
        'DCPOR': 0.0,
        'REFPW': 1.0,
        'BWI': 1.0,
        'CW': 0.0,
        'VWI': 0.5,
        'CVW': 0.0,
    }
    table = defaults.copy()
    for line in data:
        if line[0] == 'TRES':
            t_res = float(line[1]) + t_delta
        elif line[0] == 'PVT':
            if table['PVT'] > 0:
                tables.append(
                    _process_pvt_lines(table, len(tables), alpha / t_res, verbose=verbose)
                )
            table = defaults.copy()
            table['PVT'] = line
        elif line[0] == 'DENSITY':
            table[f'DEN{line[1][:3]}'] = float(line[2])
        elif line[0] == 'GRAVITY':
            if line[1] == 'GAS':
                table['DENGAS'] = float(line[2]) * 1.2222
            else:
                print(f"Unknown gravity option: {line[1]}. Expected 'GAS'.")
        elif line[0] in ['CPOR', 'PRPOR', 'DCPOR', 'REFPW', 'BWI', 'CW', 'VWI', 'CVW']:
            table[line[0]] = float(line[-1])
            if line[0] in ['CPOR', 'PRPOR', 'DCPOR']:
                defaults[line[0]] = float(line[-1])
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
    table_out = {
        'sat': pvt,
        'bot': _process_bot_vot(table['BOT'], pvt),
        'uot': _process_bot_vot(table['VOT'], pvt),
    }
    for k in ['DENOIL', 'DENGAS', 'DENWAT',
              'CPOR', 'PRPOR', 'DCPOR',
              'REFPW', 'BWI', 'CW', 'VWI', 'CVW']:
        table_out[k.lower()] = table.get(k, 0.0)
    return table_out


def _build_subsat_interp(pvt_table):
    """Build subsaturated Bo and Uo interpolators."""
    table = {
        'sat': pd.DataFrame(pvt_table['sat']),
        'bo': _build_interpolation(pvt_table['bot']),
        'uo': _build_interpolation(pvt_table['uot']),
    }
    for k in ['DENOIL', 'DENGAS', 'DENWAT',
              'CPOR', 'PRPOR', 'DCPOR',
              'REFPW', 'BWI', 'CW', 'VWI', 'CVW']:
        table[k.lower()] = pvt_table.get(k.lower(), 0.0)
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
        if len(table) % 2 == 0:
            values = np.array(table[2:], dtype=float).reshape(-1, 2)
        else:
            values = np.array(table[1:], dtype=float).reshape(-1, 2)
        if len(values) == 0:
            raise ValueError("No values found in keyword table.")

        psat_values = pvt['PRES']
        rs_values = pvt['RS']
        interpolated_rs = np.interp(values[0, 0], psat_values, rs_values)

        output[interpolated_rs] = {
            'PRES': values[:, 0],
            'val': values[:, 1],
            }

    return output


def _build_interpolation(tables):
    """
    Build interpolation table.

    It is assumed that, for a given Rs value, Bo and Uo (**y**) hold an approximate linear
    relationship between the subsaturated pressure (**delta_p** = p - p_sat) and the inverse
    *compressibility* of the quantity (1/y.dy/dp).
    A single slope is calculated for each undersat table (**alpha**).
    dy/dp is aproximated using finite forward differences.

    Another value, **beta**, is calculated for each pressure point in the
    undersat table:
    beta = [(y/y_sat)^alpha - 1] / (alpha * delta_p).
    The mean beta is used as another interpolation factor is due to the fact that it usually
    is approximately constant for a given p_sat.

    For any interpolation it is needed alpha = f(p_sat) and beta = f(p_sat).

    To obtain the resulting interpolation: y = y_sat * (alpha * beta * delta_p + 1)^{1/alpha}.

    This function returns a list of slopes (alphas) with saturation
    pressure, and a 2D interpolator of the constants (betas) as a
    function of saturation pressure and subsaturated pressure.
    """
    psat = []
    alphas = []
    betas = []
    for table in tables.values():
        psat.append(table['PRES'][0])
        p_subsat = table['PRES'][:-1] - table['PRES'][0]

        d_pres = table['PRES'][1:] - table['PRES'][:-1]
        d_val = table['val'][1:] - table['val'][:-1]
        comp = d_val/d_pres / table['val'][:-1]

        slope, _, _, _, _ = linregress(p_subsat, 1 / (comp+EPS))
        alphas.append(slope)
        alpha, _, _, _, _ = linregress(p_subsat, 1 / (comp+EPS))
        alphas.append(alpha)

        delta_p = table['PRES'][1:] - table['PRES'][0]
        relative_val = table['val'][1:]/table['val'][0]
        beta = (np.power(relative_val, alpha) - 1) / (alpha * delta_p)
        betas.append(beta.mean())

    alphas = np.array(alphas)
    betas = np.array(betas)
    psat = np.array(psat)

    return np.stack([psat, alphas, betas], axis=0)


# MARK: Get Por
def get_por_mod(table, p):
    """
    Get porosity modifier for a given pressure.

    This function uses the default porosity model:
        por(p) = por_input [ 1 + cpor (p - prpor) + dcpor (p - prpor)^2]

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'cpor': Pressure dependence of formation porosity
        - 'prpor': Reference pressure for rock compressibility
        - 'dcpor': Pressure dependence of rock compressibility
    p : np.array
        Pressure.

    Returns
    -------
    float
        Porosity modifier.
    """
    return 1 + table['cpor'] * (p - table['prpor']) + table['dcpor'] * (p - table['prpor'])**2


# MARK: Get Water
def get_bw(table, p):
    """
    Get water formation volume factor for a given pressure.

    This function uses the default bw model:
        bw = bwi [ 1 - cw (p - prw) ]

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'refpw': Reference pressure for water compressibility
        - 'bwi': Water formation volume factor at reference pressure
        - 'cw': Water compressibility
    p : np.array
        Pressure.

    Returns
    -------
    float
        Water formation volume factor.
    """
    return table['bwi'] * (1 - table['cw'] * (p - table['refpw']))


def get_bw_inv(table, bw):
    """
    Get pressure for a given water formation volume factor.

    This function uses the default bw model:
        bw = bwi [ 1 - cw (p - prw) ]

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'refpw': Reference pressure for water compressibility
        - 'bwi': Water formation volume factor at reference pressure
        - 'cw': Water compressibility
    bw : np.array
        Water formation volume factor.

    Returns
    -------
    float
        Pressure.
    """
    return (1 - bw / table['bwi']) / table['cw'] + table['refpw']


def get_uw(table, p):
    """
    Get water viscosity for a given pressure.

    This function uses the default uw model:
        vw = vwi + cvw • (p - prw)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'refpw': Reference pressure for water compressibility
        - 'vwi': Water viscosity at the reference pressure
        - 'cvw': Pressure dependence of water viscosity
    p : np.array
        Pressure.

    Returns
    -------
    float
        Water viscosity.
    """
    return table['vwi'] + table['cvw'] * (p - table['refpw'])


def get_uw_inv(table, uw):
    """
    Get pressure for a given water viscosity.

    This function uses the default uw model:
        vw = vwi + cvw • (p - prw)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'refpw': Reference pressure for water compressibility
        - 'vwi': Water viscosity at the reference pressure
        - 'cvw': Pressure dependence of water viscosity
    uw : np.array
        Water viscosity.

    Returns
    -------
    float
        Pressure.
    """
    return (uw - table['vwi']) / table['cvw'] + table['refpw']


def get_rhow(table, p, bw=None):
    """
    Get water density for a given pressure.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'refpw': Reference pressure for water compressibility
        - 'bwi': Water formation volume factor at reference pressure
        - 'cw': Water compressibility
    p : np.array
        Pressure.
    bw : np.array, optional
        Water formation volume factor. If not provided, it will be
        calculated from data.

    Returns
    -------
    float
        Water density.
    """
    if bw is None:
        bw = get_bw(table, p)
    return table['denwat'] / bw


# MARK: Get Gas
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
        - 'bo': Undersaturated Bo table (Pres > Psat).
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


def get_eg_inv(table, eg):
    """
    Get the pressure for a given gas expansion factor.

    This function linearly interpolates pressure with the
    inverse of gas formation volume factor: p = f(1/Bg) = f(Eg),
    except for the values below the lowest Eg value,
    where it is assumed a linear extrapolation of the inverse function:
    p = f(1/Eg)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    eg : np.array
        Gas expansion factor (Eg=1/Bg).

    Returns
    -------
    float
        Pressure.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return interp.alt_interp1d(
        x=sat['EG'],
        y=sat['PRES'],
        x_new=eg,
        x_inversion=sat['EG'].min(),
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
        - 'bo': Undersaturated Bo table (Pres > Psat).
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


def get_ug_inv(table, ug):
    """
    Get the pressure for a given gas viscosity.

    This function linearly interpolates pressure with the
    gas viscosity: p = f(Ug),
    except for the values below the lowest Ug value,
    where it is assumed a linear extrapolation of the inverse function:
    p = f(1/Ug)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    ug : np.array
        Gas viscosity.

    Returns
    -------
    float
        Pressure.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return interp.alt_interp1d(
        x=sat['UG'],
        y=sat['PRES'],
        x_new=ug,
        x_inversion=sat['UG'].min(),
        extrap=True,
        inverse_smaller=True,
        )

def get_rhog(table, p, eg=None):
    """
    Get gas density for a given pressure.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
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


# MARK: Get Psat
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
        - 'bo': Undersaturated Bo table (Pres > Psat).
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
        - 'bo': Undersaturated Bo table (Pres > Psat).
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


# MARK: Get Oil sat
def get_bo_sat(table, psat):
    """
    Oil formation volume factor for a given saturation pressure.

    Oil formation volume factor is linearly interpolated with saturation pressure:
    Bo = f(Psat),
    except for the values below the lowest saturation pressure
    where it is assumed a linear extrapolation of the inverse function:
    Bo = f(1/Psat)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    psat : np.array
        Saturation pressure.

    Returns
    -------
    float
        Oil formation volume factor at the saturation pressure.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return interp.alt_interp1d(
        x=sat['PRES'],
        y=sat['BO'],
        x_new=psat,
        x_inversion=sat['PRES'].min(),
        extrap=True,
        inverse_smaller=True,
        )


def get_bo_sat_inv(table, bo):
    """
    Saturation pressure for a given saturated oil formation volume factor.

    Saturation pressure is linearly interpolated with oil formation volume factor:
    Psat = f(Bo),
    except for the values below the lowest oil formation volume factor
    where it is assumed a linear extrapolation of the inverse function:
    Psat = f(1/Bo)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    bo : np.array
        Oil formation volume factor.

    Returns
    -------
    float
        Saturation pressure.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return interp.alt_interp1d(
        x=sat['BO'],
        y=sat['PRES'],
        x_new=bo,
        x_inversion=sat['BO'].min(),
        extrap=True,
        inverse_smaller=True,
        )


def get_uo_sat(table, psat):
    """
    Oil viscosity for a given saturation pressure.

    Oil viscosity is linearly interpolated with saturation pressure:
    Uo = f(Psat),
    except for the values above the highest saturation pressure
    where it is assumed a linear extrapolation of the inverse function:
    Uo = f(1/Psat)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    psat : np.array
        Saturation pressure.

    Returns
    -------
    float
        Oil viscosity at the saturation pressure.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return interp.alt_interp1d(
        x=sat['PRES'],
        y=sat['UO'],
        x_new=psat,
        x_inversion=sat['PRES'].max(),
        extrap=True,
        inverse_smaller=False,
        )


def get_uo_sat_inv(table, uo):
    """
    Saturation pressure for a given saturated oil viscosity.

    Saturation pressure is linearly interpolated with oil viscosity:
    Psat = f(Uo),
    except for the values below the lowest oil viscosity
    where it is assumed a linear extrapolation of the inverse function:
    Psat = f(1/Uo)

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    bo : np.array
        Oil formation volume factor.

    Returns
    -------
    float
        Saturation pressure.
    """
    if 'sat' not in table:
        raise ValueError("Missing saturated data in PVT table.")
    sat = table['sat']
    return interp.alt_interp1d(
        x=sat['UO'],
        y=sat['PRES'],
        x_new=uo,
        x_inversion=sat['UO'].max(),
        extrap=True,
        inverse_smaller=False,
        )


# MARK: Get Oil undersat
def _get_bo_uo(table, p, rs, col_name, psat=None):
    if psat is None:
        psat = get_psat(table, rs)

    if col_name.lower() == 'bo':
        vsat = get_bo_sat(table, psat)
    elif col_name.lower() == 'uo':
        vsat = get_uo_sat(table, psat)
    else:
        raise ValueError(f"Unknown column name: {col_name}. Expected 'bo' or 'uo'.")

    psat_table = table[col_name.lower()][0]
    alphas = table[col_name.lower()][1]
    betas = table[col_name.lower()][2]

    alpha = interp.interp_extrap(psat_table, alphas, psat, extrap=False)
    beta = interp.interp_extrap(psat_table, betas, psat, extrap=False)

    sub_sat = p - psat
    s = alpha * sub_sat * beta + 1
    s[s < EPS] =  - EPS / sub_sat[s < EPS] # avoid negative values inside the power
    return vsat * np.power(s, 1/alpha)


def _get_bo_uo_inv(table, val, rs, col_name, psat=None):
    if psat is None:
        psat = get_psat(table, rs)

    if col_name.lower() == 'bo':
        vsat = get_bo_sat(table, psat)
    elif col_name.lower() == 'uo':
        vsat = get_uo_sat(table, psat)
    else:
        raise ValueError(f"Unknown column name: {col_name}. Expected 'bo' or 'uo'.")

    psat_table = table[col_name.lower()][0]
    alphas = table[col_name.lower()][1]
    betas = table[col_name.lower()][2]

    alpha = interp.interp_extrap(psat_table, alphas, psat, extrap=False)
    beta = interp.interp_extrap(psat_table, betas, psat, extrap=False)

    s = (np.power(val / vsat, alpha) - 1) / (alpha * beta)
    return s + psat


def get_bo(table, p, rs, psat=None):
    """
    Get oil formation volume factor for a given pressure and solubility ratio.

    This function assumes that the oil formation volume factor (Bo) 'compressibility'
    varies linearly with the subsaturated pressure. The slope (alpha) and constant
    term (beta) are interpolated from the undersaturated Bo tables. No extrapolation
    is performed, using the values from the nearest saturated table.

    Bo values are then calculated as:
        Bo = Bo_sat * (alpha * (p - psat) / beta + 1)^(1/alpha)

    where:
        - Bo_sat is the oil formation volume factor at saturation pressure.
        - p is the pressure.
        - psat is the saturation pressure.
    This formula is the integral of the 'linear compressibility' model.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
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


def get_bo_inv(table, bo, rs, psat=None):
    """
    Get the pressure for a given oil formation volume factor and solubility ratio.

    This function assumes that the oil formation volume factor (Bo) 'compressibility'
    varies linearly with the subsaturated pressure. The slope (alpha) and constant
    term (beta) are interpolated from the undersaturated Bo tables. No extrapolation
    is performed, using the values from the nearest saturated table.

    Bo values are then calculated as:
        Bo = Bo_sat * (alpha * (p - psat) * beta + 1)^(1/alpha)
    To get pressure from Bo:
        p = ((Bo/Bo_sat)^alpha - 1) / (alpha * beta) - psat

    where:
        - Bo_sat is the oil formation volume factor at saturation pressure.
        - p is the pressure.
        - psat is the saturation pressure.
    This formula is the integral of the 'linear compressibility' model.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    bo : np.array
        Oil formation volume factor.
    rs : np.array
        Solubility ratio.
    psat : np.array, optional
        Saturation pressure. If not provided, it will be calculated
        from saturated data.

    Returns
    -------
    float
        Pressure.
    """
    return _get_bo_uo_inv(table, bo, rs, 'BO', psat)


def get_uo(table, p, rs, psat=None):
    """
    Get oil viscosity for a given pressure and solubility ratio.

    This function assumes that the oil viscosity (Uo) 'compressibility'
    varies linearly with the subsaturated pressure. The slope (alpha) and constant
    term (beta) are interpolated from the undersaturated Uo tables. No extrapolation
    is performed, using the values from the nearest saturated table.

    Uo values are then calculated as:
        Uo = Uo_sat * (alpha * (p - psat) * beta + 1)^(1/alpha)

    where:
        - Uo_sat is the oil viscosity at saturation pressure.
        - p is the pressure.
        - psat is the saturation pressure.
    This formula is the integral of the 'linear compressibility' model.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
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


def get_uo_inv(table, uo, rs, psat=None):
    """
    Get the pressure for a given oil viscosity and solubility ratio.

    This function assumes that the oil viscosity (Uo) 'compressibility'
    varies linearly with the subsaturated pressure. The slope (alpha) and constant
    term (beta) are interpolated from the undersaturated Uo tables. No extrapolation
    is performed, using the values from the nearest saturated table.

    Bo values are then calculated as:
        Uo = Uo_sat * (alpha * (p - psat) * beta + 1)^(1/alpha)
    To get pressure from Uo:
        p = ((Uo/Uo_sat)^alpha - 1) / (alpha * beta) - psat

    where:
        - Uo_sat is the oil viscosity at saturation pressure.
        - p is the pressure.
        - psat is the saturation pressure.
    This formula is the integral of the 'linear compressibility' model.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
        - 'uo': Undersaturated Uo table (Pres > Psat).
        - 'denoil': Oil density.
        - 'dengas': Gas density.
    uo : np.array
        Oil viscosity.
    rs : np.array
        Solubility ratio.
    psat : np.array, optional
        Saturation pressure. If not provided, it will be calculated
        from saturated data.

    Returns
    -------
    float
        Pressure.
    """
    return _get_bo_uo_inv(table, uo, rs, 'UO', psat)


def get_rhoo(table, p, rs, bo=None, psat=None):
    """
    Get oil density for a given pressure and solubility ratio.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
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


# MARK: Get all
def get_pvt_values(table, data, check_limits=False):
    """
    Get PVT values for a given RS and Pressure.

    Parameters
    ----------
    table : dict
        PVT table with the following keys:
        - 'sat': Saturated table (Pres = Psat).
        - 'bo': Undersaturated Bo table (Pres > Psat).
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


# MARK: Equilibrium
def _get_vol_error(pvt, vo_std, vg_std, vw_std, vpor_ref, p, rs=None, psat=None, is_sat=None):
    """Calculate the volume error for a given pressure."""
    if is_sat is None:
        rs = vg_std / (vo_std + EPS)
        psat = get_psat(pvt, rs=rs)
        is_sat = psat > p

    if (is_sat).any():
        rs[is_sat] = get_rs(pvt, psat=p[is_sat])
        psat[is_sat] = p[is_sat]

    vpor = vpor_ref * get_por_mod(pvt, p=p)
    vo = vo_std * get_bo(pvt, p=p, rs=rs, psat=psat)
    vg = (vg_std - rs * vo_std) / get_eg(pvt, p=p)
    vw = vw_std * get_bw(pvt, p=p)
    v_total = vo + vg + vw
    v_error = v_total - vpor
    return v_error


def find_equilibrium(pvt, vo_std, vg_std, vw_std, vpor_ref, max_iter=10, tol=1e-6):
    """
    Find the equilibrium pressure using the secant method.

    First it is tested the saturation pressure. With this information
    the algorithm can determine if the system is saturated or not.
    The secant method is used to find the equilibrium pressure.

    Arguments
    ---------
    pvt : dict
        PVT data.
    vo_std : np.ndarray
        Standard oil volume.
    vg_std : np.ndarray
        Standard gas volume.
    vw_std : np.ndarray
        Standard water volume.
    vpor_ref : np.ndarray
        Reference pore volume.
    max_iter : int
        Maximum number of iterations.
        Defaults to 10.
    tol : float
        Tolerance for equilibrium pressure convergence (p_i+1 - p_i).
        Defaults to 1e-6.

    Returns
    -------
    np.ndarray
        Equilibrium pressure.
    """
    vo_std = np.asarray(vo_std)
    vg_std = np.asarray(vg_std)
    vw_std = np.asarray(vw_std)
    vpor_ref = np.asarray(vpor_ref)

    # Check if equilibrium is saturated or undersaturated
    rs = vg_std / (vo_std + EPS)
    psat = get_psat(pvt, rs=rs)
    error_ = _get_vol_error(
        pvt, vo_std, vg_std, vw_std, vpor_ref,
        p=psat,
        rs=rs,
        psat=psat,
        is_sat=np.zeros_like(psat, dtype=bool)
    )

    p0 = psat.copy()
    filter_ = psat > pvt['sat']['PRES'].max()
    p0[filter_] = pvt['sat']['PRES'].max()

    e0 = error_.copy()
    e0[filter_] = _get_vol_error(
        pvt, vo_std[filter_], vg_std[filter_], vw_std[filter_], vpor_ref[filter_],
        p=p0[filter_]
    )

    is_sat = error_ < 0
    p1 = np.zeros_like(psat)
    if is_sat.any():
        p1[is_sat] = p0[is_sat] - (p0[is_sat] - pvt['sat']['PRES'].min()) / 2
    if (~is_sat).any():
        p1[~is_sat] = p0[~is_sat] + (pvt['sat']['PRES'].max() - p0[~is_sat]) / 2

    # Apply secant method
    for _ in range(max_iter):
        e1 = _get_vol_error(
            pvt, vo_std, vg_std, vw_std, vpor_ref,
            p=p1,
            rs=rs,
            psat=psat,
            is_sat=is_sat
        )

        denom = e1 - e0
        p_star = np.where(
            (np.abs(denom) < EPS) | (np.abs(p0 - p1) < tol),
            (p0 + p1) / 2,
            (p0 * e1 - p1 * e0) / np.where(np.abs(denom) < EPS, EPS, denom)
        )

        if (np.abs(p_star - p1) < tol).all():
            return p_star

        filter_ =  np.abs(e1) < np.abs(e0)
        p0[filter_] = p1[filter_]
        e0[filter_] = e1[filter_]
        p1 = p_star

    return p_star


if __name__ == "__main__":
    print(__doc__)
