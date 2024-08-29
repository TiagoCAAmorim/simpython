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
        self._file = sr3_file
        self._dates = dates

        if auto_read:
            self.read()

# MARK: Read Data

    def read(self):
        """Reads grid information."""
        self._active_index = self._file.get_table("SpatialProperties/000000/GRID/IPSTCS")
        self._sizes = self._extract_grid_sizes()
        self._properties = self._extract_properties()


    def _extract_grid_sizes(self):
        dataset = self._file.get_table("SpatialProperties/000000/GRID")
        ni = int(dataset["IGNTID"][0])
        nj = int(dataset["IGNTJD"][0])
        nk = int(dataset["IGNTKD"][0])
        n_cells = ni*nj*nk
        n_active = self._active_index.size
        n_fracture = 0
        n_active_fracture = 0

        if self._active_index[-1] > n_cells:
            n_active_matrix = np.where(self._active_index > n_cells)[0][0]
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
            "n_active_matrix": n_active,
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
                if size not in [n_cells, n_active]:
                    _ = grid_property_list.pop(key)
                    continue
                if "size" in grid_property_list[key]:
                    if grid_property_list[key]["size"] != size:
                        msg = f"Inconsistent grid size for {key}. "
                        msg += f"Expected {size}, found {grid_property_list[key]['size']}."
                        raise ValueError(msg)
                else:
                    grid_property_list[key]["size"] = size
                    grid_property_list[key]["is_complete"] = (
                        sub_dataset.size == n_cells
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


    def get_cell_indexes(self, property_name, elements=None):
        """Returns cell indexes for the given property.

            Parameters
            ----------
            property_name : str
                Property name.
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
        if property_name not in self._properties:
            raise ValueError(f"Property {property_name} not found.")
        elements = self._validate_elements(elements)

        if self.is_complete(property_name):
            index = np.array(range(self._sizes["n_cells"]))
            frac_index = self._sizes["n_matrix"]
        else:
            index = self._active_index
            frac_index = self._sizes["n_active_matrix"]

        if elements == ["MATRIX"]:
            return index[:frac_index]
        if elements == ["FRACTURE"]:
            return index[frac_index:-1]
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


    def n2ijk(self, n):
        """Returns (i,j,k) coordinates of the n-th cell.

            Parameters
            ----------
            n : int
                Cell number, from 0 to number of values-1.

            Raises
            ------
            ValueError
                If an incorrect cell number is provided.
            ValueError
                If shape is not defined.
        """
        if n < 0:
            msg = "Cells number must be greater than or equal to 0."
            raise ValueError(msg)

        ni, nj, nk = self._sizes["nijk"]

        if n > ni*nj*nk:
            msg = "Cells number must be smaller than number of values."
            raise ValueError(msg)

        k = int(n/(ni*nj)) + 1
        j = int( (n/ni - (k-1)*nj)) + 1
        i = n - (k-1)*ni*nj - (j-1)*ni + 1
        return i, j, k


    def ijk2n(self, i, j=None, k=None):
        """Returns cell number of the (i,j,k) cell.

            Parameters
            ----------
            i : int or list/tuple
                i direction coordinate or list/tuple
                with (i,j,k) coordinates.
            j : int, optional
                j direction coordinate. Assumes i contains
                all coordinates if None is provided.
                (default: None)
            k : int, optional
                k direction coordinate. Assumes i contains
                all coordinates if None is provided.
                (default: None)

            Raises
            ------
            ValueError
                If an incorrect coordinate is provided.
            ValueError
                If shape is not defined.
        """
        if (j is None) and (k is None):
            if len(i) != 3:
                msg = f"Expected 3 coordinates, found {len(i)}."
                raise ValueError(msg)
            i, j, k = i
        if (j is not None) and (k is None):
            msg = "Coordinates must be provided as a tuple/list or separate arguments."
            raise ValueError(msg)
        if (j is None) and (k is not None):
            msg = "Coordinates must be provided as a tuple/list or separate arguments."
            raise ValueError(msg)

        if (i < 1) or (j < 1) or (k < 1):
            msg = "Coordinates number must be greater than or equal to 1."
            raise ValueError(msg)

        ni, nj, nk = self._sizes["nijk"]

        if (i > ni) or (j > nj) or (k > nk):
            msg = "Coordinates number must be smaller than or equal to grid sizes."
            raise ValueError(msg)

        return (k - 1)*ni*nj + (j - 1)*ni + i - 1
