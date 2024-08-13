# sr3reader/properties.py
"""
properties.py

This module provides functionality for handling properties.

Classes:
--------
PropertyHandler
    A class to handle properties.

Usage Example:
--------------
property_handler = PropertyHandler()
description("OILRATSC")
"""

import re


class PropertyHandler:
    """
    A class to handle properties.

    Attributes
    ----------
    _properties : dict
        A dictionary to store property data.

    Methods
    -------
    set_units(units):
        Sets the unit handler for the property handler.
    extract(property_table, components_table=None):
        Extracts property information from the given table.
    replace_components(property_list):
        Returns list or dict that replaces components numbers to names.
    description(property_name):
        Returns dict with property attributes.
    dimensionality(self, property_name):
        Returns property dimensionality.
    unit(self, property_name):
        Returns property current unit.
    conversion(self, property_name):
        Returns property current unit conversion.
    set_alias(self, old, new):
        Sets an alias for an existing property.
    """


    def __init__(self):
        self._properties = {}
        self._component_list = {}
        self._units = None


    def set_units(self, units):
        """Sets the unit handler for the property handler.

        Parameters
        ----------
        units : UnitHandler
            Unit handler to be used.
        """
        self._units = units


    def extract(self, property_table, components_table=None):
        """Extracts property information from the given table.

        Parameters
        ----------
        property_table : h5py.Dataset
            Property table from the SR3 file.
            Usually "General/UnitsTable".
        components_table : h5py.Dataset
            Components table from the SR3 file.
            Usually "General/ComponentTable".
        """
        if components_table is not None:
            self._extract_components_table(components_table)
        self._extract_property_table(property_table)


    def _extract_property_table(self, dataset):
        self._properties = {}
        columns = zip(
            dataset["Keyword"],
            dataset["Name"],
            dataset["Long Name"],
            dataset["Dimensionality"],
        )
        for keyword, name, long_name, dimensionality in columns:
            if keyword != "":
                keyword = keyword.decode()
                name = name.decode()
                long_name = long_name.decode()
                dimensionality = dimensionality.decode()
                if keyword[-2:] == "$C":
                    for c in self._component_list.values():
                        new_keyword = f"{keyword[:-2]}({c})"
                        self._properties[new_keyword] = {
                            "name": name.replace("$C", f" ({c})"),
                            "long name": long_name.replace("$C", f" ({c})"),
                            "dimensionality": dimensionality,
                        }
                else:
                    self._properties[keyword] = {
                        "name": name,
                        "long name": long_name,
                        "dimensionality": dimensionality,
                    }
        _ = self._properties.pop("")

    def _extract_components_table(self, dataset, ignore_water=False):
        self._component_list = {
            (number + 1): name[0].decode()
            for (number, name) in enumerate(dataset[:])
            if not (name[0].decode() == "WATER" and ignore_water)
        }


    def replace_components(self, property_list):
        """Returns list or dict that replaces components numbers to names.

        Parameters
        ----------
        property_list : [str] or dict
            Property list or dictionary.
        """
        pattern = re.compile(r"\((\d+)\)")

        def _replace(match):
            number = int(match.group(1))
            return f'({str(self._component_list.get(number, match.group(1)))})'
        if isinstance(property_list, dict):
            return {pattern.sub(_replace, k): v
                    for k, v in property_list.items()}
        return [pattern.sub(_replace, k) for k in property_list]


    def description(self, property_name):
        """Returns dict with property attributes.

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        if property_name not in self._properties:
            msg = f"{property_name} was not found in Master Property Table."
            raise ValueError(msg)
        p = self._properties[property_name]
        return {
            "description": p["name"],
            "long description": p["long name"],
            "unit": self._units.get_current(p["dimensionality"]),
        }


    def dimensionality(self, property_name):
        """Returns property dimensionality.

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        if property_name not in self._properties:
            msg = f"{property_name} was not found in Master Property Table."
            raise ValueError(msg)
        d = self._properties[property_name]["dimensionality"]
        return d


    def unit(self, property_name):
        """Returns property current unit.

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        d = self.dimensionality(property_name)
        return self._units.get_current(d)


    def conversion(self, property_name):
        """Returns property current unit conversion.

        Parameters
        ----------
        property_name : str
            Property to be evaluated.

        Raises
        ------
        ValueError
            If property_name is not found.
        """
        d = self.dimensionality(property_name)
        return self._units.conversion(d)


    def set_alias(self, old, new, return_error=True):
        """Sets an alias for an existing property.

        Parameters
        ----------
        old : str
            Original property.
        new : str
            New property alias.
        check_error : bool, optional
            Raises error if problems are found.
            (default : True)

        Raises
        ------
        ValueError
            If old property does not exist.
        ValueError
            If new property already exists.
        """
        if old not in self._properties:
            msg = f'Property not found: {old}'
            raise ValueError(msg)
        if new in self._properties and return_error:
            msg = f'Property already exists: {new}'
            raise ValueError(msg)
        self._properties[new] = self._properties[old]
