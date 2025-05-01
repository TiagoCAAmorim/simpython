"""
Module to extract well index information in out file.

Well index is written after keyword 'WELPRN WI' in GEM
or 'WPRN WELL LAYER' in IMEX.

Example:

    from out_wi import OutWI

    out_wi = OutWI(verbose=False, encoding='utf-8')
    out_wi.process('./simulation.out', prune=True)

    print('Data found:')
    print(out_wi)

    print('Plotting...')
    vertical_lines=[50, 5000]
    wells = out_wi.get_wells()
    for well_name in wells:
        out_wi.plot_well(
            well_name,
            vertical_lines=vertical_lines,
            file_name= f'./plots/{well_name}.png'
        )
"""

import re
from pathlib import Path
import math
from functools import cmp_to_key
import itertools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from . import utils # pylint: disable=import-error
except ImportError:
    import utils


START = {
    'IMEX': 'Units for Well Index',
    'GEM': 'W E L L  I N D E X  R E P O R T'
}

IMEX_WELL = {
    'number': (2,6, int),
    'name': (6,22, str),
    'type': (27,38, str),
    'constraint': (39,42, str),
    'constr_val': (42,52, float),
    'constr_unit': (52,58, str),
}

KEEP_COLS = [
    'number', 'name', 'wi', 'cell', 'cell i', 'cell j', 'cell k', 'cell medium',
]

COLS = {
    'IMEX':{
        'layer': (60,64, int),
        'cell': (64,80,str),
        'wi': (81,93,float),
        'oil_pi': ( 93,103, float),
        'wat_pi': (103,113, float),
        'gas_pi': (113,123, float),
        'sol_pi': (123,133, float),
        'pol_pi': (133,143, float),
        'swt_pi': (143,153, float),
    },
    'GEM':{
        'layer': (0,9, int),
        'cell': (10,22, str),
        'rtype': (23,28, int),
        'FF': (29,38, float),
        'kh': (39,52, float),
        're': (53,67, float),
        'skin': (68,78, float),
        'rw': (79,92, float),
        'Di': (93,106, float),
        'wi': (107,119, float),
        'element': (120,128, int),
    },
}

# MARK: OutWI
class OutWI:

    """
    OutWI: Class with code to read well index data in a .out CMG simulation file.

    Attributes
    ----------
    encoding : str
        File encoding. Default: 'utf-8'.
    wi_only : bool
        If True, only well index data is read. Default: False.
    verbose : bool
        Print messages. Default: False.

    Methods
    -------
    process():
        Process out file.
    get():
        Return dict with well index data.
    process_and_get():
        Process file and return well index data.
    prune(self):
        Delete data if equal to previous time-step.
    get_wells()
        Return dict of wells and associated dates.
    get_well_dates(self, well_name):
        Return list of dates associated to the well.
    get_table():
        Return WI data as a pandas.DataFrame.
    plot_well(well_name):
        Return matplotlib plot with well WI.
    """


    def __init__(self, encoding='utf-8', wi_only=False ,verbose=False):
        self._encoding = encoding
        self._verbose = verbose
        self._wi_only = wi_only

        self._file_path = None
        self._file_type = None
        self._data = {}

        self._current_time = (None,100000)
        self._current_well = None
        self._current_line = None


    def _log(self, msg):
        if self._verbose:
            print(msg)


    # MARK: Print
    def __str__(self):
        msg = ''

        dates = list(self._data.keys())
        if len(dates) == 0:
            return 'No data'
        if len(dates) == 1:
            msg = f'1 date: {dates[0][0]} ({dates[0][1]} days)\n'
        else:
            msg = f'{len(dates)} dates: {dates[0][0]} ({dates[0][1]} days)'
            msg += f' to {dates[-1][0]} ({dates[-1][1]} days)\n'

        wells = {}
        for v in self._data.values():
            for wi,vi in v.items():
                if wi not in wells:
                    wells[wi] = {'number':[], 'layers':[], 'entries':0}
                wells[wi]['number'].append(str(vi['well_data']['number']))
                wells[wi]['layers'].append(str(len(vi['con_data'])))
                wells[wi]['entries'] += 1

        if len(wells) == 0:
            return msg + 'No well data.'
        msg += f'{len(wells)} well{"s" if len(wells) > 1 else ""}:\n'
        for k,v in wells.items():
            numbers = '/'.join(set(v['number']))
            layers = '/'.join(set(v['layers']))
            msg += f'  {k} (#{numbers}): {layers} layers, '
            msg += f'{v["entries"]} entr{"ies" if v["entries"] > 1 else "y"}\n'
        return msg[:-1]


    # MARK: Setters
    def set_encoding(self, encoding):
        """
        Set encoding.

        Arguments:
        -----------
        - encoding: str. File encoding.
        """
        self._encoding = encoding


    def set_wi_only(self, wi_only):
        """
        Set wi_only.

        Arguments:
        -----------
        - wi_only: bool. If True, only well index data is read.
        """
        self._wi_only = wi_only


    # MARK: Getters
    def get(self):
        """Return dict with all data read."""
        return self._data


    def get_encoding(self):
        """Return file encoding."""
        return self._encoding


    def get_wi_only(self):
        """Return wi_only."""
        return self._wi_only


    def get_file_path(self):
        """Return file path."""
        return self._file_path


    def get_file_type(self):
        """Return file type."""
        return self._file_type


    def get_wells(self):
        """Return dict of wells and associated dates."""
        wells = {}
        for (date,time), wells_data in self._data.items():
            for well in wells_data:
                if well not in wells:
                    wells[well] = []
                wells[well].append((date,time))
        return wells


    def get_well_dates(self, well_name):
        """
        Return list of dates associated to the well.

        Arguments:
        -----------
        - well: str. Well name.
        """
        wells = self.get_wells()
        if well_name not in wells:
            return None
        return wells[well_name]


    def get_table(self):
        """Return WI data as a pandas.DataFrame."""
        data = self.get()
        table = []
        for date_key, date_dict in data.items():
            row_date = {
                'date': date_key[0],
                'days': date_key[1],
                }
            for well_name, well_data in date_dict.items():
                row_well = {'well': well_name}
                for k,v in well_data['well_data'].items():
                    row_well[k] = v
                for connection in well_data['con_data']:
                    row = {}
                    for k,v in row_date.items():
                        row[k] = v
                    for k,v in row_well.items():
                        row[k] = v
                    for k,v in connection.items():
                        row[k] = v
                    table.append(row)

        return pd.DataFrame(table)


    # MARK: Process
    def process(self, file_path, prune=True):
        """
        Search for well index data.

        Arguments:
        -----------
        - file_path: str. Path to .out file.
        - prune: bool. If False, keeps all tables read.
            If True, keeps only the tables that are
            different from the table read before.
            Default: True.
        """
        self._file_path = None
        self._data = {}

        if self._verbose:
            print(f'Processing {file_path}.')

        file_path = Path(file_path)
        if not file_path.is_file():
            msg = f'File not found: {file_path.resolve().absolute()}.'
            raise ValueError(msg)
        self._file_path = file_path

        try:
            self._file_type = utils.get_file_type(file_path, encoding=self._encoding)
            self._log(f'File type: {self._file_type}')
            self._get_data()
            if prune:
                self.prune()

        except UnicodeDecodeError as e:
            msg = f'Error reading: {self._file_path.name} with {self._encoding}. '
            msg += 'Try different encoding:'
            print(msg, e)
            raise


    def process_and_get(self, file_path, prune=True):
        """
        Process file and return well index data.

        Arguments:
        -----------
        - file_path: str. Path to .out file.
        - prune: bool. If False, keeps all tables read.
            If True, keeps only the tables that are
            different from the table read before.
            Default: True.
        """
        self.process(file_path=file_path, prune=prune)
        return self.get()


    # MARK: Prune
    def prune(self):
        """Delete data if equal to previous time-step."""

        self._log('Pruning data.')
        prev_data = {}
        data = {}
        for k,v in self._data.items():
            if k not in data:
                data[k] = {}
            for ki,vi in v.items():
                if ki in prev_data:
                    if not OutWI._equal(prev_data[ki], vi):
                        data[k][ki] = vi
                        prev_data[ki] = vi
                else:
                    data[k][ki] = vi
                    prev_data[ki] = vi
            if len(data[k]) == 0:
                self._log(f'Repeated data for {k[0]} ({k[1]} days).')
                _ = data.pop(k)
        self._data = data


    @staticmethod
    def _equal(data1, data2): # pylint: disable=too-many-return-statements
        """Check if all items in two data sets are equal."""
        if isinstance(data1, dict) and isinstance(data2, dict):
            if len(data1) != len(data2):
                return False
            for k,d1 in data1.items():
                if k not in data2:
                    return False
                last_check = OutWI._equal(d1, data2[k])
                if not last_check:
                    return False
        elif isinstance(data1, list) and isinstance(data2, list):
            if len(data1) != len(data2):
                return False
            for d1,d2 in zip(data1,data2):
                last_check = OutWI._equal(d1, d2)
                if not last_check:
                    return False
        else:
            if data1 != data2:
                return False
        return True


    # MARK: Read time
    def _update_time(self):
        pattern = r'^\s*TIME:\s+(\d+\.?\d*)\s+days\s+.+\s+DATE:\s+(\d{4}):(\d{1,2}):(\d{1,2})\s*$'
        match = re.search(pattern, self._current_line)
        if match:
            days_ = float(match[1])
            date_ = '/'.join(match.groups()[1:][::-1])
            self._adjust_last_table((date_, days_))
            self._current_time = (date_, days_)

    def _print_time(self):
        return f'{self._current_time[0]} ({self._current_time[1]} days)'


    def _adjust_last_table(self, new_time):
        if self._current_time in self._data:
            if new_time[1] < self._current_time[1]:
                if new_time not in self._data:
                    msg = f'Adjusting last table: {self._print_time()} '
                    msg += f'to {new_time[0]} ({new_time[1]} days)'
                    self._log(msg)
                    data_ = self._data.pop(self._current_time)
                    self._data = {
                        **self._data,
                        new_time:data_,
                    }
                else:
                    msg = f'Last time read, {self._print_time()} '
                    msg += f'is before the current ({new_time[0]} - {new_time[1]} days), '
                    msg += 'but the current time is already in the data.'
                    raise ValueError(msg)


    # MARK: Read well data
    def _update_well(self):
        """update current well."""
        if self._file_type == 'IMEX':
            well_name, data = self._read_well_imex()
        elif self._file_type == 'GEM':
            well_name, data = self._read_well_gem()
        else:
            msg = f'File type not supported: {self._file_type}.'
            raise ValueError(msg)

        if data is None:
            return
        if well_name is None:
            msg = 'Found well index data, but well name is not set.'
            raise ValueError(msg)

        if self._current_time not in self._data:
            self._data[self._current_time] = {}
        else:
            self._check_well_layers()

        self._current_well = well_name
        if self._wi_only:
            data = {k:v for k,v in data.items() if k in KEEP_COLS}
        self._data[self._current_time][self._current_well] = {
                'well_data': {**data},
                'con_data': [],
            }


    def _check_well_layers(self):
        if self._current_well in self._data[self._current_time]:
            n_con = len(self._data[self._current_time][self._current_well]['con_data'])
            if 'layers' in self._data[self._current_time][self._current_well]['well_data']:
                expected = self._data[self._current_time][self._current_well]['well_data']['layers']
                if n_con != expected:
                    msg = f'Expected {expected} layers for well {self._current_well} '
                    msg += f'at {self._print_time()}, '
                    msg += f'but only {n_con} data lines were read. Check data.'
                    raise ValueError(msg)
            else:
                self._data[self._current_time][self._current_well]['well_data']['layers'] = n_con


    def _read_well_gem(self):
        pattern = r'Well Number =\s+(.*)\s+Well Name =\s+(.*)\s+'
        pattern += r' Number of Active Layers =\s+(.*)\s+\((.*)Regulated\)'
        match = re.search(pattern, self._current_line)
        if match:
            well_n = int(match[1])
            well_name = match[2]
            layers = int(match[3])
            regulated = match[4] == ''

            return well_name, {
                    'number': well_n,
                    'layers': layers,
                    'regulated': regulated
                }
        return None, None


    def _read_well_imex(self):
        i1,i2,_ = IMEX_WELL['constr_val']
        const_value = self._current_line[i1:i2].strip()
        if const_value == '':
            return None, None
        try:
            const_value = float(const_value)
            data = {}
            well_name = None
            for k, (i1,i2,t) in IMEX_WELL.items():
                d = t(self._current_line[i1:i2].strip())
                if k == 'name':
                    well_name = d
                else:
                    data[k] = d

            return well_name, data

        except ValueError:
            return None, None


    # MARK: Read Con data
    def _get_con_data(self):
        """Extract well connection data from current line."""
        try:
            out = {k: self._current_line[i1:i2].strip()
                   for k,(i1,i2,_) in COLS[self._file_type].items()}
            for k,v in out.items():
                t = COLS[self._file_type][k][2]
                if v == '' and t != str:
                    out[k] = t(0)
                else:
                    try:
                        out[k] = t(v)
                    except ValueError:
                        return None
            if out['cell'] == '':
                return None
            return out
        except ValueError:
            pass
        return None


    @staticmethod
    def _process_cell(con_data, prev_cell):
        """Tranform cell string to i, j, k and medium."""
        if 'cell' not in con_data:
            return
        cell_str = con_data['cell']
        match = re.match(r'(\d+),(\d+),(\d+)(?:\s*(\w+))?', cell_str)

        read = {'cell i':0, 'cell j':0, 'cell k':0}
        if match:
            for i,k in enumerate(read.keys()):
                read[k] = int(match.group(i+1))

            medium = match.group(4) if match.group(4) else 'X'
            if medium[0] == 'M':
                medium = 'MT'
            elif medium[0] == 'F':
                medium = 'FR'
            read['cell medium'] = medium
        else:
            msg = f"Cell string is not in the expected format: {cell_str}."
            raise ValueError(msg)

        if read['cell medium'] == 'X':
            same = prev_cell['cell medium'] == 'MT'
            for d1,d2 in zip(read.values(), prev_cell.values()):
                same = same and (d1 == d2)

            if same:
                read['cell medium'] = 'FR'
            else:
                read['cell medium'] = 'MT'

        for k,v in read.items():
            con_data[k] = v


    def _process_line(self):
        """Extract well data from line."""

        con_data = self._get_con_data()
        if con_data is None:
            return
        if con_data['wi'] == 0:
            return

        if self._current_well is None:
            msg = f'Found well index data at {self._print_time()}, '
            msg += 'but well is not set. Check data.'
            raise ValueError(msg)

        data_ = self._data[self._current_time][self._current_well]

        prev_cell = {'cell i':0, 'cell j':0, 'cell k':0, 'cell medium':''}
        if len(data_['con_data']) > 0:
            for p in prev_cell:
                prev_cell[p] = data_['con_data'][-1][p]
        OutWI._process_cell(con_data, prev_cell)

        if self._wi_only:
            con_data = {k:v for k,v in con_data.items() if k in KEEP_COLS}
        data_['con_data'].append(con_data)

    # MARK: Read file
    def _get_data(self):
        """Read data from file line by line."""
        self._data = {}
        self._current_well = None
        self._current_time = (None, 1E5)

        with open(self._file_path, 'r', encoding=self._encoding, errors='ignore') as file:
            start = False
            for n, line in enumerate(file):
                try:
                    self._current_line = line
                    if line.strip() != '':
                        self._update_time()

                    if START[self._file_type] in line:
                        msg = f'New WI Report (line {n+1:,}): {self._print_time()}'
                        self._log(msg)
                        if start:
                            msg = 'Attention: Previous WI report was not closed.'
                            raise ValueError(msg)
                        start = True
                        if self._current_time in self._data:
                            if len(self._data[self._current_time]) > 0:
                                msg = f'Current date was already read: {self._print_time()}. '
                                msg += 'Adding small number to the days.'
                                while self._current_time in self._data:
                                    small = math.ulp(self._current_time[1])
                                    new_days =  self._current_time[1] + small
                                    self._current_time = (self._current_time[0], new_days)
                                raise ValueError(msg)
                    elif start:
                        if line.strip() in ['','1']:
                            if self._current_time in self._data:
                                self._check_well_layers()
                                self._current_well = None
                                start = False
                                msg = f'End of WI Report (line {n+1:,}): {self._print_time()}'
                                self._log(msg)
                        else:
                            self._update_well()
                            self._process_line()
                except Exception as e: #pylint: disable=broad-exception-caught
                    print(f"Error in line {n + 1:,}: {e}")


    # MARK: Plot
    @staticmethod
    def _order_cells(cells):
        """
        Atempts to generate a single order cell list.

        The algorithm tries to order the cells based on the order they
        appear in the provided lists. If two cells are only found in
        different lists, it tries to infer the main direction of the
        series of cells.

        Arguments:
        - cells: dict. Dictionary of lists of strings. The strings
            must be in the following format:
            '<i index>,<j index>,<k index>'.
            It is assumed that each list is ordered.
        """

        def _get_best_dimens_order(cells):
            """Checks the best way to describe the main direction of the cells."""
            dimens_order = ['i','j','k']
            best_order = dimens_order
            best_count = 0

            permutations = list(itertools.permutations(dimens_order))
            for perm in permutations:
                count = 0
                for cells_ in cells.values():

                    def _cell_index(cell_str, order=perm):
                        match = re.match(r'(\d+),(\d+),(\d+)', cell_str)
                        total = 0
                        dimens = ['i','j','k']
                        alpha = [1, 1000, 1000000]
                        for i in range(3):
                            alpha_i = alpha[order.index(dimens[i])]
                            total += int(match.group(i+1)) * alpha_i
                        return total

                    cells_sorted = sorted(cells_, key=_cell_index)
                    count += sum(1 for a, b in zip(cells_sorted, cells_) if a == b)

                if count == sum(len(v) for v in cells.values()):
                    return perm

                if count > best_count:
                    best_order = perm
                    best_count = count

            return best_order

        best_order = _get_best_dimens_order(cells)

        def cell_order_index(cell_str):
            """Return an index associated to a cell."""
            match = re.match(r'(\d+),(\d+),(\d+)', cell_str)
            total = 0
            dimens = ['i','j','k']
            alpha = [1, 1000, 1000000]
            for i in range(3):
                alpha_i = alpha[best_order.index(dimens[i])]
                total += int(match.group(i+1)) * alpha_i
            return total

        def cell_order(cell_1, cell_2):
            """Gets cells relative position."""
            if cell_1 == cell_2:
                return 0
            i1 = -1
            for cells_ in cells.values():
                if (cell_1 in cells_) and (cell_2 in cells_):
                    i1 = cells_.index(cell_1)
                    i2 = cells_.index(cell_2)
                    break
            if i1 == -1:
                i1 = cell_order_index(cell_1)
                i2 = cell_order_index(cell_2)
            if i1 < i2:
                return -1
            if i1 > i2:
                return 1
            return 0

        all_cells = []
        for v in cells.values():
            all_cells.extend(v)
        all_cells = list(set(all_cells))

        if len(all_cells) == sum(len(v) for v in cells.values()):
            return sorted(all_cells, key=cell_order_index)
        return sorted(all_cells, key=cmp_to_key(cell_order))


    @staticmethod
    def _rebuild_series(xs, ys, default_y=None, order_function=None):
        """
        Rebuild series so that they share the same x values.

        Any non-existing values will be added to the series
        with the default value.

        Arguments:
        - xs: dict. Dictionnary with the x values of each series.
        - ys: dict. Dictionnary with the y values of each series.
        - default_y: any. Value to be included in the series when
            the corresponding x value is not present.
        - order_function: function. Function that defines the x
            values order given xs. If None, uses sorted on the
            set that holds all unique x values.
        """

        if order_function is None:
            all_xs = []
            for v in xs.values():
                all_xs.extend(v)
            all_xs = list(set(all_xs))
            all_xs = sorted(all_xs)
        else:
            all_xs = order_function(xs)

        new_ys = {}
        for k,y in ys.items():
            new_ys[k] = []
            for x in all_xs:
                if x in xs[k]:
                    i_x = xs[k].index(x)
                    new_ys[k].append(y[i_x])
                else:
                    new_ys[k].append(default_y)

        return all_xs, new_ys


    def plot_well(self, well_name, date_key=None, vertical_lines=None, file_name=None, show=False):
        """
        Return matplotlib plot with well WI.

        Arguments:
        -----------
        - well_name: str. Name of the well.
        - date_key: set. Date key to be plotter. If None, uses the
            first date the well was found. Default is None.
        - vertical_lines: list of float. WI values of the vertical lines
            to be included in the plot. If None, no lines are added.
            Default is None.
        - file_name: str. Path to image file to be created. If None,
            no file is created. Default is None.
        - show: bool. Indicates if plt.show() is to be executed.
            Default is False.
        """

        if well_name not in self.get_wells():
            msg = f'{well_name} not found.'
            raise ValueError(msg)

        if date_key is None:
            date_key = self.get_wells()[well_name][0]

        if date_key not in self._data:
            msg = f'{date_key} not found in data.'
            raise ValueError(msg)

        if well_name not in self._data[date_key]:
            msg = f'{well_name} not found in {date_key}.'
            raise ValueError(msg)

        def _get_values():
            cells = {'MT':[], 'FR':[]}
            wis = {'MT':[], 'FR':[]}
            for d in self._data[date_key][well_name]['con_data']:
                ii = d['cell i']
                jj = d['cell j']
                kk = d['cell k']
                m = d['cell medium']
                wi = d['wi']
                cell_str = f'{ii},{jj},{kk}'
                cells[m].append(cell_str)
                wis[m].append(wi)
            return cells, wis

        cells, wis = _get_values()
        new_cells, new_wis = OutWI._rebuild_series(
            cells, wis, order_function=OutWI._order_cells)
        new_cells.append('')
        for k,v in new_wis.items():
            new_wis[k].append(v[-1])

        fig, axes = plt.subplots(1, 2, figsize=(8,8))
        y_values = np.arange(0, len(new_cells), 1)
        for ax in axes:
            for key, values in new_wis.items():
                if len(values) > 0:
                    ax.step(values, y_values-0.5,
                            where='pre',
                            label=key, linewidth=2,
                            alpha=0.8)
                    ax.set_yticks(y_values, new_cells)

            if vertical_lines is not None:
                for v in vertical_lines:
                    ax.axvline(x=v, color='r', linestyle='-', linewidth=0.5)
                    ax.text(v, len(new_cells)-1.5, str(v),
                            color='red', fontsize=8, rotation=90, va='center', ha='right')

            ax.invert_yaxis()
            ax.legend(loc='upper left')
            ax.grid(which='both', linestyle='-', linewidth=0.25)
            ax.set_xlabel('WI')
            ax.set_ylabel('Cell')
        axes[1].set_xscale('log')

        fig.suptitle(f'{well_name}@{date_key}', fontsize=16)
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        if file_name is not None:
            plt.savefig(file_name)
        if show:
            plt.show()

        return axes


def _error_msg():
    print(__doc__)
    print(OutWI.__doc__)


if __name__ == "__main__":
    _error_msg()
