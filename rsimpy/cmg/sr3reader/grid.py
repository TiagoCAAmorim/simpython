# sr3reader/grid.py
"""
grid.py

This module provides functionality for handling grids.

Classes:
--------
GridHandler
    A class to handle grids.

Usage Example:
--------------
grid_handler = GridHandler(sr3_file, dates_handler)
ni, nj, nk = grid_handler.get_size("nijk")
"""

import numpy as np
from rsimpy.common.utils import _n2ijk, _ijk2n, _is_neighbor

from .coordinates import GridCoordHandler

class GridHandler:
    """
    A class to handle grids.

    Parameters
    ----------
    sr3_file : sr3reader.Sr3Handler
        SR3 file object.
    dates : sr3reader.DateHandler
        Date handler object.
    auto_read : bool, optional
        If True, reads date information from the SR3 file.
        (default: True)

    Methods
    -------
    read()
        Reads grid information.
    has_fracture()
        Checks if the grid has fractures.
    get_size(key=None)
        Gets grid sizes.
    get_property(name=None)
        Gets dict with property atributes by name.
    is_complete(name):
        Check if property is complete.
    is_internal(name):
        Check if property is internal.
    """

    def __init__(self, sr3_file, dates, auto_read=True):
        self._sizes = ()
        self._properties = []
        self._active_index = []
        self._complete_index = []
        self._file = sr3_file
        self._dates = dates

        if auto_read:
            self.read()

        self.coordinates = GridCoordHandler(
            sr3_file=self._file,
            sr3_grid=self,
            auto_read=auto_read)

# MARK: Read Data

    def read(self):
        """Reads grid information."""
        self._active_index = self._file.get_table("SpatialProperties/000000/GRID/IPSTCS")[:]
        self._complete_index = self._file.get_table("SpatialProperties/000000/GRID/ICSTPS")[:]
        self._sizes = self._extract_grid_sizes()
        self._properties = self._extract_properties()


    def _extract_grid_sizes(self):
        dataset = self._file.get_table("SpatialProperties/000000/GRID")
        ni = int(dataset["IGNTID"][0])
        nj = int(dataset["IGNTJD"][0])
        nk = int(dataset["IGNTKD"][0])
        n_cells = ni*nj*nk
        n_active = int(self._active_index.size)
        n_active_matrix = n_active
        n_fracture = 0
        n_active_fracture = 0

        if self._active_index[-1] > n_cells:
            n_active_matrix = int(np.where(self._active_index > n_cells)[0][0])
            n_active_fracture = n_active - n_active_matrix
            n_fracture = n_cells
            n_cells = 2 * n_cells

        return {
            "ni": ni,
            "nj": nj,
            "nk": nk,
            "nijk": (ni, nj, nk),
            "n_cells": n_cells,
            "n_matrix": ni*nj*nk,
            "n_fracture": n_fracture,
            "n_active": n_active,
            "n_active_matrix": n_active_matrix,
            "n_active_fracture": n_active_fracture
        }


    def _extract_properties(self):
        dataset = self._file.get_table("SpatialProperties/Statistics")
        grid_property_list = {
            name.decode(): {
                "min": min_,
                "max": max_,
                "timesteps": set(),
                "is_internal": False,
                "is_complete": False,
                "original_name": name.decode().replace("/","%2F")
            }
            for name, min_, max_ in zip(
                dataset["Keyword"], dataset["Min"], dataset["Max"]
            )
        }

        n_active = self._sizes["n_active"]
        n_cells = self._sizes["n_cells"]
        n_matrix = self._sizes["n_matrix"]
        _dataset_type = type(self._file.get_table("General/HistoryTable"))

        def _list_grid_properties(timestep_str, set_timestep=None):
            dataset = self._file.get_table(f"SpatialProperties/{timestep_str}")
            for key in dataset.keys():
                sub_dataset = self._file.get_table(f"SpatialProperties/{timestep_str}/{key}")
                if not isinstance(sub_dataset, _dataset_type):
                    continue
                key = key.replace("%2F", "/")
                if key not in grid_property_list:
                    msg = f"{key} not listed previously!"
                    raise ValueError(msg)

                size = sub_dataset.size
                if size not in [n_cells, n_active, n_matrix]:
                    _ = grid_property_list.pop(key)
                    continue
                if "size" in grid_property_list[key]:
                    if grid_property_list[key]["size"] != size:
                        msg = f"Inconsistent grid size for {key}. "
                        msg += f"Expected {size}, found {grid_property_list[key]['size']}."
                        raise ValueError(msg)
                else:
                    grid_property_list[key]["size"] = size
                    grid_property_list[key]["matrix_or_frat_only"] = (
                        sub_dataset.size == n_matrix
                    )
                    grid_property_list[key]["is_complete"] = (
                        sub_dataset.size in [n_cells, n_matrix]
                    )

                if set_timestep is None:
                    grid_property_list[key]["timesteps"].add(
                        int(timestep_str)
                    )
                else:
                    grid_property_list[key]["timesteps"].add(
                        set_timestep
                    )
                    grid_property_list[key]["is_internal"] = True

        _list_grid_properties("000000/GRID", 0)
        for ts in self._dates.get_timesteps("grid"):
            _list_grid_properties(str(ts).zfill(6))
        for p in grid_property_list.values():
            p["timesteps"] = list(p["timesteps"])
            p["timesteps"].sort()
        return grid_property_list


# MARK: Getters and Setters

    def set_properties(self, properties):
        """Sets properties dict"""
        self._properties = properties


    def has_fracture(self):
        """Check if grid has fractures."""
        return self._sizes["n_active_fracture"] > 0


    def get_size(self, key=None):
        """Get grid size.

        Available keys:
            ni, nj, nk: total number of cells per coordinate
            nijk: tuple with (ni, nj, nk)
            n_cells: total number of cells
            n_matrix: total number of cells in matrix
            n_fracture: total number of cells in fracture
            n_active: number of active cells
            n_active_matrix: number of active cells in matrix
            n_active_fracture: number of active cells in fracture

        Parameters
        ----------
        key : str, optional
            Size key.
            If none, returns all grid sizes.
            (default: None)

        Raises
        ------
            ValueError
                If key is not found.
        """
        if key is None:
            return self._sizes
        if key not in self._sizes:
            msg = f'Key "{key}" not found. Avaliable keys: '
            msg += ", ".join(list(self._sizes.keys()))
            raise ValueError(msg)
        return self._sizes[key]


    def get_property(self, name=None):
        """Gets dict with property atributes by name.

        Atributes
        ---------
        name : str
            Property name.
            If None, returns all properties.
            (default: None)

        Returns
        -------
        dict
            Property data.

        Raises
        ------
            ValueError
                If property name is not found.
        """
        if name is None:
            return self._properties
        if name not in self._properties:
            raise ValueError(f"Property {name} not found.")
        return self._properties[name]


    def is_complete(self, name):
        """Check if property is complete.

        Parameters
        ----------
        name : str
            Property name.

        Returns
        -------
        bool
            True if property is complete.
        """
        return self._properties[name]["is_complete"]


    def is_internal(self, name):
        """Check if property is internal.

        Parameters
        ----------
        name : str
            Property name.

        Returns
        -------
        bool
            True if property is internal.
        """
        return self._properties[name]["is_internal"]

    def is_matrix_or_fracture_only(self, name):
        """Check if property is defined only in matrix or fracture cells.

        Parameters
        ----------
        name : str
            Property name.

        Returns
        -------
        bool
            True if property is defined only in matrix or fracture cells.
        """
        return self._properties[name]["matrix_or_frat_only"]


    def get_cell_indexes(self, is_complete, elements=None):
        """Returns cell indexes for the given property.

        Parameters
        ----------
        is_complete : bool
            If property is complete.
        elements : list, optional
            List of elements to return: 'MATRIX' or 'FRACTURE'.
            If None, returns all elements.

        Returns
        -------
        list
            List of cell indexes.

        Raises
        ------
        ValueError
            If property name is not found.
        """
        elements = self._validate_elements(elements)

        if is_complete:
            index = np.array(range(1, self._sizes["n_cells"]+1))
            frac_index = self._sizes["n_matrix"]
        else:
            index = self._active_index
            frac_index = self._sizes["n_active_matrix"]

        if elements == ["MATRIX"]:
            return index[:frac_index]
        if elements == ["FRACTURE"]:
            return index[frac_index:]
        return index[:]


    def _validate_elements(self, elements):
        if elements is None:
            elements = ["MATRIX"]
            if self.has_fracture():
                elements.append("FRACTURE")
            return elements

        if isinstance(elements, str):
            elements = [elements]
        for e in elements:
            if e not in ["MATRIX", "FRACTURE"]:
                msg = f'Invalid element: {e}.'
                raise ValueError(msg)
        if "FRACTURE" in elements and not self.has_fracture():
            msg = "Grid does not have fractures."
            raise ValueError(msg)
        return elements

# MARK: Index Converters
    def complete2active(self, complete_index=None):
        """Converts complete cell index to active cell index.

        Inactive cells will have index 0.

        Attributes
        ----------
        complete_index : int or [int], optional
            Complete cell index or list of indexes.
            If None, uses all cell indexes.
            (default: None)
        """
        if complete_index is None:
            return self._complete_index
        i = self._complete_index[np.array(complete_index)-1]
        if isinstance(i, int):
            return i[0]
        return i


    def active2complete(self, active_index=None):
        """Converts active cell index to complete cell index.

        Attributes
        ----------
        active_index : int or [int], optional
            Active cell index or list of indexes.
            If None, uses all active cell indexes.
            (default: None)
        """
        if active_index is None:
            return self._active_index
        i = self._active_index[np.array(active_index)-1]
        if isinstance(i, int):
            return i[0]
        return i


    def n2ijk(self, n, as_string=False):
        """Returns (i,j,k) coordinates of the n-th cell.

            Parameters
            ----------
            n : int or [int]
                Cell number, from 1 to ni*nj*nk or
                2*ni*nj*nk, if has_fracture is True.
            as_string : bool, optional
                If True, returns the coordinates as
                strings.
                (default: False)

            Raises
            ------
            ValueError
                If an incorrect cell number is provided.
            ValueError
                If shape is not defined.
        """
        ijk = _n2ijk(self._sizes["nijk"], n, self.has_fracture())
        if as_string:
            ijk = [','.join([str(c) for c in c]) for c in ijk]
        return ijk


    def ijk2n(self, ijk):
        """Returns cell number of the (i,j,k) cell.

            Parameters
            ----------
            ijk : list/tuple or [list/tuple]
                (i,j,k) coordinates or list of coordinates.
                Grids with fractures must have an additional
                element indicating if the cell is matrix
                (1) or fracture (2).
                E.g.: (i, j, k, 1) or [(i, j, k, 2), ...]

            Raises
            ------
            ValueError
                If an incorrect coordinate is provided.
            ValueError
                If shape is not defined.
        """
        return _ijk2n(self._sizes["nijk"], ijk)

    def is_neighbor(self, ijk1, ijk2):
        """Checks if cells as neighbors.

            Parameters
            ----------
            ijk1 : list/tuple or [list/tuple]
                (i,j,k) coordinates or list of coordinates.
                Grids with fractures must have an additional
                element indicating if the cell is matrix
                (1) or fracture (2).
                E.g.: (i, j, k, 1) or [(i, j, k, 2), ...]
            ijk2 : same as ijk1

            Raises
            ------
            ValueError
                If shapes are different.
        """
        return _is_neighbor(ijk1, ijk2)
