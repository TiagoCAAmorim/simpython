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


    def get_bulk_volumes(self, cells=None, active_only=False):
        """Calculate bulk volume for grid cells from vertex coordinates.

        Coordinates are read from ``self.coordinates.get`` and processed in a
        fully vectorized way for all selected cells.

        The implementation follows the tetrakis-hexahedron (TH) formula in
        Grandy (1997), UCRL-ID-128886, Eq. (12):

            12 v = [a1; b1; c1] + [a2; b2; c2] + [a3; b3; c3]

        where each bracket is a scalar triple product. The report uses a node
        ordering where node 0 has neighbors (1, 2, 4). ``coordinates.py`` uses
        a different convention, so coordinates are remapped before applying the
        equation.

        Parameters
        ----------
        cells : int, list of int, np.ndarray or None, optional
            Complete cell index(es). If provided, ``active_only`` is ignored.
        active_only : bool, optional
            If True and ``cells`` is None, returns volumes only for active cells.
            If False and ``cells`` is None, returns volumes for all cells.
            (default: False)

        Returns
        -------
        np.ndarray
            Bulk volumes for the selected cells.
        """
        if cells is None and active_only:
            cells = self.get_cell_indexes(is_complete=False)

        nodes = self.coordinates.get(cells=cells, face=None)
        if nodes.ndim == 2:
            nodes = nodes[np.newaxis, ...]

        # Remap from coordinates.py numbering to Grandy's Eq. (12) numbering.
        # report_idx -> current_idx: [0, 1, 2, 3, 4, 5, 6, 7] -> [0, 1, 3, 2, 4, 5, 7, 6]
        report_nodes = nodes[:, [0, 1, 3, 2, 4, 5, 7, 6], :]
        x0, x1, x2, x3, x4, x5, x6, x7 = [report_nodes[:, i, :] for i in range(8)]

        term1 = np.einsum(
            "ij,ij->i",
            (x7 - x1) + (x6 - x0),
            np.cross((x7 - x2), (x3 - x0)),
        )
        term2 = np.einsum(
            "ij,ij->i",
            (x6 - x0),
            np.cross((x7 - x2) + (x5 - x0), (x7 - x4)),
        )
        term3 = np.einsum(
            "ij,ij->i",
            (x7 - x1),
            np.cross((x5 - x0), (x7 - x4) + (x3 - x0)),
        )

        return np.abs((term1 + term2 + term3) / 12.0)


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
        if not hasattr(active_index, '__iter__') or isinstance(active_index, (str, bytes)):
            return i.item() if hasattr(i, 'item') else i
        return i


    def n2ijk(self, n, as_active=False, as_string=False):
        """Returns (i,j,k) coordinates of the n-th cell.

            Parameters
            ----------
            n : int or [int]
                Cell number, from 1 to ni*nj*nk or
                2*ni*nj*nk, if has_fracture is True.
            as_active : bool, optional
                If True, assumes the cell number refers
                to the active cells only.
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
        if as_active:
            n = self.active2complete(n)
        ijk = _n2ijk(self._sizes["nijk"], n, self.has_fracture())
        if as_string:
            ijk = [','.join([str(c) for c in c]) for c in ijk]
        return ijk


    def ijk2n(self, ijk, as_active=False):
        """Returns cell number of the (i,j,k) cell.

            Parameters
            ----------
            ijk : list/tuple or [list/tuple]
                (i,j,k) coordinates or list of coordinates.
                Grids with fractures must have an additional
                element indicating if the cell is matrix
                (1) or fracture (2).
                E.g.: (i, j, k, 1) or [(i, j, k, 2), ...]
            as_active : bool, optional
                If True, returns the active cell number.
                (default: False)

            Raises
            ------
            ValueError
                If an incorrect coordinate is provided.
            ValueError
                If shape is not defined.
        """
        if as_active:
            return self.complete2active(self.ijk2n(ijk))
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
