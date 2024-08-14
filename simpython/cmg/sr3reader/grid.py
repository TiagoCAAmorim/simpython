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
grid_handler = GridHandler()
"""

import numpy as np


class GridHandler:
    """
    A class to handle grids.

    Attributes
    ----------

    Methods
    -------
    """

    def __init__(self, sr3_file, dates):
        self._properties = []
        self._size = ()
        self.file = sr3_file
        self.dates = dates
        self.extract()


    def extract(self):
        """Extracts grid information."""
        self._size = self._extract_grid_sizes()
        self._properties = self._extract_properties()


    def has_fracture(self):
        """Check if grid has fractures."""
        return self._size["n_active_fracture"] > 0


    def get_size(self, key=None):
        """Get grid size.

        Available keys:
            ni, nj, nk, nijk, n_cells,
            n_active, n_active_matrix, n_active_fracture

        Parameters
        ----------
        key : str, optional
            Size key.
            If none, returns all sizes.
            (default: None)

        Raises
        ------
            ValueError
                If key is not found.
        """
        if key is None:
            return self._size
        if key not in self._size:
            raise ValueError(f"Key {key} not found.")
        return self._size[key]


    def _extract_grid_sizes(self):
        dataset = self.file.get_table("SpatialProperties/000000/GRID")
        ni = dataset["IGNTID"][0]
        nj = dataset["IGNTJD"][0]
        nk = dataset["IGNTKD"][0]
        n_cells = ni * nj * nk
        n_active = dataset["IPSTCS"].size
        n_active_matrix = n_active
        n_active_fracture = 0
        if dataset["IPSTCS"][-1] > ni * nj * nk:
            n_active_matrix = np.where(
                self.file.get_table("SpatialProperties/000000/GRID/IPSTCS") > ni * nj * nk
            )[0][0]
            n_active_fracture = n_active - n_active_matrix
            n_cells = 2 * n_cells
        return {
            "ni": int(ni),
            "nj": int(nj),
            "nk": int(nk),
            "nijk": (ni, nj, nk),
            "n_active": int(n_active),
            "n_active_matrix": int(n_active_matrix),
            "n_active_fracture": int(n_active_fracture),
            "n_cells": int(n_cells)
        }


    def get_property(self, name=None):
        """Get grid property by name.

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


    def _extract_properties(self):
        dataset = self.file.get_table("SpatialProperties/Statistics")
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

        n_active = self._size["n_active"]
        n_cells = self._size["n_cells"]

        _dataset_type = type(self.file.get_table("General/HistoryTable"))
        def _list_grid_properties(timestep, set_timestep=None):
            dataset = self.file.get_table(f"SpatialProperties/{timestep}")
            for key in dataset.keys():
                sub_dataset = self.file.get_table(f"SpatialProperties/{timestep}/{key}")
                if not isinstance(sub_dataset, _dataset_type):
                    continue
                key = key.replace("%2F", "/")
                if key not in grid_property_list:
                    raise ValueError(f"{key} not listed previously!")
                size = sub_dataset.size
                if size not in [n_cells, n_active]:
                    _ = grid_property_list.pop(key)
                    continue
                if "size" in grid_property_list[key]:
                    if grid_property_list[key]["size"] != size:
                        msg = f"Inconsistent grid size for {key}."
                        raise ValueError(msg)
                else:
                    grid_property_list[key]["size"] = size
                    grid_property_list[key]["is_complete"] = (
                        sub_dataset.size == n_cells
                    )
                if set_timestep is None:
                    grid_property_list[key]["timesteps"].add(
                        int(timestep)
                    )
                else:
                    grid_property_list[key]["timesteps"].add(
                        set_timestep
                    )
                    grid_property_list[key]["is_internal"] = True

        _list_grid_properties("000000/GRID", 0)
        for ts in self.dates.get_timesteps("grid"):
            _list_grid_properties(str(ts).zfill(6))
        for p in grid_property_list.values():
            p["timesteps"] = list(p["timesteps"])
            p["timesteps"].sort()
        # self._grid_properties_adjustments(grid_property_list)
        return grid_property_list
