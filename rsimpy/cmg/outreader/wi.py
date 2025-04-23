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
from functools import cmp_to_key
import itertools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import utils # pylint: disable=import-error


COLS = {
    'IMEX':{
        'well_number': (3,6, int),
        'well_name': (7,22, str),
        'layer': (61,65, int),
        'cell': (66,80,str),
        'wi': (82,93,float),
        'oil_pi': (94,103, float),
        'wat_pi': (104,113, float),
        'gas_pi': (114,123, float),
        'sol_pi': (124,133, float),
        'pol_pi': (134,143, float),
        'swt_pi': (144,153, float),
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

# MARK: DatDates
class OutWI:

    """
    OutWI: Class with code to read well index data in a .out CMG simulation file.

    Attributes
    ----------
    encoding : str
        File encoding. Default: 'utf-8'.
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
    get_wells()
        Return dict of wells and associated dates.
    get_well_dates(self, well_name):
        Return list of dates associated to the well.
    get_table():
        Return WI data as a pandas.DataFrame.
    plot_well(well_name):
        Return matplotlib plot with well WI.
    """


    def __init__(self, encoding='utf-8', verbose=False):
        self._encoding = encoding
        self._verbose = verbose

        self._file_path = None
        self._data = {}


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
            for ki,vi in v.items():
                if ki not in wells:
                    wells[ki] = {'number':[], 'layers':[], 'regulated':[], 'entries':0}
                wells[ki]['number'].append(str(vi['number']))
                wells[ki]['layers'].append(str(vi['layers']))
                reg = 'Regulated' if vi['regulated'] else 'Un-Regulated'
                wells[ki]['regulated'].append(reg)
                wells[ki]['entries'] += 1

        if len(wells) == 0:
            return msg + 'No well data.'
        msg += f'{len(wells)} well(s):\n'
        for k,v in wells.items():
            numbers = '/'.join(set(v['number']))
            layers = '/'.join(set(v['layers']))
            regulated = '/'.join(set(v['regulated']))
            msg += f'  {k} (#{numbers}): {layers} layers, {regulated}, {v["entries"]} entrie(s)\n'
        return msg[:-1]


    # MARK: Getters
    def get(self):
        """Return dict with all data read."""
        return self._data


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
                for k,v in well_data.items():
                    if k == 'wi':
                        continue
                    row_well[k] = v
                for connection in well_data['wi']:
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
            msg = f'File not found: {file_path}.'
            raise ValueError(msg)

        self._file_path = file_path

        try:
            file_type = utils.get_file_type(file_path, encoding=self._encoding)
            self._get_data(file_type)
            if prune:
                self._prune_data()
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
        try:
            self.process(file_path=file_path, prune=prune)
            return self.get()
        except: # pylint: disable=bare-except
            print('Could not retrieve data.')
            return None


    # MARK: Prune
    def _prune_data(self):
        """Delete data if equal to previous time-step."""

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
                _ = data.pop(k)
        self._data = data


    @staticmethod
    def _equal(data1, data2):
        for k in ['number', 'layers']:
            if data1[k] != data2[k]:
                return False
            for wi1, wi2 in zip(data1['wi'], data2['wi']):
                for w in wi1:
                    if wi1[w] != wi2[w]:
                        return False
        return True


    # MARK: read data
    @staticmethod
    def _get_time(line):
        pattern = r'TIME:\s+(\d+\.?\d*)\s+days\s+DATE:\s+(\d{4}):(\d{2}):(\d{2})'
        match = re.search(pattern, line)
        if match:
            days = float(match[1])
            date = '/'.join(match.groups()[1:][::-1])
            return {'date':date, 'days':days}
        return None


    @staticmethod
    def _get_well(line):
        pattern = r'Well Number =\s+(.*)\s+Well Name =\s+(.*)\s+'
        pattern += r' Number of Active Layers =\s+(.*)\s+\((.*)Regulated\)'
        match = re.search(pattern, line)
        if match:
            well_n = int(match[1])
            well_name = match[2]
            layers = int(match[3])
            regulated = match[4] == ''

            return {
                'well number': well_n,
                'well name': well_name,
                'layers': layers,
                'regulated': regulated}
        return None


    @staticmethod
    def _get_wi_data(line, file_type):
        try:
            out = {k: t(line[i1:i2]) for k,(i1,i2,t) in COLS[file_type].items()}
            for k,v in out.items():
                if isinstance(v, str):
                    out[k] = v.strip()
            return out
        except ValueError:
            pass
        return None

    @staticmethod
    def _process_cell(wi, prev_cell):
        if 'cell' not in wi:
            return
        cell_str = wi['cell']
        match = re.match(r'(\d+),(\d+),(\d+)(?:\s*(\w+))?', cell_str)

        if match:
            ii = int(match.group(1))
            jj = int(match.group(2))
            kk = int(match.group(3))

            medium = match.group(4) if match.group(4) else 'X'
            if medium[0] == 'M':
                medium = 'MT'
            elif medium[0] == 'F':
                medium = 'FR'
        else:
            msg = f"Cell string is not in the expected format: {cell_str}."
            raise ValueError(msg)

        if medium == 'X':
            same = (prev_cell['i'] == ii) and (prev_cell['j'] == jj)
            same = same and (prev_cell['k'] == kk) and (prev_cell['m'] == 'MT')
            if same:
                medium = 'FR'
            else:
                medium = 'MT'

        wi['cell i'] = ii
        wi['cell j'] = jj
        wi['cell k'] = kk
        wi['cell medium'] = medium

        _ = wi.pop('cell')


    @staticmethod
    def _process_line(line_number, line, data, current, file_type):
        log = ''

        time = OutWI._get_time(line)
        if time is not None:
            current = {
                'date': time['date'],
                'days': time['days'],
                'well': None
            }
            time_key = (current['date'], current['days'])
            data[time_key] = {}

            log = f'  Current date: {time["date"]} ({time["days"]} days)'
            return data, current, log

        well = OutWI._get_well(line)
        if well is not None:
            if current['date'] is None:
                msg = f'Found new well ({well["well name"]}) in line {line_number}, '
                msg += 'but date is not set. Check data.'
                raise ValueError(msg)
            current['well'] = well

            well_key = current['well']['well name']
            time_key = (current['date'], current['days'])
            data[time_key][well_key] = {
                'number': current['well']['well number'],
                'layers': current['well']['layers'],
                'regulated': current['well']['regulated'],
                'wi': []
            }

            log = f'    New well: {well["well name"]} (line {line_number})'
            return data, current, log

        wi = OutWI._get_wi_data(line, file_type)
        if wi is not None:
            if current['date'] is None:
                msg = f'Found well index data in line {line_number}, '
                msg += 'but date is not set. Check data.'
                raise ValueError(msg)
            if current['well'] is None:
                msg = f'Found well index data in line {line_number} ({current["days"]} days), '
                msg += 'but well is not set. Check data.'
                raise ValueError(msg)

            time_key = (current['date'], current['days'])
            well_key = current['well']['well name']

            if len(data[time_key][well_key]['wi']) >= data[time_key][well_key]['layers']:
                msg = f'Found well index data for {well_key} '
                msg += f'in line {line_number} at time {time_key} ({current["days"]} days), '
                msg += f'but only {current["well"]["layers"]} data lines were expected. '
                msg += 'Check data.'
                raise ValueError(msg)

            prev_cell = {'i':0, 'j':0, 'k':0, 'm':''}
            if len(data[time_key][well_key]['wi']) > 0:
                prev_cell['i'] = data[time_key][well_key]['wi'][-1]['cell i']
                prev_cell['j'] = data[time_key][well_key]['wi'][-1]['cell j']
                prev_cell['k'] = data[time_key][well_key]['wi'][-1]['cell k']
                prev_cell['m'] = data[time_key][well_key]['wi'][-1]['cell medium']
            OutWI._process_cell(wi, prev_cell)
            data[time_key][well_key]['wi'].append(wi)

        return data, current, ''


    def _get_data(self, file_type):
        data = {}
        with open(self._file_path, 'r', encoding=self._encoding, errors='ignore') as file:
            start = False
            for n, line in enumerate(file):
                try:
                    if 'W E L L  I N D E X  R E P O R T' in line:
                        start = True
                        current = {'date': None, 'days': None, 'well': None}
                        self._log(f'New WI Report (line {n+1})')
                    elif start:
                        if line.strip() == '1':
                            start = False
                            self._log(f'End of WI Report (line {n+1})')
                        else:
                            data, current, msg = OutWI._process_line(n+1, line, data, current, file_type)
                            if msg != '':
                                self._log(msg)
                except Exception as e: #pylint: disable=broad-exception-caught
                    print(f"Error in line {n + 1}: {e}")

        self._data = data


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
            for d in self._data[date_key][well_name]['wi']:
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

def test(file_path):
    """Tests"""
    out_wi = OutWI(verbose=False, encoding='utf-8')
    out_wi.process(file_path, prune=True)

    print('Data found:')
    print(out_wi)

    print(out_wi.get_table())
    print(out_wi.get())



    # print('Plotting...')
    # vertical_lines=[50, 5000]
    # wells = out_wi.get_wells()
    # for well_name in wells:
    #     out_wi.plot_well(
    #         well_name,
    #         vertical_lines=vertical_lines,
    #         file_name= f'./plots/{well_name}.png'
    #     )

if __name__ == "__main__":
    # _error_msg()
    test('tests/out/test_gem_small.out')
    # test('tests/out/test_imex_small.out')
