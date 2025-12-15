# sr3reader/wells.py
"""
wells.py

This module provides functionality for handling wells.

Classes:
--------
WellHandler
    A class to handle wells.

Usage Example:
--------------
well_handler = WellHandler(sr3_file, dates_handler)
ni, nj, nk = grid_handler.get_size("nijk")
"""

import numpy as np

class WellHandler:
    """
    A class to handle wells.

    Parameters
    ----------
    sr3_reader: sr3reader.Sr3Reader
        SR3 reader object.

    Methods
    -------
    get(property_name, days):
        Returns well property for the given days.
    get_names():
        Returns list of well names.
    get_type(well_names):
        Returns list of well types.
    get_children(well_names):
        Returns lists of well-reservoir connection names.
    get_cells(well_names):
        Returns lists of well-reservoir connection cells.
    get_groups(well_names):
        Returns list of associated well groups.
    """

    def __init__(self, sr3_reader):
        self._sr3 = sr3_reader

    def get_well_names(self):
        """Returns list of well names."""
        return self._sr3.elements.get('well')

    def _filter_layer_data(self, well_names, property_name):
        if well_names is None:
            well_names = self._sr3.elements.get('well')
        conn_data = self._sr3.elements.get_layer_data(property_name)
        conn_names = np.array(list(conn_data.keys()))
        names = np.char.partition(conn_names, '{')[:, 0]
        values = np.array(list(conn_data.values()))
        out = {}
        for well in well_names:
            out[well] = values[names == well].tolist()
        return out

    def get_children(self, well_names=None):
        """
        Returns dict of well-reservoir connection names.

        Parameters
        ----------
        well_names : list of str
            List of well names to get connections for.
            If None, gets connections for all wells.
            Default is None.
        """
        self._sr3.elements._get_layer_data() # pylint: disable=protected-access
        layer_data = self._sr3.elements._layer_data # pylint: disable=protected-access
        if well_names is None:
            well_names = self._sr3.elements.get('well')
        conn_names = np.array(list(layer_data.keys()))
        names = np.char.partition(conn_names, '{')[:, 0]
        out = {}
        for well in well_names:
            out[well] = conn_names[names == well].tolist()
        return out

    def get_cells(self, well_names=None, as_active=True):
        """
        Returns dict of well-reservoir connection names.

        Parameters
        ----------
        well_names : list of str
            List of well names to get connections for.
            If None, gets connections for all wells.
            Default is None.
        as_active : bool
            If True, returns cell indices as active cell indices.
            If False, returns cell indices as global cell indices.
            Default is True.
        """
        self._sr3.elements._get_layer_data() # pylint: disable=protected-access
        layer_data = self._sr3.elements._layer_data # pylint: disable=protected-access
        if well_names is None:
            well_names = self._sr3.elements.get('well')
        conn_names = np.array(list(layer_data.keys()))
        names = np.char.partition(conn_names, '{')[:, 0]
        cell_str = "cell_act" if as_active else "cell"
        cells = np.array([v[cell_str] for v in layer_data.values()])
        out = {}
        for well in well_names:
            out[well] = cells[names == well]
        return out

    def get_duplicates(self, coverage=0.95, flatten_k=True):
        """
        Returns dict of duplicate wells.

        Two wells are considered duplicates if they share at least
        `coverage` fraction of their connections.

        Parameters
        ----------
        coverage : float
            Fraction of shared connections to consider two wells as duplicates.
            Default is 0.95.
        flatten_k : bool
            If True, flattens the k index when comparing connections.
            Default is True.
        """
        names = self._sr3.elements.get('well')
        duplicates = {}

    def get_well_types(self, well_names=None, check_duplicates=False):
        """
        Returns list of well types.

        Well types are defined by the WELLOPMO property:
            * -2: Producer
            * 1: Water Injector
            * 3: Gas Injector

        Additional well types:
            * 4: WAG Injector (Water and Gas Injector)
            * 10: Convertible (Producer + Water and/or Gas Injector)

        Parameters
        ----------
        well_names : list of str
            List of well names to get types for. If None, gets types for all wells.
            Default is None.
        check_duplicates : bool
            Use well connections to check for duplicate wells. Returns the same type
            to all corresponding duplicates. Default is False.
        """
