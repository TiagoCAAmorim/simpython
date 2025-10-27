# sr3reader/data.py
"""
krel.py

This module provides functionality for extracting relative permeability tables.

Classes:
--------
DataHandler
    A class to handle relative permeability extraction.

Usage Example:
--------------
krel_handler = KrelHandler()
krel_table1 = krel_handler.get(1)
"""

import numpy as np
import xarray as xr

# from rsimpy.cmg.sr3reader.data import SimData
from rsimpy.cmg.sr3reader.sim_data import SimData

class KrelHandler:
    """
    A class to handle relative permeability extraction.

    Parameters
    ----------
    sr3_reader: sr3reader.Sr3Reader
        SR3 reader object.

    Methods
    -------
    get(table_number):
        Returns relative permeability data.
    """

    def __init__(self, sr3_reader, auto_read=False):
        self._file = sr3_reader
        self._krel_tables = None
        if auto_read:
            self.read()


    def read(self):
        """Reads relative permeability tables from the file."""
        self._krel_tables = []
        go_tables = []
        wo_tables = []
        ts = self._file.get_table("Tables")
        for t in list(ts.keys()):
            tables = self._file.get_table(f"Tables/{t}")
            for table in tables:
                if str(table).upper().startswith("GO-PERM-TABLE"):
                    go_tables.append(self._process_table(f"Tables/{t}/{table}"))
                elif str(table).upper().startswith("WO-PERM-TABLE"):
                    wo_tables.append(self._process_table(f"Tables/{t}/{table}"))
        if len(go_tables) != len(wo_tables):
            raise ValueError("Mismatch in number of GO and WO tables.")
        if len(go_tables) == 0:
            raise ValueError("No GO or WO tables found.")
        for go, wo in zip(go_tables, wo_tables):
            processed_tables = self._process_tables(go, wo)
            self._krel_tables.append(SimData(processed_tables))


    def _process_table(self, table):
        """Processes a table and returns its data."""
        data = self._file.get_table(table)

        xr_dataset = xr.Dataset()
        xr_dataset.attrs["saturation"] = data.dtype.names[0].replace('TAB-','').lower()

        for i, c in enumerate(data.dtype.names):
            c_ = c.replace('TAB-','').lower()
            data_ = np.array([data[t][i] for t in range(data.shape[0])])
            data_array = xr.DataArray(
                data_,
                dims=[c_])
            xr_dataset[c_] = data_array

        return xr_dataset


    def _process_tables(self, go_table, wo_table):
        """Processes GO and WO tables and returns their data."""
        if wo_table.attrs["saturation"] == 'sw':
            wo_table['so'] = 1 - wo_table['sw']
        else:
            wo_table['sw'] = 1 - wo_table['so']
        wo_table['sg'] = 0*wo_table['so']
        swcon = wo_table['sw'].min()

        if go_table.attrs["saturation"] == 'sg':
            go_table['sl'] = 1 - go_table['sg']
            go_table['so'] = 1 - go_table['sg'] - swcon
        else:
            go_table['sg'] = 1 - go_table['sl']
            go_table['so'] = go_table['sl'] - swcon
        go_table['sw'] = 1 - go_table['sg'] - go_table['so']
        sgcon = go_table['sg'].min()

        end_points = {
            'swcon': swcon,
            'sgcon': sgcon,
            'swcrit':   wo_table['sw'].values[wo_table['krw'].values==0].max(),
            'sgcrit':   go_table['sg'].values[go_table['krg'].values==0].max(),
            'sorw':     wo_table['so'].values[wo_table['krow'].values==0].max(),
            'sorg':     go_table['so'].values[go_table['krog'].values==0].max(),
            'sg_quad':  go_table['sg'].values[go_table['krg'].values>0].min(),
            'sog_quad': go_table['sg'].values[go_table['krog'].values>0].min(),
            'krw_max':  wo_table['krw'].max(),
            'krg_max':  go_table['krg'].max(),
            'kro_max':  wo_table['krow'].max(),
            'krw_sorw': wo_table['krw'].values[wo_table['krow'].values==0].min(),
            'krg_sorg': go_table['krg'].values[go_table['krog'].values==0].min(),
        }

        if end_points['kro_max'] != go_table['krog'].max():
            raise ValueError("Mismatch in KRO max values.")

        xr_dataset = xr.Dataset()
        xr_dataset.attrs["element_type"] = "krel"
        for k,v in end_points.items():
            xr_dataset.attrs[k] = float(v)

        def _new_data_array(table, s_name, col_name):
            data_array = xr.DataArray(
                table[col_name].values,
                coords={s_name: table[s_name].values},
                dims=[s_name])
            return data_array

        elements_ = ['krg', 'krog', 'pcg', 'pcgd', 'pcgi']
        for c in elements_:
            if c in go_table:
                xr_dataset[c] = _new_data_array(go_table, 'sl', c)

        elements_ = ['krw', 'krow', 'pcw', 'pcwd', 'pcwi']
        for c in elements_:
            if c in wo_table:
                xr_dataset[c] = _new_data_array(wo_table, 'sw', c)

        return xr_dataset


    def get_krw(self, table_number, sw, table=None, kr_string='krw'):
        """Returns krw for given sw from specified table.

        Parameters
        ----------
        table_number: int
            Associated table number.
        sw: float or np.ndarray
            Water saturation.
        table: xr.Dataset, optional
            Pre-fetched table data.
        kr_string: str, optional
            Specifies which krw curve to use. Defaults to 'krw'.

        Raises
        ------
        ValueError
            If table_number is invalid.
        """
        if table is None:
            table = self.get(table_number)
        krw = np.interp(sw,
                        table['sw'].values,
                        table[kr_string].values)
        return krw


    def get_krg(self, table_number, sg, table=None, kr_string='krg', use_quadratic_correction=True):
        """Returns krg for given sg from specified table.

        Parameters
        ----------
        table_number: int
            Associated table number.
        sg: float or np.ndarray
            Gas saturation.
        table: xr.Dataset, optional
            Pre-fetched table data.
        kr_string: str, optional
            Specifies which krg curve to use. Defaults to 'krg'.
        use_quadratic_correction: bool, optional
            Whether to apply quadratic correction for sg below sg_quad.
            Defaults to True.

        Raises
        ------
        ValueError
            If table_number is invalid.
        """
        if table is None:
            table = self.get(table_number)
        if use_quadratic_correction:
            qg_quad = (sg - table.attrs['sgcrit'])**2 / \
                (table.attrs['sg_quad'] - table.attrs['sgcrit']) + \
                table.attrs['sgcrit']
            sg = np.where(sg > table.attrs['sg_quad'], sg, qg_quad)

        if (table['sl'].values[-1] - table['sl'].values[0]) > 0:
            krg = np.interp(1-sg,
                            table['sl'].values,
                            table[kr_string].values)
        else:
            krg = np.interp(sg,
                            1-table['sl'].values,
                            table[kr_string].values)
        return krg


    def get_kro(self, table_number, sw, sg):
        """Returns kro for given sw and sg from specified table.

        Stone II model is assumed.

        Parameters
        ----------
        table_number: int
            Associated table number.
        sw: float or np.ndarray
            Water saturation.
        sg: float or np.ndarray
            Gas saturation.

        Raises
        ------
        ValueError
            If table_number is invalid.
        """
        table = self.get(table_number)

        krw = self.get_krw(table_number, sw, table=table)
        krow = self.get_krw(table_number, sw, table=table, kr_string='krow')
        krg = self.get_krg(table_number, sg, table=table)
        krog = self.get_krg(table_number, sg, table=table, kr_string='krog', use_quadratic_correction=False)

        kro_cw = table.attrs['kro_max']
        kro = kro_cw * ( (krow/kro_cw + krw) * (krog/kro_cw + krg) - krw - krg )

        return kro.clip(min=0.0)


    def get(self,table_number):
        """Returns relative permeability data.

        Parameters
        ----------
        table_number: int
            Associated table number.

        Raises
        ------
        ValueError
            If table_number is invalid.
        """
        if self._krel_tables is None:
            self.read()
        if table_number < 1 or table_number > len(self._krel_tables):
            msg = f"Invalid table number: {table_number}."
            msg += f" Available tables: {len(self._krel_tables)}."
            raise ValueError(msg)
        return self._krel_tables[table_number - 1]


    def get_number_of_tables(self):
        """Returns the number of relative permeability tables."""
        if self._krel_tables is None:
            self.read()
        return len(self._krel_tables)


    def __len__(self):
        return self.get_number_of_tables()


# MARK: Save Data

    def to_csv(self,
               filename,
               table_number):
        """Saves data to a CSV file.

        Parameters
        ----------
        filename : str
            Filename to save the data.
            If None, the data is not saved.
        table_number : int
            Associated table number.
        """
        if self._krel_tables is None:
            self.read()
        if table_number < 1 or table_number > len(self._krel_tables):
            msg = f"Invalid table number: {table_number}."
            msg += f" Available tables: {len(self._krel_tables)}."
            raise ValueError(msg)
        self._krel_tables[table_number - 1].to_csv(filename)
